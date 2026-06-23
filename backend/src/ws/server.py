"""WebSocket 服务器模块 - 提供 WebSocket 端点实现。"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.auth.service import AuthService
from src.db.database import get_db
from src.monitoring.logger import Logger
from src.ws.connection_manager import ConnectionManager
from src.ws.message_handler import MessageHandler

router = APIRouter()
manager = ConnectionManager()
logger = Logger()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    session_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """WebSocket 端点。

    通过 query 参数 token 进行认证，session_id 可选指定关联会话。
    连接建立后进入消息循环，接收并处理客户端发送的 JSON 消息。

    Args:
        websocket: WebSocket 连接对象。
        token: 用户访问令牌（通过 query 参数传递）。
        session_id: 关联会话 ID（可选，通过 query 参数传递）。
        db: 数据库会话（通过依赖注入获取）。
    """
    # 验证 token
    auth_service = AuthService(db)
    try:
        user = auth_service.get_current_user(token)
    except Exception:
        await websocket.close(code=4001, reason="认证失败")
        return

    # 生成 client_id
    client_id = str(uuid.uuid4())
    logger.info(
        f"WebSocket 连接: client_id={client_id}, user={user.username}, session_id={session_id}"
    )

    try:
        await manager.connect(websocket, client_id, session_id)
        # 创建消息处理器
        handler = MessageHandler(db, manager)

        # 消息循环
        while True:
            data = await websocket.receive_json()
            await handler.handle(data, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"WebSocket 断开: client_id={client_id}")

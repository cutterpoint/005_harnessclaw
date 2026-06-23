"""WebSocket 消息处理器模块 - 处理客户端发送的各类消息。"""
from sqlalchemy.orm import Session

from src.agent.schemas import AgentRunRequest
from src.auth.service import AuthService
from src.monitoring.logger import Logger
from src.ws.connection_manager import ConnectionManager


class MessageHandler:
    """WebSocket 消息处理器，分发并处理不同类型的消息。"""

    def __init__(self, db: Session, connection_manager: ConnectionManager):
        """初始化消息处理器。

        Args:
            db: SQLAlchemy 数据库会话。
            connection_manager: WebSocket 连接管理器实例。
        """
        self.db = db
        self.connection_manager = connection_manager
        self.logger = Logger()

    async def handle(self, message: dict, client_id: str) -> None:
        """处理接收到的消息。

        根据消息 type 字段分发到对应的处理方法。

        Args:
            message: 接收到的 JSON 消息字典。
            client_id: 发送消息的客户端唯一标识。
        """
        msg_type = message.get("type")
        self.logger.info(f"收到消息: client_id={client_id}, type={msg_type}")

        if msg_type == "ping":
            await self._handle_ping(client_id)
        elif msg_type == "chat":
            await self._handle_chat(message, client_id)
        elif msg_type == "disconnect":
            await self._handle_disconnect(client_id)
        else:
            await self.connection_manager.send_message(client_id, {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            })

    async def _handle_ping(self, client_id: str) -> None:
        """处理心跳。

        Args:
            client_id: 客户端唯一标识。
        """
        await self.connection_manager.send_message(client_id, {"type": "pong"})

    async def _handle_chat(self, message: dict, client_id: str) -> None:
        """处理对话消息。

        验证用户身份后，发送处理状态并调用 Agent 引擎执行对话。

        Args:
            message: 对话消息字典，包含 content、token、session_id 等字段。
            client_id: 客户端唯一标识。
        """
        # 获取用户消息
        user_message = message.get("content", "")
        session_id = message.get("session_id")
        token = message.get("token", "")
        user_id = message.get("user_id")

        # 验证用户
        auth_service = AuthService(self.db)
        try:
            user = auth_service.get_current_user(token)
        except Exception:
            user = None

        if not user:
            await self.connection_manager.send_message(client_id, {
                "type": "error",
                "message": "Authentication failed"
            })
            return

        # 发送"正在处理"状态
        await self.connection_manager.send_message(client_id, {
            "type": "status",
            "status": "processing"
        })

        # 创建 AgentEngine 并执行（需要初始化所有依赖）
        # 这里简化处理，实际需要完整初始化
        try:
            # TODO: 完整初始化 AgentEngine
            # agent_engine = create_agent_engine(self.db)
            # result = await agent_engine.run(AgentRunRequest(...))

            # 模拟响应
            await self.connection_manager.send_message(client_id, {
                "type": "response",
                "content": f"Echo: {user_message}",
                "session_id": session_id
            })
        except Exception as e:
            await self.connection_manager.send_message(client_id, {
                "type": "error",
                "message": str(e)
            })

    async def _handle_disconnect(self, client_id: str) -> None:
        """处理断开连接。

        Args:
            client_id: 客户端唯一标识。
        """
        self.connection_manager.disconnect(client_id)

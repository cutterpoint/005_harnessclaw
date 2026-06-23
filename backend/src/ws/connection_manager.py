"""WebSocket 连接管理器模块 - 管理 WebSocket 连接的生命周期与消息分发。"""
from typing import Dict, List, Optional

from fastapi import WebSocket

from src.monitoring.logger import Logger


class ConnectionManager:
    """WebSocket 连接管理器，维护客户端连接和会话关联。"""

    def __init__(self):
        """初始化连接管理器。"""
        self.active_connections: Dict[str, WebSocket] = {}  # client_id -> WebSocket
        self.session_connections: Dict[int, List[str]] = {}  # session_id -> [client_ids]
        self.logger = Logger()

    async def connect(self, websocket: WebSocket, client_id: str, session_id: int) -> None:
        """接受 WebSocket 连接并注册。

        Args:
            websocket: WebSocket 连接对象。
            client_id: 客户端唯一标识。
            session_id: 关联的会话 ID。
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(client_id)
        self.logger.info(
            f"WebSocket 连接建立: client_id={client_id}, session_id={session_id}"
        )

    def disconnect(self, client_id: str) -> None:
        """断开连接并清理。

        Args:
            client_id: 客户端唯一标识。
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        for session_id, client_ids in self.session_connections.items():
            if client_id in client_ids:
                client_ids.remove(client_id)
                break
        self.logger.info(f"WebSocket 连接断开: client_id={client_id}")

    async def send_message(self, client_id: str, message: dict) -> None:
        """发送消息给指定客户端。

        Args:
            client_id: 客户端唯一标识。
            message: 待发送的 JSON 消息字典。
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict, session_id: Optional[int] = None) -> None:
        """广播消息。

        Args:
            message: 待广播的 JSON 消息字典。
            session_id: 指定会话 ID 时仅广播给该会话的客户端，为 None 时广播给所有客户端。
        """
        if session_id:
            client_ids = self.session_connections.get(session_id, [])
            for client_id in client_ids:
                await self.send_message(client_id, message)
        else:
            for client_id in list(self.active_connections.keys()):
                await self.send_message(client_id, message)

    def get_connection_count(self) -> int:
        """获取当前连接数。

        Returns:
            当前活跃连接数量。
        """
        return len(self.active_connections)

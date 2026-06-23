"""WebSocket 模块单元测试。"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.schemas import UserCreate
from src.auth.service import AuthService
from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata
from src.db.database import Base, get_db
from src.ws.connection_manager import ConnectionManager
from src.ws.message_handler import MessageHandler
from src.ws.server import manager, router


class MockWebSocket:
    """模拟 WebSocket 用于测试。"""

    def __init__(self):
        self.accepted = False
        self.sent_messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None

    async def accept(self):
        """接受连接。"""
        self.accepted = True

    async def send_json(self, message):
        """发送 JSON 消息。"""
        self.sent_messages.append(message)

    async def close(self, code=1000, reason=None):
        """关闭连接。"""
        self.closed = True
        self.close_code = code
        self.close_reason = reason


@pytest.fixture
def db_session():
    """创建内存 SQLite 数据库会话，每个测试函数独立隔离。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ----------------------------- ConnectionManager 测试 -----------------------------


class TestConnectionManager:
    """连接管理器相关测试。"""

    async def test_connection_manager_connect_disconnect(self):
        """测试连接和断开。"""
        cm = ConnectionManager()
        ws = MockWebSocket()

        # 连接
        await cm.connect(ws, "client1", session_id=1)

        assert ws.accepted is True
        assert "client1" in cm.active_connections
        assert cm.get_connection_count() == 1
        assert "client1" in cm.session_connections[1]

        # 断开
        cm.disconnect("client1")

        assert "client1" not in cm.active_connections
        assert cm.get_connection_count() == 0
        assert "client1" not in cm.session_connections.get(1, [])

    async def test_connection_manager_send_message(self):
        """测试发送消息。"""
        cm = ConnectionManager()
        ws = MockWebSocket()

        await cm.connect(ws, "client1", session_id=1)
        await cm.send_message("client1", {"type": "test", "data": "hello"})

        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0] == {"type": "test", "data": "hello"}

        # 测试发送给不存在的客户端（不应抛出异常）
        await cm.send_message("nonexistent", {"type": "test"})

        cm.disconnect("client1")

    async def test_connection_manager_broadcast(self):
        """测试广播消息。"""
        cm = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await cm.connect(ws1, "client1", session_id=1)
        await cm.connect(ws2, "client2", session_id=2)

        # 全局广播
        await cm.broadcast({"type": "broadcast"})

        assert len(ws1.sent_messages) == 1
        assert ws1.sent_messages[0] == {"type": "broadcast"}
        assert len(ws2.sent_messages) == 1
        assert ws2.sent_messages[0] == {"type": "broadcast"}

        cm.disconnect("client1")
        cm.disconnect("client2")

    async def test_connection_manager_session_broadcast(self):
        """测试按会话广播消息。"""
        cm = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        await cm.connect(ws1, "client1", session_id=1)
        await cm.connect(ws2, "client2", session_id=1)
        await cm.connect(ws3, "client3", session_id=2)

        # 按会话广播
        await cm.broadcast({"type": "session_msg"}, session_id=1)

        # session_id=1 的客户端应收到消息
        assert len(ws1.sent_messages) == 1
        assert ws1.sent_messages[0] == {"type": "session_msg"}
        assert len(ws2.sent_messages) == 1
        assert ws2.sent_messages[0] == {"type": "session_msg"}

        # session_id=2 的客户端不应收到消息
        assert len(ws3.sent_messages) == 0

        cm.disconnect("client1")
        cm.disconnect("client2")
        cm.disconnect("client3")


# ----------------------------- MessageHandler 测试 -----------------------------


class TestMessageHandler:
    """消息处理器相关测试。"""

    async def test_message_handler_ping(self, db_session):
        """测试处理心跳。"""
        cm = ConnectionManager()
        ws = MockWebSocket()
        await cm.connect(ws, "client1", session_id=1)

        handler = MessageHandler(db_session, cm)
        await handler.handle({"type": "ping"}, "client1")

        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0] == {"type": "pong"}

        cm.disconnect("client1")

    async def test_message_handler_unknown_type(self, db_session):
        """测试未知消息类型。"""
        cm = ConnectionManager()
        ws = MockWebSocket()
        await cm.connect(ws, "client1", session_id=1)

        handler = MessageHandler(db_session, cm)
        await handler.handle({"type": "unknown_type"}, "client1")

        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0]["type"] == "error"
        assert "Unknown message type" in ws.sent_messages[0]["message"]

        cm.disconnect("client1")

    async def test_message_handler_chat_auth_failed(self, db_session):
        """测试认证失败。"""
        cm = ConnectionManager()
        ws = MockWebSocket()
        await cm.connect(ws, "client1", session_id=1)

        handler = MessageHandler(db_session, cm)
        await handler.handle(
            {
                "type": "chat",
                "content": "hello",
                "token": "invalid_token",
                "session_id": 1,
            },
            "client1",
        )

        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0]["type"] == "error"
        assert ws.sent_messages[0]["message"] == "Authentication failed"

        cm.disconnect("client1")


# ----------------------------- WebSocket 端点测试 -----------------------------


class TestWebSocketEndpoint:
    """WebSocket 端点相关测试。"""

    def test_websocket_endpoint(self):
        """测试 WebSocket 端点。"""
        # 创建独立的内存数据库（使用 StaticPool 共享连接，确保跨会话数据可见）
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )

        # 使用临时会话创建用户并获取 token
        setup_session = TestingSessionLocal()
        auth_service = AuthService(setup_session)
        auth_service.register(
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="SecurePassword123",
            )
        )
        token = auth_service.login(
            username="testuser",
            password="SecurePassword123",
        ).access_token
        setup_session.close()

        # 创建 FastAPI 应用
        app = FastAPI()
        app.include_router(router)

        # 覆盖数据库依赖 - 每次请求创建新会话
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        # 清理全局管理器
        manager.active_connections.clear()
        manager.session_connections.clear()

        try:
            client = TestClient(app)
            with client.websocket_connect(
                f"/ws?token={token}&session_id=1"
            ) as ws:
                # 测试心跳
                ws.send_json({"type": "ping"})
                data = ws.receive_json()
                assert data == {"type": "pong"}

                # 测试未知消息类型
                ws.send_json({"type": "unknown"})
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "Unknown message type" in data["message"]
        finally:
            app.dependency_overrides.clear()
            manager.active_connections.clear()
            manager.session_connections.clear()
            Base.metadata.drop_all(bind=engine)

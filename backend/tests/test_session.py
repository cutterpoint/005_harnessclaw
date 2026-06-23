"""会话管理模块单元测试。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata
from src.db.database import Base
from src.db.models import Session as DBSession
from src.session.schemas import MessageCreate, SessionUpdate
from src.session.service import SessionManager


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


@pytest.fixture
def session_manager(db_session):
    """创建会话管理器实例。"""
    return SessionManager(db_session)


class TestSession:
    """会话相关测试。"""

    def test_create_session(self, session_manager):
        """测试创建会话。"""
        response = session_manager.create_session(user_id=1, title="测试会话")

        assert response.id is not None
        assert response.user_id == 1
        assert response.title == "测试会话"
        assert response.status == "active"
        assert response.session_key is not None
        assert len(response.session_key) > 0
        assert response.created_at is not None

    def test_get_session(self, session_manager):
        """测试获取会话。"""
        created = session_manager.create_session(user_id=1, title="测试会话")

        fetched = session_manager.get_session(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.session_key == created.session_key
        assert fetched.title == "测试会话"
        assert fetched.status == "active"

    def test_get_session_by_key(self, session_manager):
        """测试按 key 获取会话。"""
        created = session_manager.create_session(user_id=1, title="测试会话")

        fetched = session_manager.get_session_by_key(created.session_key)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.session_key == created.session_key

    def test_get_user_sessions(self, session_manager):
        """测试获取用户会话列表（含分页）。"""
        # 用户 1 创建 5 个会话
        for i in range(5):
            session_manager.create_session(user_id=1, title=f"会话{i}")
        # 用户 2 创建 2 个会话
        for i in range(2):
            session_manager.create_session(user_id=2, title=f"用户2会话{i}")

        # 获取用户 1 全部会话
        result = session_manager.get_user_sessions(user_id=1, page=1, limit=20)
        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["limit"] == 20

        # 分页：第 1 页 2 条
        result = session_manager.get_user_sessions(user_id=1, page=1, limit=2)
        assert result["total"] == 5
        assert len(result["items"]) == 2

        # 分页：第 3 页 2 条（只剩 1 条）
        result = session_manager.get_user_sessions(user_id=1, page=3, limit=2)
        assert result["total"] == 5
        assert len(result["items"]) == 1

        # 用户隔离：用户 2 只有 2 个会话
        result = session_manager.get_user_sessions(user_id=2)
        assert result["total"] == 2

    def test_update_session(self, session_manager):
        """测试更新会话标题和状态。"""
        created = session_manager.create_session(user_id=1, title="原标题")

        # 更新标题
        updated = session_manager.update_session(
            created.id, SessionUpdate(title="新标题")
        )
        assert updated.title == "新标题"
        assert updated.status == "active"

        # 更新状态为 archived
        updated = session_manager.update_session(
            created.id, SessionUpdate(status="archived")
        )
        assert updated.status == "archived"
        assert updated.title == "新标题"

    def test_delete_session(self, session_manager):
        """测试删除会话（验证软删除）。"""
        created = session_manager.create_session(user_id=1, title="待删除")

        # 删除会话
        result = session_manager.delete_session(created.id)
        assert result is True

        # 验证软删除：get_session 返回 None
        fetched = session_manager.get_session(created.id)
        assert fetched is None

        # 验证数据库中记录仍存在且 status 为 deleted
        raw = (
            session_manager.db.query(DBSession)
            .filter(DBSession.id == created.id)
            .first()
        )
        assert raw is not None
        assert raw.status == "deleted"

    def test_add_message(self, session_manager):
        """测试添加消息。"""
        session = session_manager.create_session(user_id=1, title="消息测试")

        msg = session_manager.add_message(
            session.id,
            MessageCreate(role="user", content="你好"),
        )

        assert msg.id is not None
        assert msg.session_id == session.id
        assert msg.role == "user"
        assert msg.content == "你好"
        assert msg.tool_call is None
        assert msg.tool_call_id is None
        assert msg.created_at is not None

    def test_get_messages(self, session_manager):
        """测试获取消息列表（含分页）。"""
        session = session_manager.create_session(user_id=1, title="消息列表测试")

        # 添加 5 条消息
        for i in range(5):
            session_manager.add_message(
                session.id,
                MessageCreate(role="user", content=f"消息{i}"),
            )

        # 获取全部
        result = session_manager.get_messages(session.id, page=1, limit=50)
        assert result["total"] == 5
        assert len(result["items"]) == 5
        # 验证按时间正序排列
        assert result["items"][0].content == "消息0"
        assert result["items"][4].content == "消息4"

        # 分页：第 1 页 2 条
        result = session_manager.get_messages(session.id, page=1, limit=2)
        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["items"][0].content == "消息0"
        assert result["items"][1].content == "消息1"

        # 分页：第 3 页 2 条（只剩 1 条）
        result = session_manager.get_messages(session.id, page=3, limit=2)
        assert result["total"] == 5
        assert len(result["items"]) == 1
        assert result["items"][0].content == "消息4"

    def test_get_recent_messages(self, session_manager):
        """测试获取最近消息。"""
        session = session_manager.create_session(user_id=1, title="最近消息测试")

        # 添加 5 条消息
        for i in range(5):
            session_manager.add_message(
                session.id,
                MessageCreate(role="user", content=f"消息{i}"),
            )

        # 获取最近 3 条
        recent = session_manager.get_recent_messages(session.id, limit=3)

        assert len(recent) == 3
        # 应返回最后 3 条（消息2、消息3、消息4），按时间正序排列
        assert recent[0].content == "消息2"
        assert recent[1].content == "消息3"
        assert recent[2].content == "消息4"

    def test_get_deleted_session(self, session_manager):
        """测试获取已删除会话返回 None。"""
        created = session_manager.create_session(user_id=1, title="将删除")
        session_manager.delete_session(created.id)

        # 按 ID 获取应返回 None
        assert session_manager.get_session(created.id) is None
        # 按 key 获取应返回 None
        assert session_manager.get_session_by_key(created.session_key) is None
        # 已删除会话不应出现在用户会话列表中
        result = session_manager.get_user_sessions(user_id=1)
        assert result["total"] == 0

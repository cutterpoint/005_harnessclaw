"""会话管理服务模块 - 提供会话的创建、查询、更新、删除及消息管理功能。"""
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models import Session as DBSession, Message
from src.monitoring.logger import Logger
from src.session.schemas import (
    MessageCreate,
    MessageResponse,
    SessionResponse,
    SessionUpdate,
)


class SessionManager:
    """会话管理器，封装会话与消息相关业务逻辑。"""

    def __init__(self, db: Session):
        """初始化会话管理器。

        Args:
            db: SQLAlchemy 数据库会话。
        """
        self.db = db
        # 使用当前数据库会话初始化日志记录器，便于记录会话相关日志
        self.logger = Logger(db=db)

    def create_session(
        self, user_id: int, title: Optional[str] = None
    ) -> SessionResponse:
        """创建新会话，生成唯一 session_key。

        Args:
            user_id: 用户 ID。
            title: 会话标题，可选。

        Returns:
            创建的会话信息。
        """
        session_key = str(uuid.uuid4())
        session = DBSession(
            user_id=user_id,
            session_key=session_key,
            title=title,
            status="active",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        self.logger.log_system(
            log_type="event",
            module="session",
            action="create_session",
            details={
                "session_id": session.id,
                "session_key": session_key,
                "title": title,
            },
            user_id=user_id,
            session_id=session.id,
        )

        return SessionResponse.model_validate(session)

    def get_session(self, session_id: int) -> Optional[SessionResponse]:
        """获取会话（默认排除已删除的会话）。

        Args:
            session_id: 会话 ID。

        Returns:
            会话信息，若不存在或已删除则返回 None。
        """
        session = (
            self.db.query(DBSession)
            .filter(DBSession.id == session_id)
            .filter(DBSession.status != "deleted")
            .first()
        )
        if session is None:
            return None
        return SessionResponse.model_validate(session)

    def get_session_by_key(self, session_key: str) -> Optional[SessionResponse]:
        """按 session_key 获取会话（默认排除已删除的会话）。

        Args:
            session_key: 会话唯一键。

        Returns:
            会话信息，若不存在或已删除则返回 None。
        """
        session = (
            self.db.query(DBSession)
            .filter(DBSession.session_key == session_key)
            .filter(DBSession.status != "deleted")
            .first()
        )
        if session is None:
            return None
        return SessionResponse.model_validate(session)

    def get_user_sessions(
        self, user_id: int, page: int = 1, limit: int = 20
    ) -> Dict:
        """获取用户会话列表（分页，默认排除已删除的会话）。

        Args:
            user_id: 用户 ID。
            page: 页码，从 1 开始。
            limit: 每页数量。

        Returns:
            包含 items、total、page、limit 的分页字典。
        """
        query = (
            self.db.query(DBSession)
            .filter(DBSession.user_id == user_id)
            .filter(DBSession.status != "deleted")
        )
        total = query.count()
        items = (
            query.order_by(DBSession.created_at.desc(), DBSession.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {
            "items": [SessionResponse.model_validate(item) for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def update_session(
        self, session_id: int, update: SessionUpdate
    ) -> SessionResponse:
        """更新会话信息（标题、状态）。

        Args:
            session_id: 会话 ID。
            update: 更新数据。

        Returns:
            更新后的会话信息。

        Raises:
            ValueError: 会话不存在或已删除。
        """
        session = (
            self.db.query(DBSession)
            .filter(DBSession.id == session_id)
            .filter(DBSession.status != "deleted")
            .first()
        )
        if session is None:
            raise ValueError("会话不存在或已删除")

        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        self.db.commit()
        self.db.refresh(session)

        return SessionResponse.model_validate(session)

    def delete_session(self, session_id: int) -> bool:
        """软删除会话（status 改为 deleted）。

        Args:
            session_id: 会话 ID。

        Returns:
            删除成功返回 True，会话不存在或已删除返回 False。
        """
        session = (
            self.db.query(DBSession)
            .filter(DBSession.id == session_id)
            .filter(DBSession.status != "deleted")
            .first()
        )
        if session is None:
            return False

        session.status = "deleted"
        self.db.commit()
        self.db.refresh(session)

        self.logger.log_system(
            log_type="event",
            module="session",
            action="delete_session",
            details={"session_id": session_id},
            user_id=session.user_id,
            session_id=session.id,
        )

        return True

    def add_message(
        self, session_id: int, message: MessageCreate
    ) -> MessageResponse:
        """向会话添加消息。

        Args:
            session_id: 会话 ID。
            message: 消息数据。

        Returns:
            创建的消息信息。

        Raises:
            ValueError: 会话不存在或已删除。
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError("会话不存在或已删除")

        msg = Message(
            session_id=session_id,
            role=message.role,
            content=message.content,
            tool_call=message.tool_call,
            tool_call_id=message.tool_call_id,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        return MessageResponse.model_validate(msg)

    def get_messages(
        self, session_id: int, page: int = 1, limit: int = 50
    ) -> Dict:
        """获取会话消息列表（分页，按时间正序）。

        Args:
            session_id: 会话 ID。
            page: 页码，从 1 开始。
            limit: 每页数量。

        Returns:
            包含 items、total、page、limit 的分页字典。
        """
        query = self.db.query(Message).filter(Message.session_id == session_id)
        total = query.count()
        items = (
            query.order_by(Message.created_at.asc(), Message.id.asc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {
            "items": [MessageResponse.model_validate(item) for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def get_recent_messages(
        self, session_id: int, limit: int = 10
    ) -> List[MessageResponse]:
        """获取会话最近 N 条消息（按时间正序返回）。

        先按时间倒序取最近 N 条，再反转为正序，便于按时间顺序阅读。

        Args:
            session_id: 会话 ID。
            limit: 返回的消息数量。

        Returns:
            最近的消息列表（时间正序）。
        """
        messages = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .all()
        )
        # 反转为正序，便于按时间顺序阅读
        messages.reverse()
        return [MessageResponse.model_validate(msg) for msg in messages]

"""短期记忆模块 - 基于 SQLite/SQLAlchemy 存储对话消息。"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models import Message
from src.monitoring.logger import Logger

logger = Logger()


class ShortTermMemory:
    """短期记忆，直接操作 messages 表。"""

    def __init__(self, db: Session) -> None:
        """初始化短期记忆。

        Args:
            db: SQLAlchemy 数据库会话。
        """
        self.db = db

    def add(
        self,
        session_id: int,
        role: str,
        content: str,
        tool_call: Optional[str] = None,
    ) -> None:
        """添加消息到短期记忆。

        Args:
            session_id: 会话 ID。
            role: 消息角色 (system/user/assistant/tool)。
            content: 消息内容。
            tool_call: 工具调用信息 (JSON 字符串)，可选。
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            tool_call=tool_call,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        logger.info(
            f"短期记忆已添加: session_id={session_id} role={role} "
            f"message_id={message.id}"
        )

    def get_recent(self, session_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取会话最近 N 条消息（按时间正序返回）。

        Args:
            session_id: 会话 ID。
            limit: 返回消息数量上限。

        Returns:
            消息字典列表，时间从旧到新。
        """
        messages = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .all()
        )
        # 反转为时间正序（旧 -> 新）
        messages.reverse()
        return [self._message_to_dict(m) for m in messages]

    def get_all(self, session_id: int) -> List[Dict[str, Any]]:
        """获取会话所有消息（按时间正序）。

        Args:
            session_id: 会话 ID。

        Returns:
            消息字典列表，时间从旧到新。
        """
        messages = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .all()
        )
        return [self._message_to_dict(m) for m in messages]

    def clear(self, session_id: int) -> None:
        """清除指定会话的所有消息。

        Args:
            session_id: 会话 ID。
        """
        deleted = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .delete(synchronize_session="fetch")
        )
        self.db.commit()
        logger.info(f"短期记忆已清除: session_id={session_id} count={deleted}")

    def search(
        self,
        session_id: int,
        keyword: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """关键词搜索会话消息。

        Args:
            session_id: 会话 ID。
            keyword: 搜索关键词。
            limit: 返回消息数量上限。

        Returns:
            匹配的消息字典列表，时间从新到旧。
        """
        messages = (
            self.db.query(Message)
            .filter(
                Message.session_id == session_id,
                Message.content.like(f"%{keyword}%"),
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .all()
        )
        return [self._message_to_dict(m) for m in messages]

    @staticmethod
    def _message_to_dict(msg: Message) -> Dict[str, Any]:
        """将 Message ORM 对象转换为字典。"""
        return {
            "id": msg.id,
            "session_id": msg.session_id,
            "role": msg.role,
            "content": msg.content,
            "tool_call": msg.tool_call,
            "tool_call_id": msg.tool_call_id,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }

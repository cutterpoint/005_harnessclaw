"""记忆系统管理器 - 整合短期记忆与长期记忆。"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.memory.long_term import LongTermMemory
from src.memory.schemas import MemoryItem
from src.memory.short_term import ShortTermMemory
from src.monitoring.logger import Logger
from src.vector.db import VectorDB

logger = Logger()


class MemorySystem:
    """记忆系统，统一管理短期记忆(SQLite)和长期记忆(向量库)。"""

    def __init__(
        self,
        db: Session,
        vector_db: Optional[VectorDB] = None,
    ) -> None:
        """初始化记忆系统。

        Args:
            db: SQLAlchemy 数据库会话，用于短期记忆。
            vector_db: 向量数据库实例，用于长期记忆。未提供时自动创建。
        """
        self.short_term = ShortTermMemory(db)
        self.long_term = LongTermMemory(vector_db)
        logger.info("记忆系统已初始化 (短期+长期)")

    def add(
        self,
        session_id: int,
        role: str,
        content: str,
        **kwargs: Any,
    ) -> None:
        """添加记忆，同时写入短期记忆和长期记忆。

        Args:
            session_id: 会话 ID。
            role: 消息角色 (system/user/assistant/tool)。
            content: 消息内容。
            **kwargs: 附加参数，如 tool_call 等。
        """
        tool_call = kwargs.get("tool_call")
        # 写入短期记忆
        self.short_term.add(
            session_id=session_id,
            role=role,
            content=content,
            tool_call=tool_call,
        )
        # 写入长期记忆
        metadata: Dict[str, Any] = {
            "session_id": session_id,
            "role": role,
        }
        # 将额外参数并入元数据（排除已处理的 tool_call）
        for key, value in kwargs.items():
            if key != "tool_call" and value is not None:
                metadata[key] = value
        self.long_term.add(content=content, metadata=metadata)

    def retrieve(
        self,
        query: str,
        session_id: Optional[int] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """检索记忆，融合短期记忆和长期记忆的结果。

        Args:
            query: 查询文本（短期记忆使用关键词匹配，长期记忆使用向量搜索）。
            session_id: 会话 ID，提供时检索该会话的短期记忆。
            limit: 各来源返回结果数量上限。

        Returns:
            融合后的记忆字典列表，每项包含 source 字段标识来源。
        """
        results: List[Dict[str, Any]] = []

        # 短期记忆：关键词搜索
        if session_id is not None:
            short_items = self.short_term.search(
                session_id=session_id,
                keyword=query,
                limit=limit,
            )
            for item in short_items:
                results.append({"source": "short_term", **item})

        # 长期记忆：向量相似性搜索
        long_items = self.long_term.search(query=query, limit=limit)
        for item in long_items:
            results.append(
                {
                    "source": "long_term",
                    "id": item.id,
                    "content": item.content,
                    "metadata": item.metadata,
                    "score": item.score,
                }
            )

        logger.info(
            f"记忆检索: query='{query}' session_id={session_id} "
            f"total={len(results)}"
        )
        return results

    def get_recent(
        self,
        session_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取短期记忆中的最近消息。

        Args:
            session_id: 会话 ID。
            limit: 返回消息数量上限。

        Returns:
            消息字典列表，时间从旧到新。
        """
        return self.short_term.get_recent(session_id=session_id, limit=limit)

    def search_long_term(
        self,
        query: str,
        limit: int = 5,
    ) -> List[MemoryItem]:
        """搜索长期记忆。

        Args:
            query: 查询文本。
            limit: 返回结果数量上限。

        Returns:
            匹配的记忆项列表。
        """
        return self.long_term.search(query=query, limit=limit)

    def clear_session(self, session_id: int) -> None:
        """清除指定会话的短期记忆。

        注意：此操作仅清除短期记忆，长期记忆中的数据不受影响。

        Args:
            session_id: 会话 ID。
        """
        self.short_term.clear(session_id=session_id)
        logger.info(f"会话短期记忆已清除: session_id={session_id}")

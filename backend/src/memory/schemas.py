"""记忆系统数据模型定义。"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """单条记忆项。"""

    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None


class MemorySearchResult(BaseModel):
    """记忆搜索结果集。"""

    items: List[MemoryItem]
    total: int

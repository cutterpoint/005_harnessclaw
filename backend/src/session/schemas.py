"""会话管理模块的 Pydantic 数据模型定义。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionCreate(BaseModel):
    """会话创建请求模型。"""

    title: Optional[str] = None


class SessionUpdate(BaseModel):
    """会话更新请求模型。"""

    title: Optional[str] = None
    status: Optional[str] = None  # active/archived/deleted


class SessionResponse(BaseModel):
    """会话信息响应模型。"""

    id: int
    user_id: int
    session_key: str
    title: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """消息创建请求模型。"""

    role: str
    content: str
    tool_call: Optional[str] = None
    tool_call_id: Optional[str] = None


class MessageResponse(BaseModel):
    """消息信息响应模型。"""

    id: int
    session_id: int
    role: str
    content: str
    tool_call: Optional[str]
    tool_call_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

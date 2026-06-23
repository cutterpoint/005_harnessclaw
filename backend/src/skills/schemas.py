"""技能管理模块的 Pydantic 数据模型定义。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SkillCreate(BaseModel):
    """技能创建请求模型。"""

    name: str
    description: Optional[str] = None
    prompt: Optional[str] = None


class SkillUpdate(BaseModel):
    """技能更新请求模型，仅更新非 None 字段。"""

    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    is_enabled: Optional[bool] = None


class SkillResponse(BaseModel):
    """技能信息响应模型。"""

    id: int
    user_id: int
    name: str
    description: Optional[str]
    prompt: Optional[str]
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SkillExecutionRequest(BaseModel):
    """技能执行请求模型。"""

    input: str
    session_id: Optional[int] = None


class SkillExecutionResult(BaseModel):
    """技能执行结果模型。"""

    skill_id: int
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float


class SkillTrainRequest(BaseModel):
    """技能学习请求模型。"""

    execution_history: List[Dict[str, Any]]
    skill_name: str
    description: Optional[str] = None

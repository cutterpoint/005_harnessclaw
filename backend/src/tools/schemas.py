"""工具模块的 Pydantic 数据模型定义。"""
import json
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, field_validator


class Parameter(BaseModel):
    """工具参数定义。"""

    name: str
    type: str  # string/integer/boolean/object/array
    required: bool = True
    description: Optional[str] = None


class ToolCreate(BaseModel):
    """工具创建请求模型。"""

    name: str
    description: Optional[str] = None
    function_name: str
    module_path: str
    parameters: List[Parameter]
    return_type: Optional[str] = None


class ToolUpdate(BaseModel):
    """工具更新请求模型，仅更新非 None 字段。"""

    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[List[Parameter]] = None
    is_enabled: Optional[bool] = None


class ToolResponse(BaseModel):
    """工具信息响应模型。"""

    id: int
    name: str
    description: Optional[str] = None
    function_name: str
    module_path: str
    parameters: List[Parameter]
    return_type: Optional[str] = None
    is_enabled: bool
    created_at: datetime

    @field_validator("parameters", mode="before")
    @classmethod
    def _parse_parameters(cls, v: Any) -> Any:
        """数据库中 parameters 为 JSON 字符串，需反序列化为列表。"""
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class ToolExecutionResult(BaseModel):
    """工具执行结果模型。"""

    tool_id: int
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float

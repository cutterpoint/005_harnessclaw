"""决策引擎模块的 Pydantic 数据模型定义。"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DecisionAction(BaseModel):
    """决策动作模型，描述决策引擎输出的单步动作。"""

    type: str  # tool_call/direct_response/finished
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_call_id: Optional[str] = None


class DecisionResult(BaseModel):
    """决策结果模型，包含动作、原始响应、工具调用及 Token 消耗。"""

    action: DecisionAction
    raw_response: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: Optional[int] = None


class ReflectionResult(BaseModel):
    """反思结果模型，评估动作执行情况并决定是否重试。"""

    success: bool
    feedback: str
    should_retry: bool = False
    improved_approach: Optional[str] = None

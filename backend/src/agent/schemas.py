"""Agent 引擎模块的数据模型定义。"""
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel


class AgentState(TypedDict):
    """Agent 运行状态，贯穿整个对话循环。

    Attributes:
        input: 用户输入文本。
        messages: 对话历史消息列表。
        tool_calls: 工具调用列表。
        tool_results: 工具执行结果列表。
        memory_items: 检索到的记忆项。
        finished: 是否已完成对话。
        summary: 最终总结回复。
        error: 错误信息。
        user_id: 用户 ID。
        session_id: 会话 ID。
        iteration: 当前迭代次数。
        max_iterations: 最大迭代次数。
    """

    input: str
    messages: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    memory_items: List[Dict[str, Any]]
    finished: bool
    summary: str
    error: Optional[str]
    user_id: Optional[int]
    session_id: Optional[int]
    iteration: int
    max_iterations: int


class AgentRunRequest(BaseModel):
    """Agent 运行请求模型。

    Attributes:
        message: 用户输入消息。
        session_id: 会话 ID，未提供时创建新会话。
        user_id: 用户 ID。
    """

    message: str
    session_id: Optional[int] = None
    user_id: Optional[int] = None


class AgentRunResponse(BaseModel):
    """Agent 运行响应模型。

    Attributes:
        response: 最终回复内容。
        session_id: 会话 ID。
        iterations: 实际迭代次数。
        tool_calls: 工具调用结果列表。
        error: 错误信息，无错误时为 None。
    """

    response: str
    session_id: int
    iterations: int
    tool_calls: List[Dict[str, Any]] = []
    error: Optional[str] = None


class AgentStatus(BaseModel):
    """Agent 状态信息模型。

    Attributes:
        state: 状态 (idle/running/finished/error)。
        iteration: 当前迭代次数。
        max_iterations: 最大迭代次数。
        session_id: 会话 ID。
        error: 错误信息。
    """

    state: str  # idle/running/finished/error
    iteration: int
    max_iterations: int
    session_id: Optional[int] = None
    error: Optional[str] = None

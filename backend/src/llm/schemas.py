"""LLM 模块 Pydantic 数据模型定义。"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LLMConfigCreate(BaseModel):
    """创建 LLM 配置的请求模型。"""

    name: str
    api_key: str
    api_base: str
    model_name: str
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7


class LLMConfigUpdate(BaseModel):
    """更新 LLM 配置的请求模型。"""

    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ChatMessage(BaseModel):
    """聊天消息模型。"""

    role: str  # system/user/assistant/tool
    content: str


class ChatCompletionRequest(BaseModel):
    """聊天补全请求模型。"""

    messages: List[ChatMessage]
    model: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None


class ChatCompletionResponse(BaseModel):
    """聊天补全响应模型。"""

    id: str
    model: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

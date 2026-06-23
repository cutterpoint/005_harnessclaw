"""提示词构建模块数据模型定义。"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    """对话消息模型。

    Attributes:
        role: 消息角色 (system/user/assistant/tool)。
        content: 消息内容。
        tool_call: 工具调用信息，仅在 assistant 角色调用工具时存在。
    """

    role: str
    content: str
    tool_call: Optional[Dict[str, Any]] = None


class ToolDescription(BaseModel):
    """工具描述模型。

    Attributes:
        name: 工具名称。
        description: 工具描述。
        parameters: 工具参数定义列表。
    """

    name: str
    description: str
    parameters: List[Dict[str, Any]]


class SkillDescription(BaseModel):
    """技能描述模型。

    Attributes:
        name: 技能名称。
        description: 技能描述。
        prompt: 技能提示词模板。
    """

    name: str
    description: str
    prompt: str


class PromptConfig(BaseModel):
    """提示词构建配置。

    Attributes:
        system_prompt: 自定义系统提示词，未提供时使用默认模板。
        max_tokens: 最大 Token 限制，超出时触发压缩。
        model_name: 目标模型名称，用于格式适配。
        include_tools: 是否在提示词中包含工具描述。
        include_skills: 是否在提示词中包含技能描述。
        history_limit: 对话历史获取条数上限。
    """

    system_prompt: Optional[str] = None
    max_tokens: int = 8192
    model_name: str = "gpt-4o"
    include_tools: bool = True
    include_skills: bool = True
    history_limit: int = 10


class BuiltPrompt(BaseModel):
    """构建完成的提示词。

    Attributes:
        messages: 组装后的消息列表。
        token_count: 当前消息列表的 Token 数量。
        is_compressed: 是否经过压缩。
        original_token_count: 压缩前的原始 Token 数量，未压缩时为 None。
    """

    messages: List[Message]
    token_count: int
    is_compressed: bool = False
    original_token_count: Optional[int] = None

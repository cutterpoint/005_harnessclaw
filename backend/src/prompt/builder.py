"""提示词构建器模块 - 动态构建符合 LLM 格式要求的提示词。"""
import json
from typing import Any, Dict, List, Optional

from src.context.compressor import ContextCompressor
from src.context.token_counter import TokenCounter
from src.core.config import settings
from src.memory.manager import MemorySystem
from src.monitoring.logger import Logger
from src.prompt.schemas import (
    BuiltPrompt,
    Message,
    PromptConfig,
    SkillDescription,
    ToolDescription,
)
from src.skills.service import SkillManager
from src.tools.executor import ToolExecutor

logger = Logger()


class PromptBuilder:
    """提示词构建器，组装系统提示词、对话历史、工具与技能描述。

    所有依赖（记忆系统、工具执行器、技能管理器、上下文压缩器）均为可选，
    未提供时跳过对应部分的组装。
    """

    def __init__(
        self,
        memory_system: Optional[MemorySystem] = None,
        tool_executor: Optional[ToolExecutor] = None,
        skill_manager: Optional[SkillManager] = None,
        context_compressor: Optional[ContextCompressor] = None,
    ) -> None:
        """初始化提示词构建器。

        Args:
            memory_system: 记忆系统实例，用于获取对话历史。
            tool_executor: 工具执行器实例，用于获取工具描述。
            skill_manager: 技能管理器实例，用于获取技能描述。
            context_compressor: 上下文压缩器实例，用于超限压缩。
        """
        self.memory_system = memory_system
        self.tool_executor = tool_executor
        self.skill_manager = skill_manager
        self.context_compressor = context_compressor
        self.token_counter = TokenCounter()
        logger.info("提示词构建器已初始化")

    def build(
        self,
        session_id: Optional[int],
        user_message: str,
        user_id: Optional[int] = None,
        config: Optional[PromptConfig] = None,
    ) -> BuiltPrompt:
        """构建完整提示词。

        流程：构建系统提示词 -> 获取对话历史 -> 获取工具描述 ->
        获取技能描述 -> 组装 -> 检查 Token 限制 -> 压缩(如需) -> 返回。

        Args:
            session_id: 会话 ID，提供时获取对话历史。
            user_message: 当前用户输入。
            user_id: 用户 ID，提供时获取该用户的技能。
            config: 提示词配置，未提供时使用默认配置。

        Returns:
            构建完成的提示词。
        """
        # 使用默认配置
        if config is None:
            config = PromptConfig(
                max_tokens=settings.MAX_TOKEN_LIMIT,
                model_name=settings.DEFAULT_MODEL,
            )

        # 1. 构建系统提示词
        system_prompt = self.build_system_prompt(config)

        # 2. 获取工具描述
        tools_section = ""
        if config.include_tools and self.tool_executor is not None:
            try:
                tools = self.add_tools()
                if tools:
                    tools_section = self._format_tools_section(tools)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"获取工具描述失败: {exc}")

        # 3. 获取技能描述
        skills_section = ""
        if (
            config.include_skills
            and self.skill_manager is not None
            and user_id is not None
        ):
            try:
                skills = self.add_skills(user_id)
                if skills:
                    skills_section = self._format_skills_section(skills)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"获取技能描述失败: {exc}")

        # 组装完整系统提示词
        full_system_prompt = system_prompt + tools_section + skills_section

        # 4. 组装消息列表
        messages: List[Message] = [
            Message(role="system", content=full_system_prompt)
        ]

        # 5. 获取对话历史
        if self.memory_system is not None and session_id is not None:
            try:
                history = self.memory_system.get_recent(
                    session_id=session_id, limit=config.history_limit
                )
                if history:
                    messages.extend(self.add_messages(history))
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"获取对话历史失败: {exc}")

        # 6. 添加当前用户消息
        messages.append(Message(role="user", content=user_message))

        # 7. 计算 Token 数量
        dict_messages = self.format(messages, config.model_name)
        token_count = self.token_counter.count_messages(dict_messages)

        # 8. 检查 Token 限制并压缩
        is_compressed = False
        original_token_count: Optional[int] = None

        if (
            token_count > config.max_tokens
            and self.context_compressor is not None
        ):
            try:
                result = self.context_compressor.compress(
                    dict_messages, config.max_tokens
                )
                compressed_dicts = result.messages
                messages = self.add_messages(compressed_dicts)
                original_token_count = token_count
                token_count = self.token_counter.count_messages(
                    self.format(messages, config.model_name)
                )
                is_compressed = True
                logger.info(
                    f"提示词已压缩: {original_token_count} -> "
                    f"{token_count} tokens"
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"上下文压缩失败: {exc}")

        return BuiltPrompt(
            messages=messages,
            token_count=token_count,
            is_compressed=is_compressed,
            original_token_count=original_token_count,
        )

    def build_system_prompt(self, config: PromptConfig) -> str:
        """构建系统提示词。

        包含角色定义、指令模板、格式说明、约束条件与输出格式。
        若配置中提供了自定义系统提示词，则直接使用；否则使用默认模板。

        Args:
            config: 提示词配置。

        Returns:
            系统提示词文本。
        """
        if config.system_prompt is not None:
            return config.system_prompt
        return self.get_default_system_prompt()

    @staticmethod
    def get_default_system_prompt() -> str:
        """获取默认系统提示词模板。

        Returns:
            默认系统提示词，包含角色定义、能力说明与注意事项。
        """
        return (
            "你是一个智能AI助手，可以帮助用户完成各种任务。\n\n"
            "你可以使用以下能力：\n"
            "1. 调用工具来获取信息或执行操作\n"
            "2. 使用已注册的技能来处理特定任务\n"
            "3. 从对话历史中获取上下文\n\n"
            "注意事项：\n"
            "- 如果需要使用工具，请按照工具调用的格式输出\n"
            "- 如果不需要工具，直接回复用户\n"
            "- 保持回复简洁、准确、有帮助"
        )

    def add_messages(self, messages: List[Dict[str, Any]]) -> List[Message]:
        """将字典消息列表转换为 Message 对象列表。

        支持字典和对象两种输入形式，兼容 tool_call 与 tool_calls 字段。

        Args:
            messages: 原始消息列表。

        Returns:
            转换后的 Message 对象列表。
        """
        result: List[Message] = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                tool_call = msg.get("tool_call")
                # 兼容 OpenAI 格式的 tool_calls（列表）字段，包装为字典
                if tool_call is None:
                    tool_calls = msg.get("tool_calls")
                    if tool_calls is not None:
                        tool_call = (
                            {"tool_calls": tool_calls}
                            if isinstance(tool_calls, list)
                            else tool_calls
                        )
            else:
                role = getattr(msg, "role", "user")
                content = getattr(msg, "content", "")
                tool_call = getattr(msg, "tool_call", None)
            result.append(
                Message(
                    role=role,
                    content=str(content) if content is not None else "",
                    tool_call=tool_call,
                )
            )
        return result

    def add_tools(self) -> List[ToolDescription]:
        """获取可用工具的描述列表。

        Returns:
            工具描述列表，工具执行器未配置时返回空列表。
        """
        if self.tool_executor is None:
            return []
        tools = self.tool_executor.get_tools()
        result: List[ToolDescription] = []
        for tool in tools:
            parameters = self._parse_parameters(
                getattr(tool, "parameters", [])
            )
            result.append(
                ToolDescription(
                    name=getattr(tool, "name", ""),
                    description=getattr(tool, "description", "") or "",
                    parameters=parameters,
                )
            )
        return result

    def add_skills(self, user_id: int) -> List[SkillDescription]:
        """获取用户已注册技能的描述列表。

        Args:
            user_id: 用户 ID。

        Returns:
            技能描述列表，技能管理器未配置时返回空列表。
        """
        if self.skill_manager is None:
            return []
        result_dict = self.skill_manager.get_skills(user_id=user_id)
        items = (
            result_dict.get("items", []) if isinstance(result_dict, dict) else []
        )
        result: List[SkillDescription] = []
        for skill in items:
            result.append(
                SkillDescription(
                    name=getattr(skill, "name", ""),
                    description=getattr(skill, "description", "") or "",
                    prompt=getattr(skill, "prompt", "") or "",
                )
            )
        return result

    def format(
        self, messages: List[Message], model_name: str
    ) -> List[Dict[str, Any]]:
        """将 Message 对象列表格式化为 OpenAI 消息字典列表。

        Args:
            messages: Message 对象列表。
            model_name: 目标模型名称，用于后续格式适配扩展。

        Returns:
            OpenAI 格式的消息字典列表。
        """
        result: List[Dict[str, Any]] = []
        for msg in messages:
            item: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.tool_call is not None:
                item["tool_call"] = msg.tool_call
            result.append(item)
        return result

    # ---- 内部方法 ----

    def _parse_parameters(self, parameters: Any) -> List[Dict[str, Any]]:
        """解析工具参数定义，兼容 JSON 字符串与列表两种存储形式。"""
        if isinstance(parameters, str):
            try:
                parsed = json.loads(parameters)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        if isinstance(parameters, list):
            return parameters
        return []

    def _format_tools_section(self, tools: List[ToolDescription]) -> str:
        """将工具描述列表格式化为系统提示词中的工具说明段落。"""
        if not tools:
            return ""
        lines = ["\n\n## 可用工具"]
        for idx, tool in enumerate(tools, 1):
            lines.append(f"{idx}. {tool.name}: {tool.description}")
            if tool.parameters:
                for param in tool.parameters:
                    name = param.get("name", "")
                    ptype = param.get("type", "string")
                    desc = param.get("description", "")
                    required = param.get("required", True)
                    req_str = "必填" if required else "可选"
                    lines.append(
                        f"     - {name} ({ptype}, {req_str}): {desc}"
                    )
        return "\n".join(lines)

    def _format_skills_section(self, skills: List[SkillDescription]) -> str:
        """将技能描述列表格式化为系统提示词中的技能说明段落。"""
        if not skills:
            return ""
        lines = ["\n\n## 可用技能"]
        for idx, skill in enumerate(skills, 1):
            lines.append(f"{idx}. {skill.name}: {skill.description}")
            if skill.prompt:
                lines.append(f"   提示词: {skill.prompt}")
        return "\n".join(lines)

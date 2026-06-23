"""提示词构建模块单元测试 - 使用 mock 对象，不依赖外部服务。"""
import os
import sys
import unittest
from unittest.mock import MagicMock

import pytest

# 确保后端目录在 sys.path 中
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from src.context.schemas import CompressionResult
from src.context.token_counter import TokenCounter
from src.prompt import BuiltPrompt, Message, PromptBuilder, PromptConfig


# ----------------------------- 系统提示词测试 -----------------------------
class TestSystemPrompt:
    """系统提示词构建相关测试。"""

    def test_get_default_system_prompt(self):
        """测试获取默认系统提示词。"""
        prompt = PromptBuilder.get_default_system_prompt()

        # 应包含角色定义
        assert "智能AI助手" in prompt
        # 应包含能力说明
        assert "调用工具" in prompt
        assert "技能" in prompt
        # 应包含约束条件
        assert "注意事项" in prompt
        # 应为非空字符串
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_system_prompt_default(self):
        """测试使用默认配置构建系统提示词。"""
        builder = PromptBuilder()
        config = PromptConfig()
        prompt = builder.build_system_prompt(config)

        # 未提供自定义提示词时应返回默认模板
        assert prompt == PromptBuilder.get_default_system_prompt()

    def test_build_system_prompt_custom(self):
        """测试使用自定义系统提示词。"""
        builder = PromptBuilder()
        custom_prompt = "你是一个专门的翻译助手。"
        config = PromptConfig(system_prompt=custom_prompt)
        prompt = builder.build_system_prompt(config)

        assert prompt == custom_prompt


# ----------------------------- 基本构建测试 -----------------------------
class TestBuildBasic:
    """基本提示词构建测试（无依赖）。"""

    def test_build_basic(self):
        """测试无依赖时的基本构建。"""
        builder = PromptBuilder()
        user_message = "你好，请介绍一下自己。"

        result = builder.build(
            session_id=None, user_message=user_message
        )

        # 应返回 BuiltPrompt 实例
        assert isinstance(result, BuiltPrompt)
        # 应包含系统消息和用户消息
        assert len(result.messages) == 2
        assert result.messages[0].role == "system"
        assert result.messages[1].role == "user"
        assert result.messages[1].content == user_message
        # Token 计数应为正数
        assert result.token_count > 0
        # 未压缩
        assert result.is_compressed is False
        assert result.original_token_count is None

    def test_build_with_config(self):
        """测试使用自定义配置构建。"""
        builder = PromptBuilder()
        config = PromptConfig(
            system_prompt="自定义系统提示词",
            max_tokens=4096,
            model_name="gpt-4o-mini",
            include_tools=False,
            include_skills=False,
        )

        result = builder.build(
            session_id=None, user_message="测试", config=config
        )

        assert result.messages[0].content == "自定义系统提示词"
        assert result.messages[0].role == "system"

    def test_build_empty_message(self):
        """测试空用户消息的构建。"""
        builder = PromptBuilder()
        result = builder.build(session_id=None, user_message="")

        assert len(result.messages) == 2
        assert result.messages[1].content == ""


# ----------------------------- 历史消息测试 -----------------------------
class TestBuildWithHistory:
    """带历史消息的构建测试。"""

    def test_build_with_history(self):
        """测试带历史消息的构建（mock memory_system）。"""
        mock_memory = MagicMock()
        mock_memory.get_recent.return_value = [
            {"role": "user", "content": "之前的问题"},
            {"role": "assistant", "content": "之前的回答"},
        ]

        builder = PromptBuilder(memory_system=mock_memory)
        result = builder.build(
            session_id=1, user_message="新的问题"
        )

        # 应包含：系统 + 2条历史 + 当前用户消息 = 4 条
        assert len(result.messages) == 4
        assert result.messages[0].role == "system"
        assert result.messages[1].role == "user"
        assert result.messages[1].content == "之前的问题"
        assert result.messages[2].role == "assistant"
        assert result.messages[2].content == "之前的回答"
        assert result.messages[3].role == "user"
        assert result.messages[3].content == "新的问题"

        # 验证 get_recent 被正确调用
        mock_memory.get_recent.assert_called_once_with(
            session_id=1, limit=10
        )

    def test_build_with_history_limit(self):
        """测试历史消息条数限制。"""
        mock_memory = MagicMock()
        mock_memory.get_recent.return_value = []

        builder = PromptBuilder(memory_system=mock_memory)
        config = PromptConfig(history_limit=5)
        builder.build(session_id=1, user_message="测试", config=config)

        mock_memory.get_recent.assert_called_once_with(
            session_id=1, limit=5
        )

    def test_build_without_session_id(self):
        """测试未提供 session_id 时不获取历史。"""
        mock_memory = MagicMock()
        builder = PromptBuilder(memory_system=mock_memory)
        result = builder.build(session_id=None, user_message="测试")

        # 不应调用 get_recent
        mock_memory.get_recent.assert_not_called()
        # 只有系统消息和用户消息
        assert len(result.messages) == 2


# ----------------------------- 工具描述测试 -----------------------------
class TestBuildWithTools:
    """带工具描述的构建测试。"""

    def test_build_with_tools(self):
        """测试带工具描述的构建（mock tool_executor）。"""
        mock_tool = MagicMock()
        mock_tool.name = "计算器"
        mock_tool.description = "执行数学计算"
        mock_tool.parameters = [
            {"name": "expression", "type": "string", "required": True,
             "description": "数学表达式"},
        ]

        mock_executor = MagicMock()
        mock_executor.get_tools.return_value = [mock_tool]

        builder = PromptBuilder(tool_executor=mock_executor)
        result = builder.build(
            session_id=None, user_message="计算 1+1"
        )

        # 系统提示词中应包含工具描述
        system_content = result.messages[0].content
        assert "可用工具" in system_content
        assert "计算器" in system_content
        assert "执行数学计算" in system_content
        assert "expression" in system_content

    def test_build_without_tools(self):
        """测试配置关闭工具描述时的构建。"""
        mock_tool = MagicMock()
        mock_tool.name = "计算器"
        mock_tool.description = "执行数学计算"
        mock_tool.parameters = []

        mock_executor = MagicMock()
        mock_executor.get_tools.return_value = [mock_tool]

        builder = PromptBuilder(tool_executor=mock_executor)
        config = PromptConfig(include_tools=False)
        result = builder.build(
            session_id=None, user_message="测试", config=config
        )

        # 系统提示词中不应包含工具描述
        system_content = result.messages[0].content
        assert "可用工具" not in system_content

    def test_add_tools_with_json_parameters(self):
        """测试工具参数为 JSON 字符串时的解析。"""
        import json

        mock_tool = MagicMock()
        mock_tool.name = "搜索"
        mock_tool.description = "搜索网络"
        mock_tool.parameters = json.dumps(
            [{"name": "query", "type": "string", "required": True,
              "description": "搜索关键词"}]
        )

        mock_executor = MagicMock()
        mock_executor.get_tools.return_value = [mock_tool]

        builder = PromptBuilder(tool_executor=mock_executor)
        tools = builder.add_tools()

        assert len(tools) == 1
        assert tools[0].name == "搜索"
        assert len(tools[0].parameters) == 1
        assert tools[0].parameters[0]["name"] == "query"


# ----------------------------- 技能描述测试 -----------------------------
class TestBuildWithSkills:
    """带技能描述的构建测试。"""

    def test_build_with_skills(self):
        """测试带技能描述的构建（mock skill_manager）。"""
        mock_skill = MagicMock()
        mock_skill.name = "翻译技能"
        mock_skill.description = "中英翻译"
        mock_skill.prompt = "你是一个专业翻译。"

        mock_manager = MagicMock()
        mock_manager.get_skills.return_value = {
            "items": [mock_skill],
            "total": 1,
            "page": 1,
            "limit": 20,
        }

        builder = PromptBuilder(skill_manager=mock_manager)
        result = builder.build(
            session_id=None, user_message="翻译", user_id=1
        )

        # 系统提示词中应包含技能描述
        system_content = result.messages[0].content
        assert "可用技能" in system_content
        assert "翻译技能" in system_content
        assert "中英翻译" in system_content
        assert "你是一个专业翻译" in system_content

        # 验证 get_skills 被调用
        mock_manager.get_skills.assert_called_once_with(user_id=1)

    def test_build_without_user_id(self):
        """测试未提供 user_id 时不获取技能。"""
        mock_manager = MagicMock()
        builder = PromptBuilder(skill_manager=mock_manager)
        result = builder.build(
            session_id=None, user_message="测试", user_id=None
        )

        mock_manager.get_skills.assert_not_called()

    def test_build_skills_disabled(self):
        """测试配置关闭技能描述时的构建。"""
        mock_skill = MagicMock()
        mock_skill.name = "技能"
        mock_skill.description = "描述"
        mock_skill.prompt = "提示词"

        mock_manager = MagicMock()
        mock_manager.get_skills.return_value = {"items": [mock_skill]}

        builder = PromptBuilder(skill_manager=mock_manager)
        config = PromptConfig(include_skills=False)
        result = builder.build(
            session_id=None, user_message="测试",
            user_id=1, config=config
        )

        system_content = result.messages[0].content
        assert "可用技能" not in system_content


# ----------------------------- 压缩测试 -----------------------------
class TestBuildWithCompression:
    """需要压缩的构建测试。"""

    def test_build_with_compression(self):
        """测试需要压缩的构建（mock context_compressor）。"""
        # 构造压缩后的消息（仅保留系统消息和用户消息）
        compressed_messages = [
            {"role": "system", "content": "压缩后的系统提示词"},
            {"role": "user", "content": "压缩后的用户消息"},
        ]
        mock_result = CompressionResult(
            messages=compressed_messages,
            original_token_count=10000,
            compressed_token_count=50,
            compression_ratio=0.005,
            method="trim",
        )

        mock_compressor = MagicMock()
        mock_compressor.compress.return_value = mock_result

        builder = PromptBuilder(context_compressor=mock_compressor)
        # 设置极低的 Token 限制以确保触发压缩
        config = PromptConfig(max_tokens=1)

        result = builder.build(
            session_id=None, user_message="测试", config=config
        )

        # 应触发压缩
        assert result.is_compressed is True
        assert result.original_token_count is not None
        assert result.original_token_count > result.token_count
        # 消息应来自压缩结果
        assert len(result.messages) == 2
        assert result.messages[0].content == "压缩后的系统提示词"
        assert result.messages[1].content == "压缩后的用户消息"

        # 验证 compress 被调用
        mock_compressor.compress.assert_called_once()

    def test_build_no_compression_within_limit(self):
        """测试未超限时不需要压缩。"""
        mock_compressor = MagicMock()
        builder = PromptBuilder(context_compressor=mock_compressor)
        config = PromptConfig(max_tokens=100000)  # 设置很高的限制

        result = builder.build(
            session_id=None, user_message="测试", config=config
        )

        assert result.is_compressed is False
        assert result.original_token_count is None
        mock_compressor.compress.assert_not_called()

    def test_build_no_compressor_over_limit(self):
        """测试超限但无压缩器时不压缩。"""
        builder = PromptBuilder()  # 不提供 context_compressor
        config = PromptConfig(max_tokens=1)  # 极低限制

        result = builder.build(
            session_id=None, user_message="测试", config=config
        )

        # 超限但无压缩器，不压缩
        assert result.is_compressed is False
        assert result.token_count > config.max_tokens


# ----------------------------- 格式转换测试 -----------------------------
class TestFormat:
    """消息格式转换测试。"""

    def test_format_openai(self):
        """测试格式化为 OpenAI 格式。"""
        builder = PromptBuilder()
        messages = [
            Message(role="system", content="系统提示"),
            Message(role="user", content="用户消息"),
            Message(role="assistant", content="助手回复"),
        ]

        result = builder.format(messages, "gpt-4o")

        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)
        assert result[0] == {"role": "system", "content": "系统提示"}
        assert result[1] == {"role": "user", "content": "用户消息"}
        assert result[2] == {"role": "assistant", "content": "助手回复"}

    def test_format_with_tool_call(self):
        """测试带工具调用的格式化。"""
        builder = PromptBuilder()
        tool_call = {"name": "calculator", "arguments": {"expr": "1+1"}}
        messages = [
            Message(
                role="assistant",
                content="调用计算器",
                tool_call=tool_call,
            ),
        ]

        result = builder.format(messages, "gpt-4o")

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "调用计算器"
        assert result[0]["tool_call"] == tool_call

    def test_add_messages(self):
        """测试消息格式转换（字典 -> Message）。"""
        builder = PromptBuilder()
        raw_messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你的？"},
            {"role": "user", "content": "谢谢"},
        ]

        result = builder.add_messages(raw_messages)

        assert len(result) == 3
        assert all(isinstance(msg, Message) for msg in result)
        assert result[0].role == "user"
        assert result[0].content == "你好"
        assert result[1].role == "assistant"
        assert result[1].content == "你好！有什么可以帮你的？"
        assert result[2].role == "user"
        assert result[2].content == "谢谢"

    def test_add_messages_with_tool_call(self):
        """测试带工具调用的消息转换。"""
        builder = PromptBuilder()
        tool_call = {"name": "search", "arguments": {"q": "test"}}
        raw_messages = [
            {
                "role": "assistant",
                "content": "搜索中",
                "tool_call": tool_call,
            },
        ]

        result = builder.add_messages(raw_messages)

        assert len(result) == 1
        assert result[0].role == "assistant"
        assert result[0].tool_call == tool_call

    def test_add_messages_tool_calls_key(self):
        """测试 tool_calls 字段名兼容。"""
        builder = PromptBuilder()
        raw_messages = [
            {
                "role": "assistant",
                "content": "调用工具",
                "tool_calls": [{"id": "call_1"}],
            },
        ]

        result = builder.add_messages(raw_messages)

        # tool_calls（列表）应被包装为字典存入 tool_call 字段
        assert result[0].tool_call == {"tool_calls": [{"id": "call_1"}]}

    def test_add_messages_empty(self):
        """测试空消息列表转换。"""
        builder = PromptBuilder()
        result = builder.add_messages([])
        assert result == []


# ----------------------------- Token 计数测试 -----------------------------
class TestTokenCount:
    """Token 计数验证测试。"""

    def test_token_count(self):
        """测试 Token 计数验证。"""
        builder = PromptBuilder()
        result = builder.build(
            session_id=None, user_message="这是一个测试消息"
        )

        # 独立计算 Token 数量
        counter = TokenCounter()
        dict_messages = builder.format(result.messages, "gpt-4o")
        expected_count = counter.count_messages(dict_messages)

        # 构建结果的 token_count 应与独立计算一致
        assert result.token_count == expected_count

    def test_token_count_increases_with_content(self):
        """测试内容增加时 Token 数增加。"""
        builder = PromptBuilder()

        short_result = builder.build(
            session_id=None, user_message="短消息"
        )
        long_result = builder.build(
            session_id=None, user_message="这是一个非常非常非常长的消息内容" * 10
        )

        assert long_result.token_count > short_result.token_count

    def test_token_count_after_compression(self):
        """测试压缩后 Token 计数正确。"""
        compressed_messages = [
            {"role": "system", "content": "短提示"},
            {"role": "user", "content": "短消息"},
        ]
        mock_result = CompressionResult(
            messages=compressed_messages,
            original_token_count=5000,
            compressed_token_count=10,
            compression_ratio=0.002,
            method="trim",
        )

        mock_compressor = MagicMock()
        mock_compressor.compress.return_value = mock_result

        builder = PromptBuilder(context_compressor=mock_compressor)
        # 设置极低的 Token 限制以确保触发压缩
        config = PromptConfig(max_tokens=1)

        result = builder.build(
            session_id=None, user_message="测试", config=config
        )

        # 压缩后的 token_count 应基于压缩后的消息重新计算
        counter = TokenCounter()
        expected_count = counter.count_messages(compressed_messages)
        assert result.token_count == expected_count
        assert result.is_compressed is True
        assert result.original_token_count is not None


# ----------------------------- 完整集成测试 -----------------------------
class TestBuildIntegration:
    """完整集成构建测试。"""

    def test_build_with_all_dependencies(self):
        """测试带所有依赖的完整构建。"""
        # mock 记忆系统
        mock_memory = MagicMock()
        mock_memory.get_recent.return_value = [
            {"role": "user", "content": "历史问题"},
            {"role": "assistant", "content": "历史回答"},
        ]

        # mock 工具执行器
        mock_tool = MagicMock()
        mock_tool.name = "搜索工具"
        mock_tool.description = "搜索信息"
        mock_tool.parameters = [
            {"name": "query", "type": "string", "required": True,
             "description": "搜索词"},
        ]
        mock_executor = MagicMock()
        mock_executor.get_tools.return_value = [mock_tool]

        # mock 技能管理器
        mock_skill = MagicMock()
        mock_skill.name = "总结技能"
        mock_skill.description = "总结文本"
        mock_skill.prompt = "请总结以下内容。"
        mock_manager = MagicMock()
        mock_manager.get_skills.return_value = {
            "items": [mock_skill],
            "total": 1,
        }

        builder = PromptBuilder(
            memory_system=mock_memory,
            tool_executor=mock_executor,
            skill_manager=mock_manager,
        )

        result = builder.build(
            session_id=1,
            user_message="请帮我搜索并总结",
            user_id=1,
        )

        # 应包含：系统(含工具+技能) + 2条历史 + 用户消息 = 4 条
        assert len(result.messages) == 4
        assert result.token_count > 0
        assert result.is_compressed is False

        # 系统提示词应包含工具和技能描述
        system_content = result.messages[0].content
        assert "可用工具" in system_content
        assert "搜索工具" in system_content
        assert "可用技能" in system_content
        assert "总结技能" in system_content

        # 历史消息应正确插入
        assert result.messages[1].content == "历史问题"
        assert result.messages[2].content == "历史回答"

        # 当前用户消息
        assert result.messages[3].content == "请帮我搜索并总结"


if __name__ == "__main__":
    unittest.main()

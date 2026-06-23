"""决策引擎模块单元测试 - 使用 mock 测试，不实际调用 LLM API。"""
import json
import os
import sys
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

# 确保后端目录在 sys.path 中
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from src.decision.engine import DecisionEngine
from src.decision.schemas import DecisionAction, DecisionResult, ReflectionResult
from src.llm.schemas import ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from src.tools.schemas import ToolExecutionResult


# ----------------------------- 辅助函数 -----------------------------

def _make_chat_response(
    content: str = "你好",
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
) -> ChatCompletionResponse:
    """构造模拟的 ChatCompletionResponse。"""
    return ChatCompletionResponse(
        id="chatcmpl-test-001",
        model="gpt-4o",
        content=content,
        tool_calls=tool_calls,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


def _make_tool_call_dict(
    name: str = "calculator",
    arguments: Optional[Dict[str, Any]] = None,
    call_id: str = "call_abc",
) -> Dict[str, Any]:
    """构造 OpenAI 格式的工具调用字典（arguments 为 JSON 字符串）。"""
    args = arguments if arguments is not None else {"expression": "1+1"}
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args, ensure_ascii=False),
        },
    }


_SENTINEL = object()


def _make_tool_execution_result(
    success: bool = True,
    result: Any = _SENTINEL,
    error: Optional[str] = None,
) -> ToolExecutionResult:
    """构造模拟的工具执行结果。"""
    return ToolExecutionResult(
        tool_id=1,
        success=success,
        result={"result": 2} if result is _SENTINEL else result,
        error=error,
        execution_time=0.01,
    )


# ----------------------------- 测试夹具 -----------------------------

@pytest.fixture
def mock_llm_service():
    """创建 mock LLMService。"""
    return MagicMock()


@pytest.fixture
def mock_tool_executor():
    """创建 mock ToolExecutor。"""
    executor = MagicMock()
    executor.get_openai_tools.return_value = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "计算器",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]
    return executor


@pytest.fixture
def engine(mock_llm_service, mock_tool_executor):
    """创建带工具执行器的决策引擎。"""
    return DecisionEngine(
        llm_service=mock_llm_service,
        tool_executor=mock_tool_executor,
    )


@pytest.fixture
def engine_no_tools(mock_llm_service):
    """创建不带工具执行器的决策引擎。"""
    return DecisionEngine(llm_service=mock_llm_service)


# ----------------------------- 测试用例 -----------------------------

class TestDecisionEngine:
    """决策引擎核心测试。"""

    def test_decide_direct_response(self, engine, mock_llm_service):
        """测试 LLM 直接回复（无工具调用）。"""
        mock_llm_service.chat_completion.return_value = _make_chat_response(
            content="你好，我是助手。",
            tool_calls=None,
        )

        messages = [{"role": "user", "content": "你好"}]
        result = engine.decide(messages, user_id=1, session_id=1)

        assert isinstance(result, DecisionResult)
        assert result.action.type == "direct_response"
        assert result.action.content == "你好，我是助手。"
        assert result.action.tool_name is None
        assert result.tool_calls is None
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 20
        assert result.total_tokens == 30
        assert result.latency_ms is not None
        assert result.latency_ms >= 0
        # 验证 LLM 被调用一次
        mock_llm_service.chat_completion.assert_called_once()

    def test_decide_tool_call(self, engine, mock_llm_service):
        """测试 LLM 返回工具调用。"""
        tool_call = _make_tool_call_dict(
            name="calculator",
            arguments={"expression": "1+2"},
        )
        mock_llm_service.chat_completion.return_value = _make_chat_response(
            content="",
            tool_calls=[tool_call],
        )

        messages = [{"role": "user", "content": "计算 1+2"}]
        result = engine.decide(messages, user_id=1, session_id=1)

        assert result.action.type == "tool_call"
        assert result.action.tool_name == "calculator"
        assert result.action.tool_arguments == {"expression": "1+2"}
        assert result.action.tool_call_id == "call_abc"
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["function"]["name"] == "calculator"
        # 验证请求中包含工具定义
        call_kwargs = mock_llm_service.chat_completion.call_args
        request = call_kwargs.args[0]
        assert request.tools is not None
        assert len(request.tools) == 1

    def test_parse_tool_calls(self, engine):
        """测试解析工具调用（arguments JSON 字符串转字典）。"""
        tool_calls = [
            _make_tool_call_dict(name="tool1", arguments={"a": 1}, call_id="call_1"),
            _make_tool_call_dict(
                name="tool2", arguments={"b": "hello"}, call_id="call_2"
            ),
        ]
        response = _make_chat_response(content="", tool_calls=tool_calls)

        parsed = engine.parse_tool_calls(response)

        assert len(parsed) == 2
        assert parsed[0]["id"] == "call_1"
        assert parsed[0]["type"] == "function"
        assert parsed[0]["function"]["name"] == "tool1"
        assert parsed[0]["function"]["arguments"] == {"a": 1}
        assert parsed[1]["id"] == "call_2"
        assert parsed[1]["function"]["name"] == "tool2"
        assert parsed[1]["function"]["arguments"] == {"b": "hello"}

    def test_parse_tool_calls_empty(self, engine):
        """测试无工具调用时返回空列表。"""
        response = _make_chat_response(content="直接回复", tool_calls=None)
        parsed = engine.parse_tool_calls(response)
        assert parsed == []

    def test_parse_tool_calls_invalid_json(self, engine):
        """测试 arguments 为非法 JSON 时回退为空字典。"""
        tool_call = {
            "id": "call_bad",
            "type": "function",
            "function": {
                "name": "bad_tool",
                "arguments": "{invalid json}",
            },
        }
        response = _make_chat_response(content="", tool_calls=[tool_call])
        parsed = engine.parse_tool_calls(response)

        assert len(parsed) == 1
        assert parsed[0]["function"]["arguments"] == {}

    def test_execute_tool_calls_success(self, engine, mock_tool_executor):
        """测试执行工具调用成功。"""
        mock_tool_executor.execute.return_value = _make_tool_execution_result(
            success=True,
            result={"result": 3},
        )

        tool_calls = [
            {
                "id": "call_abc",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": {"expression": "1+2"},
                },
            }
        ]
        results = engine.execute_tool_calls(tool_calls, user_id=1, session_id=1)

        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["result"] == {"result": 3}
        assert results[0]["error"] is None
        assert results[0]["tool_name"] == "calculator"
        assert results[0]["tool_call_id"] == "call_abc"
        # 验证执行器被调用
        mock_tool_executor.execute.assert_called_once_with(
            tool_name="calculator",
            arguments={"expression": "1+2"},
            user_id=1,
            session_id=1,
        )

    def test_execute_tool_calls_failure(self, engine, mock_tool_executor):
        """测试执行工具调用失败。"""
        mock_tool_executor.execute.return_value = _make_tool_execution_result(
            success=False,
            result=None,
            error="参数验证失败",
        )

        tool_calls = [
            {
                "id": "call_xyz",
                "type": "function",
                "function": {"name": "calculator", "arguments": {}},
            }
        ]
        results = engine.execute_tool_calls(tool_calls, user_id=1, session_id=1)

        assert len(results) == 1
        assert results[0]["success"] is False
        assert results[0]["error"] == "参数验证失败"
        assert results[0]["result"] is None

    def test_execute_tool_calls_exception(self, engine, mock_tool_executor):
        """测试工具执行抛出异常时被捕获。"""
        mock_tool_executor.execute.side_effect = RuntimeError("执行崩溃")

        tool_calls = [
            {
                "id": "call_err",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": {"expression": "1+1"},
                },
            }
        ]
        results = engine.execute_tool_calls(tool_calls, user_id=1)

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "执行崩溃" in results[0]["error"]

    def test_execute_tool_calls_no_executor(self, engine_no_tools):
        """测试无工具执行器时返回失败结果。"""
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": {"expression": "1+1"},
                },
            }
        ]
        results = engine_no_tools.execute_tool_calls(tool_calls, user_id=1)

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "未配置" in results[0]["error"]

    def test_reflect_success(self, engine):
        """测试反思工具执行成功。"""
        action = DecisionAction(
            type="tool_call",
            tool_name="calculator",
            tool_arguments={"expression": "1+1"},
            tool_call_id="call_abc",
        )
        result = _make_tool_execution_result(success=True, result={"result": 2})

        reflection = engine.reflect(action, result=result)

        assert isinstance(reflection, ReflectionResult)
        assert reflection.success is True
        assert reflection.should_retry is False

    def test_reflect_failure(self, engine):
        """测试反思工具执行失败（应重试）。"""
        action = DecisionAction(
            type="tool_call",
            tool_name="calculator",
            tool_arguments={},
            tool_call_id="call_xyz",
        )
        result = _make_tool_execution_result(
            success=False,
            error="缺少必填参数",
        )

        reflection = engine.reflect(action, result=result)

        assert reflection.success is False
        assert reflection.should_retry is True
        assert "缺少必填参数" in reflection.feedback
        assert reflection.improved_approach is not None

    def test_reflect_direct_response(self, engine):
        """测试直接回复的反思（应成功）。"""
        action = DecisionAction(type="direct_response", content="你好")
        reflection = engine.reflect(action)

        assert reflection.success is True
        assert reflection.should_retry is False

    def test_reflect_with_error(self, engine):
        """测试仅提供错误信息时的反思。"""
        action = DecisionAction(
            type="tool_call",
            tool_name="calculator",
            tool_arguments={},
            tool_call_id="call_err",
        )
        reflection = engine.reflect(action, result=None, error="网络超时")

        assert reflection.success is False
        assert reflection.should_retry is True
        assert "网络超时" in reflection.feedback

    def test_reflect_list_results(self, engine):
        """测试反思多个工具调用结果列表。"""
        action = DecisionAction(
            type="tool_call",
            tool_name="calculator",
            tool_arguments={},
            tool_call_id="call_1",
        )
        results = [
            {"tool_call_id": "call_1", "success": True, "result": 1, "error": None},
            {"tool_call_id": "call_2", "success": False, "result": None, "error": "失败"},
        ]
        reflection = engine.reflect(action, result=results)

        assert reflection.success is False
        assert reflection.should_retry is True
        assert "失败" in reflection.feedback

    def test_summarize(self, engine, mock_llm_service):
        """测试生成总结。"""
        mock_llm_service.chat_completion.return_value = _make_chat_response(
            content="这是对话总结。",
        )

        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]
        summary = engine.summarize(messages, user_id=1, session_id=1)

        assert summary == "这是对话总结。"
        mock_llm_service.chat_completion.assert_called_once()
        # 验证请求中包含总结提示词
        call_args = mock_llm_service.chat_completion.call_args
        request = call_args.args[0]
        assert isinstance(request, ChatCompletionRequest)
        # 第一条消息应为 system 角色，包含总结提示
        assert request.messages[0].role == "system"
        assert "总结" in request.messages[0].content

    def test_summarize_error(self, engine, mock_llm_service):
        """测试总结生成失败时返回错误信息。"""
        mock_llm_service.chat_completion.side_effect = RuntimeError("API 不可用")

        messages = [{"role": "user", "content": "你好"}]
        summary = engine.summarize(messages, user_id=1)

        assert "失败" in summary or "不可用" in summary

    def test_build_decision_messages(self, engine):
        """测试构建决策请求。"""
        messages = [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "你好"},
        ]
        tools = [{"type": "function", "function": {"name": "calc"}}]

        request = engine.build_decision_messages(messages, tools=tools)

        assert isinstance(request, ChatCompletionRequest)
        assert len(request.messages) == 2
        assert request.messages[0].role == "system"
        assert request.messages[0].content == "你是助手"
        assert request.messages[1].role == "user"
        assert request.messages[1].content == "你好"
        assert request.tools == tools

    def test_build_decision_messages_no_tools(self, engine):
        """测试构建不带工具的决策请求。"""
        messages = [{"role": "user", "content": "你好"}]
        request = engine.build_decision_messages(messages)

        assert isinstance(request, ChatCompletionRequest)
        assert len(request.messages) == 1
        assert request.tools is None

    def test_decide_with_error(self, engine, mock_llm_service):
        """测试 LLM 调用异常处理。"""
        mock_llm_service.chat_completion.side_effect = RuntimeError("API 不可用")

        messages = [{"role": "user", "content": "你好"}]
        result = engine.decide(messages, user_id=1, session_id=1)

        # 异常应被捕获，返回 direct_response
        assert result.action.type == "direct_response"
        assert "API 不可用" in result.action.content
        assert result.latency_ms is not None
        assert result.latency_ms >= 0
        assert result.prompt_tokens == 0
        assert result.total_tokens == 0

    def test_decide_without_tool_executor(self, engine_no_tools, mock_llm_service):
        """测试无工具执行器时的决策（请求不含工具定义）。"""
        mock_llm_service.chat_completion.return_value = _make_chat_response(
            content="直接回复",
        )

        messages = [{"role": "user", "content": "你好"}]
        result = engine_no_tools.decide(messages, user_id=1)

        assert result.action.type == "direct_response"
        assert result.action.content == "直接回复"
        # 验证请求中不包含工具
        call_args = mock_llm_service.chat_completion.call_args
        request = call_args.args[0]
        assert request.tools is None

    def test_decide_multiple_tool_calls(self, engine, mock_llm_service):
        """测试 LLM 返回多个工具调用时，action 取第一个。"""
        tool_calls = [
            _make_tool_call_dict(name="tool_a", arguments={"x": 1}, call_id="call_1"),
            _make_tool_call_dict(name="tool_b", arguments={"y": 2}, call_id="call_2"),
        ]
        mock_llm_service.chat_completion.return_value = _make_chat_response(
            content="",
            tool_calls=tool_calls,
        )

        messages = [{"role": "user", "content": "执行多个工具"}]
        result = engine.decide(messages, user_id=1)

        assert result.action.type == "tool_call"
        assert result.action.tool_name == "tool_a"
        assert result.action.tool_call_id == "call_1"
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 2


if __name__ == "__main__":
    unittest.main()

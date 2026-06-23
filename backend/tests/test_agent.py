"""Agent 引擎模块单元测试 - 使用 mock 对象，不依赖外部服务。"""
import os
import sys
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# 确保后端目录在 sys.path 中
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from src.agent.engine import AgentEngine
from src.agent.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    AgentState,
    AgentStatus,
)
from src.core.config import settings
from src.decision.schemas import DecisionAction, DecisionResult, ReflectionResult
from src.prompt.schemas import BuiltPrompt, Message


# ----------------------------- 辅助函数 -----------------------------

def _make_built_prompt(
    messages: Optional[List[Dict[str, Any]]] = None,
) -> BuiltPrompt:
    """构造模拟的 BuiltPrompt。"""
    if messages is None:
        messages = [{"role": "user", "content": "你好"}]
    msg_objects = [Message(role=m["role"], content=m["content"]) for m in messages]
    return BuiltPrompt(
        messages=msg_objects,
        token_count=10,
        is_compressed=False,
    )


def _make_direct_response_decision(
    content: str = "你好，我是助手。",
) -> DecisionResult:
    """构造直接回复的决策结果。"""
    return DecisionResult(
        action=DecisionAction(type="direct_response", content=content),
        raw_response=content,
        tool_calls=None,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )


def _make_tool_call_decision(
    tool_name: str = "calculator",
    arguments: Optional[Dict[str, Any]] = None,
) -> DecisionResult:
    """构造工具调用的决策结果。"""
    args = arguments if arguments is not None else {"expression": "1+1"}
    tool_calls = [
        {
            "id": "call_001",
            "type": "function",
            "function": {"name": tool_name, "arguments": args},
        }
    ]
    return DecisionResult(
        action=DecisionAction(
            type="tool_call",
            tool_name=tool_name,
            tool_arguments=args,
            tool_call_id="call_001",
        ),
        raw_response=None,
        tool_calls=tool_calls,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )


def _make_tool_results(success: bool = True) -> List[Dict[str, Any]]:
    """构造工具执行结果列表。"""
    return [
        {
            "tool_call_id": "call_001",
            "tool_name": "calculator",
            "arguments": {"expression": "1+1"},
            "success": success,
            "result": {"result": 2} if success else None,
            "error": None if success else "执行失败",
        }
    ]


def _make_state(session_id: int = 1, user_id: int = 1) -> AgentState:
    """构造测试用的 Agent 状态字典。"""
    return {
        "input": "测试",
        "messages": [],
        "tool_calls": [],
        "tool_results": [],
        "memory_items": [],
        "finished": False,
        "summary": "",
        "error": None,
        "user_id": user_id,
        "session_id": session_id,
        "iteration": 0,
        "max_iterations": settings.MAX_ITERATIONS,
    }


# ----------------------------- 测试夹具 -----------------------------

@pytest.fixture
def mock_db():
    """创建 mock 数据库会话。"""
    return MagicMock()


@pytest.fixture
def mock_decision_engine():
    """创建 mock DecisionEngine。"""
    return MagicMock()


@pytest.fixture
def mock_memory_system():
    """创建 mock MemorySystem。"""
    return MagicMock()


@pytest.fixture
def mock_prompt_builder():
    """创建 mock PromptBuilder。"""
    return MagicMock()


@pytest.fixture
def mock_session_manager():
    """创建 mock SessionManager。"""
    return MagicMock()


@pytest.fixture
def agent(
    mock_db,
    mock_decision_engine,
    mock_memory_system,
    mock_prompt_builder,
    mock_session_manager,
):
    """创建 AgentEngine 实例（所有依赖均为 mock）。"""
    return AgentEngine(
        db=mock_db,
        decision_engine=mock_decision_engine,
        memory_system=mock_memory_system,
        prompt_builder=mock_prompt_builder,
        session_manager=mock_session_manager,
    )


# ----------------------------- 测试用例 -----------------------------

class TestAgentRun:
    """Agent run 方法测试。"""

    async def test_agent_run_direct_response(
        self,
        agent,
        mock_prompt_builder,
        mock_decision_engine,
        mock_memory_system,
    ):
        """测试 Agent 直接回复（无工具调用）。"""
        mock_prompt_builder.build.return_value = _make_built_prompt()
        mock_decision_engine.decide.return_value = _make_direct_response_decision(
            "你好，我是助手。"
        )

        request = AgentRunRequest(message="你好", session_id=1, user_id=1)
        response = await agent.run(request)

        assert isinstance(response, AgentRunResponse)
        assert response.response == "你好，我是助手。"
        assert response.session_id == 1
        assert response.iterations == 1
        assert response.tool_calls == []
        assert response.error is None
        # 验证决策引擎被调用一次
        mock_decision_engine.decide.assert_called_once()
        # 验证记忆保存
        mock_memory_system.add.assert_called_once()
        # 验证 summarize 未被调用（直接回复不需要总结）
        mock_decision_engine.summarize.assert_not_called()

    async def test_agent_run_with_tool_call(
        self,
        agent,
        mock_prompt_builder,
        mock_decision_engine,
        mock_memory_system,
    ):
        """测试 Agent 调用工具后回复。"""
        mock_prompt_builder.build.return_value = _make_built_prompt()
        mock_decision_engine.decide.return_value = _make_tool_call_decision()
        mock_decision_engine.execute_tool_calls.return_value = _make_tool_results(
            success=True
        )
        mock_decision_engine.reflect.return_value = ReflectionResult(
            success=True,
            feedback="工具执行成功",
            should_retry=False,
        )
        mock_decision_engine.summarize.return_value = "计算结果是 2"

        request = AgentRunRequest(message="计算 1+1", session_id=1, user_id=1)
        response = await agent.run(request)

        assert isinstance(response, AgentRunResponse)
        assert response.response == "计算结果是 2"
        assert response.session_id == 1
        assert response.iterations == 1
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["tool_name"] == "calculator"
        assert response.error is None
        # 验证工具执行
        mock_decision_engine.execute_tool_calls.assert_called_once()
        # 验证反思
        mock_decision_engine.reflect.assert_called_once()
        # 验证总结生成
        mock_decision_engine.summarize.assert_called_once()
        # 验证记忆保存
        mock_memory_system.add.assert_called_once()

    async def test_agent_run_max_iterations(
        self,
        agent,
        mock_prompt_builder,
        mock_decision_engine,
    ):
        """测试达到最大迭代次数。"""
        # 设置最大迭代次数为 3
        with patch.object(settings, "MAX_ITERATIONS", 3):
            mock_prompt_builder.build.return_value = _make_built_prompt()
            mock_decision_engine.decide.return_value = _make_tool_call_decision()
            mock_decision_engine.execute_tool_calls.return_value = _make_tool_results(
                success=False
            )
            mock_decision_engine.reflect.return_value = ReflectionResult(
                success=False,
                feedback="工具执行失败",
                should_retry=True,
            )
            mock_decision_engine.summarize.return_value = "达到最大迭代次数"

            request = AgentRunRequest(message="测试", session_id=1, user_id=1)
            response = await agent.run(request)

        assert response.iterations == 3
        assert response.response == "达到最大迭代次数"
        assert response.error is None
        # decide 被调用 3 次（每次迭代一次）
        assert mock_decision_engine.decide.call_count == 3
        # summarize 在循环结束后调用一次
        mock_decision_engine.summarize.assert_called_once()

    async def test_agent_run_with_error(
        self,
        agent,
        mock_prompt_builder,
        mock_decision_engine,
    ):
        """测试处理错误情况。"""
        mock_prompt_builder.build.return_value = _make_built_prompt()
        mock_decision_engine.decide.side_effect = RuntimeError("LLM 服务不可用")

        request = AgentRunRequest(message="测试", session_id=1, user_id=1)
        response = await agent.run(request)

        assert response.error is not None
        assert "LLM 服务不可用" in response.error
        assert response.session_id == 1
        assert response.iterations == 1
        # 验证状态为 error
        status = agent.get_status(1)
        assert status.state == "error"

    async def test_agent_run_creates_new_session(
        self,
        agent,
        mock_prompt_builder,
        mock_decision_engine,
        mock_session_manager,
    ):
        """测试未提供 session_id 时创建新会话。"""
        mock_session = MagicMock()
        mock_session.id = 100
        mock_session_manager.create_session.return_value = mock_session
        mock_prompt_builder.build.return_value = _make_built_prompt()
        mock_decision_engine.decide.return_value = _make_direct_response_decision()

        request = AgentRunRequest(message="你好", session_id=None, user_id=1)
        response = await agent.run(request)

        mock_session_manager.create_session.assert_called_once()
        assert response.session_id == 100


class TestAgentState:
    """Agent 状态管理测试。"""

    def test_initialize_state_with_session(
        self, agent, mock_session_manager
    ):
        """测试初始化状态（提供 session_id）。"""
        request = AgentRunRequest(message="你好", session_id=5, user_id=2)
        state = agent._initialize_state(request)

        assert state["input"] == "你好"
        assert state["session_id"] == 5
        assert state["user_id"] == 2
        assert state["finished"] is False
        assert state["summary"] == ""
        assert state["error"] is None
        assert state["iteration"] == 0
        assert state["max_iterations"] == settings.MAX_ITERATIONS
        assert state["messages"] == []
        assert state["tool_results"] == []
        # 不应创建新会话
        mock_session_manager.create_session.assert_not_called()

    def test_initialize_state_creates_session(
        self, agent, mock_session_manager
    ):
        """测试初始化状态（未提供 session_id 时创建新会话）。"""
        mock_session = MagicMock()
        mock_session.id = 42
        mock_session_manager.create_session.return_value = mock_session

        request = AgentRunRequest(message="你好", session_id=None, user_id=1)
        state = agent._initialize_state(request)

        mock_session_manager.create_session.assert_called_once()
        assert state["session_id"] == 42
        assert state["user_id"] == 1

    def test_save_message(self, agent, mock_session_manager):
        """测试保存消息。"""
        state = _make_state(session_id=1, user_id=1)

        agent._save_message(state, "user", "你好")
        agent._save_message(state, "assistant", "你好！")

        # 验证消息追加到状态列表
        assert len(state["messages"]) == 2
        assert state["messages"][0] == {"role": "user", "content": "你好"}
        assert state["messages"][1] == {
            "role": "assistant",
            "content": "你好！",
        }
        # 验证 session_manager.add_message 被调用两次
        assert mock_session_manager.add_message.call_count == 2


class TestAgentStatus:
    """Agent 状态查询与重置测试。"""

    def test_get_status_idle(self, agent):
        """测试获取未运行会话的状态（应为 idle）。"""
        status = agent.get_status(999)

        assert isinstance(status, AgentStatus)
        assert status.state == "idle"
        assert status.iteration == 0
        assert status.max_iterations == settings.MAX_ITERATIONS
        assert status.session_id == 999
        assert status.error is None

    async def test_get_status_after_run(
        self, agent, mock_prompt_builder, mock_decision_engine
    ):
        """测试运行后获取状态（应为 finished）。"""
        mock_prompt_builder.build.return_value = _make_built_prompt()
        mock_decision_engine.decide.return_value = _make_direct_response_decision()

        request = AgentRunRequest(message="你好", session_id=1, user_id=1)
        await agent.run(request)

        status = agent.get_status(1)
        assert status.state == "finished"
        assert status.iteration == 1
        assert status.session_id == 1
        assert status.error is None

    async def test_reset(
        self, agent, mock_prompt_builder, mock_decision_engine
    ):
        """测试重置状态。"""
        mock_prompt_builder.build.return_value = _make_built_prompt()
        mock_decision_engine.decide.return_value = _make_direct_response_decision()

        request = AgentRunRequest(message="你好", session_id=1, user_id=1)
        await agent.run(request)

        # 运行后状态应为 finished
        assert agent.get_status(1).state == "finished"

        # 重置后状态应为 idle
        agent.reset(1)
        status = agent.get_status(1)
        assert status.state == "idle"
        assert status.iteration == 0


if __name__ == "__main__":
    unittest.main()

"""Agent 引擎模块 - 系统核心循环，协调决策、记忆、会话等模块完成对话。"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.agent.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    AgentState,
    AgentStatus,
)
from src.core.config import settings
from src.decision.engine import DecisionEngine
from src.memory.manager import MemorySystem
from src.monitoring.logger import Logger
from src.prompt.builder import PromptBuilder
from src.session.schemas import MessageCreate
from src.session.service import SessionManager


class AgentEngine:
    """Agent 引擎，协调各模块完成"输入-决策-工具-反思-记忆"的核心循环。

    核心循环流程：
        1. 接收输入 -> 2. 上下文管理 -> 3. 记忆检索 -> 4. 构建提示词 ->
        5. LLM 调用 -> 6. 工具调用处理 -> 7. 检查终止条件 -> 8. 保存记忆
    """

    def __init__(
        self,
        db: Session,
        decision_engine: DecisionEngine,
        memory_system: MemorySystem,
        prompt_builder: PromptBuilder,
        session_manager: SessionManager,
        workflow_orchestrator: Optional[Any] = None,
    ):
        """初始化 Agent 引擎。

        Args:
            db: 数据库会话。
            decision_engine: 决策引擎实例。
            memory_system: 记忆系统实例。
            prompt_builder: 提示词构建器实例。
            session_manager: 会话管理器实例。
            workflow_orchestrator: 工作流编排器（可选）。
        """
        self.db = db
        self.decision_engine = decision_engine
        self.memory_system = memory_system
        self.prompt_builder = prompt_builder
        self.session_manager = session_manager
        self.workflow_orchestrator = workflow_orchestrator
        self.logger = Logger()
        # 会话状态跟踪：session_id -> AgentStatus
        self._states: Dict[int, AgentStatus] = {}

    async def run(self, request: AgentRunRequest) -> AgentRunResponse:
        """完整的对话执行流程。

        Args:
            request: Agent 运行请求，包含用户消息及可选的会话/用户 ID。

        Returns:
            Agent 运行响应，包含最终回复、迭代次数及工具调用结果。
        """
        # 1. 初始化状态
        state = self._initialize_state(request)

        # 2. 保存用户消息
        self._save_message(state, "user", request.message)

        # 标记运行中
        self._update_status(state, "running")

        try:
            # 3. 主循环
            while (
                not state["finished"]
                and state["iteration"] < state["max_iterations"]
            ):
                state["iteration"] += 1

                # 3.1 构建提示词
                prompt = self.prompt_builder.build(
                    state["session_id"], state["input"], state["user_id"]
                )

                # 3.2 调用决策引擎
                decision = self.decision_engine.decide(
                    self._messages_to_dicts(prompt.messages),
                    state["user_id"],
                    state["session_id"],
                )

                # 3.3 处理决策结果
                if decision.action.type == "tool_call":
                    # 执行工具调用
                    tool_results = self.decision_engine.execute_tool_calls(
                        decision.tool_calls or [],
                        state["user_id"],
                        state["session_id"],
                    )
                    state["tool_results"].extend(tool_results)

                    # 保存工具结果消息
                    for result in tool_results:
                        self._save_message(state, "tool", str(result))

                    # 反思
                    reflection = self.decision_engine.reflect(
                        decision.action, tool_results
                    )
                    if not reflection.should_retry:
                        # 工具调用完成，生成最终回复
                        state["summary"] = self.decision_engine.summarize(
                            state["messages"],
                            state["user_id"],
                            state["session_id"],
                        )
                        state["finished"] = True

                elif decision.action.type in ("direct_response", "finished"):
                    state["summary"] = decision.action.content or ""
                    state["finished"] = True

                # 3.4 保存助手消息
                if decision.action.content:
                    self._save_message(
                        state, "assistant", decision.action.content
                    )

            # 4. 如果循环结束但未完成，生成总结
            if not state["finished"]:
                state["summary"] = self.decision_engine.summarize(
                    state["messages"],
                    state["user_id"],
                    state["session_id"],
                )
                state["finished"] = True

        except Exception as exc:
            state["error"] = str(exc)
            self.logger.error(f"Agent 运行出错: {exc}")
            self._update_status(state, "error")

        # 5. 保存记忆
        if state["summary"]:
            try:
                self.memory_system.add(
                    state["session_id"], "assistant", state["summary"]
                )
            except Exception as exc:
                self.logger.warning(f"保存记忆失败: {exc}")

        # 6. 返回结果
        if not state["error"]:
            self._update_status(state, "finished")

        return AgentRunResponse(
            response=state["summary"]
            or (f"运行出错: {state['error']}" if state["error"] else ""),
            session_id=state["session_id"],
            iterations=state["iteration"],
            tool_calls=state["tool_results"],
            error=state["error"],
        )

    def _initialize_state(self, request: AgentRunRequest) -> AgentState:
        """初始化 Agent 状态。

        若未提供 session_id，则通过会话管理器创建新会话。

        Args:
            request: Agent 运行请求。

        Returns:
            初始化后的 Agent 状态字典。
        """
        user_id = request.user_id
        session_id = request.session_id

        # 如果会话ID未提供，创建新会话
        if session_id is None:
            create_user_id = user_id if user_id is not None else 1
            session = self.session_manager.create_session(
                user_id=create_user_id,
                title=request.message[:50] if request.message else None,
            )
            session_id = session.id

        state: AgentState = {
            "input": request.message,
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
        return state

    def _save_message(self, state: AgentState, role: str, content: str) -> None:
        """保存消息到会话。

        将消息追加到状态历史列表，并持久化到数据库。

        Args:
            state: Agent 状态。
            role: 消息角色 (user/assistant/tool)。
            content: 消息内容。
        """
        # 追加到状态消息列表
        state["messages"].append({"role": role, "content": content})

        # 持久化到数据库
        try:
            self.session_manager.add_message(
                state["session_id"],
                MessageCreate(role=role, content=content),
            )
        except Exception as exc:
            self.logger.warning(f"保存消息失败: {exc}")

    @staticmethod
    def _messages_to_dicts(messages: List[Any]) -> List[Dict[str, Any]]:
        """将 Message 对象列表转为字典列表。

        兼容字典和对象两种输入形式，供决策引擎使用。

        Args:
            messages: Message 对象或字典列表。

        Returns:
            消息字典列表，每项含 role/content 键。
        """
        result: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            else:
                item: Dict[str, Any] = {
                    "role": getattr(msg, "role", "user"),
                    "content": getattr(msg, "content", ""),
                }
                tool_call = getattr(msg, "tool_call", None)
                if tool_call is not None:
                    item["tool_call"] = tool_call
                result.append(item)
        return result

    def _update_status(self, state: AgentState, status: str) -> None:
        """更新会话状态跟踪。

        Args:
            state: Agent 状态。
            status: 状态字符串 (idle/running/finished/error)。
        """
        session_id = state["session_id"]
        if session_id is None:
            return
        self._states[session_id] = AgentStatus(
            state=status,
            iteration=state["iteration"],
            max_iterations=state["max_iterations"],
            session_id=session_id,
            error=state["error"],
        )

    def get_status(self, session_id: int) -> AgentStatus:
        """获取 Agent 状态。

        Args:
            session_id: 会话 ID。

        Returns:
            当前 Agent 状态，未运行过时返回 idle 状态。
        """
        if session_id not in self._states:
            return AgentStatus(
                state="idle",
                iteration=0,
                max_iterations=settings.MAX_ITERATIONS,
                session_id=session_id,
            )
        return self._states[session_id]

    def reset(self, session_id: int) -> None:
        """重置 Agent 状态。

        清除指定会话的状态跟踪信息。

        Args:
            session_id: 会话 ID。
        """
        if session_id in self._states:
            del self._states[session_id]
        self.logger.info(f"Agent 状态已重置: session_id={session_id}")

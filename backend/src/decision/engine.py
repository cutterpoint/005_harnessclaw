"""决策引擎模块 - 负责 LLM 交互、工具调用解析与反思机制。"""
import json
import time
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.decision.schemas import (
    DecisionAction,
    DecisionResult,
    ReflectionResult,
)
from src.llm.schemas import ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from src.llm.service import LLMService
from src.monitoring.logger import Logger
from src.tools.executor import ToolExecutor


class DecisionEngine:
    """决策引擎主类，协调 LLM 调用、工具执行与反思评估。"""

    def __init__(
        self,
        llm_service: LLMService,
        prompt_builder: Optional[Any] = None,
        tool_executor: Optional[ToolExecutor] = None,
    ):
        """初始化决策引擎。

        Args:
            llm_service: LLM 服务实例，用于聊天补全调用。
            prompt_builder: 提示词构建器（可选），用于构建上下文消息。
            tool_executor: 工具执行器（可选），用于执行工具调用。
        """
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder
        self.tool_executor = tool_executor
        self.logger = Logger()

    def decide(
        self,
        messages: List[Dict],
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> DecisionResult:
        """生成决策：构建请求 -> 调用 LLM -> 解析响应 -> 返回决策结果。

        Args:
            messages: 对话消息列表，每条消息为含 role/content 的字典。
            user_id: 用户 ID。
            session_id: 会话 ID。

        Returns:
            决策结果，包含动作类型、工具调用及 Token 消耗。
        """
        start_time = time.time()

        # 获取工具定义（若配置了工具执行器）
        tools: Optional[List[Dict[str, Any]]] = None
        if self.tool_executor is not None:
            try:
                openai_tools = self.tool_executor.get_openai_tools()
                tools = openai_tools if openai_tools else None
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(f"获取工具定义失败，将以无工具模式决策: {exc}")
                tools = None

        # 构建决策请求
        request = self.build_decision_messages(messages, tools=tools)

        # 调用 LLM
        try:
            response = self.llm_service.chat_completion(
                request, user_id=user_id, session_id=session_id
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"决策引擎 LLM 调用失败: {exc}")
            return DecisionResult(
                action=DecisionAction(
                    type="direct_response",
                    content=f"LLM 调用失败: {exc}",
                ),
                raw_response=None,
                latency_ms=latency_ms,
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # 解析工具调用
        tool_calls = self.parse_tool_calls(response)

        # 构建决策动作
        if tool_calls:
            first_call = tool_calls[0]
            action = DecisionAction(
                type="tool_call",
                tool_name=first_call["function"]["name"],
                tool_arguments=first_call["function"]["arguments"],
                tool_call_id=first_call["id"],
            )
        else:
            action = DecisionAction(
                type="direct_response",
                content=response.content,
            )

        return DecisionResult(
            action=action,
            raw_response=response.content,
            tool_calls=tool_calls if tool_calls else None,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            latency_ms=latency_ms,
        )

    def parse_tool_calls(
        self, response: ChatCompletionResponse
    ) -> List[Dict[str, Any]]:
        """从 LLM 响应中解析工具调用，将 arguments JSON 字符串转为字典。

        Args:
            response: LLM 聊天补全响应。

        Returns:
            解析后的工具调用列表，每项含 id/type/function(name+arguments)。
        """
        if not response.tool_calls:
            return []

        parsed: List[Dict[str, Any]] = []
        for tc in response.tool_calls:
            func = tc.get("function", {}) if isinstance(tc, dict) else {}
            arguments_raw = func.get("arguments", "{}")
            # arguments 可能是 JSON 字符串或已解析的字典
            if isinstance(arguments_raw, str):
                try:
                    arguments = json.loads(arguments_raw)
                except (json.JSONDecodeError, ValueError):
                    arguments = {}
            else:
                arguments = arguments_raw if isinstance(arguments_raw, dict) else {}

            parsed.append(
                {
                    "id": tc.get("id"),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": func.get("name"),
                        "arguments": arguments,
                    },
                }
            )
        return parsed

    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        user_id: int,
        session_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """执行工具调用列表，收集每个工具的执行结果。

        Args:
            tool_calls: 解析后的工具调用列表。
            user_id: 触发执行的用户 ID。
            session_id: 关联的会话 ID。

        Returns:
            工具执行结果列表，每项含 tool_call_id/tool_name/arguments/success/result/error。
        """
        results: List[Dict[str, Any]] = []
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name")
            arguments = func.get("arguments", {})
            tool_call_id = tc.get("id")

            if self.tool_executor is None:
                results.append(
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "success": False,
                        "result": None,
                        "error": "工具执行器未配置",
                    }
                )
                continue

            try:
                exec_result = self.tool_executor.execute(
                    tool_name=tool_name,
                    arguments=arguments,
                    user_id=user_id,
                    session_id=session_id,
                )
                results.append(
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "success": exec_result.success,
                        "result": exec_result.result,
                        "error": exec_result.error,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "success": False,
                        "result": None,
                        "error": str(exc),
                    }
                )
        return results

    def reflect(
        self,
        action: DecisionAction,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> ReflectionResult:
        """反思评估动作执行情况，判断是否应该重试。

        - 工具执行成功 -> success=True
        - 工具执行失败 -> success=False, should_retry=True
        - 直接回复 -> success=True

        Args:
            action: 被评估的决策动作。
            result: 工具执行结果（ToolExecutionResult 或结果列表）。
            error: 执行错误信息。

        Returns:
            反思结果，包含是否成功、反馈及是否重试。
        """
        if action.type == "tool_call":
            return self._reflect_tool_call(action, result, error)
        # 直接回复或已完成动作视为成功
        return ReflectionResult(
            success=True,
            feedback="直接回复成功",
            should_retry=False,
        )

    def _reflect_tool_call(
        self,
        action: DecisionAction,
        result: Optional[Any],
        error: Optional[str],
    ) -> ReflectionResult:
        """反思工具调用动作的执行结果。"""
        # 处理列表形式的结果（来自 execute_tool_calls）
        if isinstance(result, list):
            return self._reflect_tool_call_list(action, result)

        # 处理单个 ToolExecutionResult
        if result is not None and hasattr(result, "success"):
            if result.success:
                return ReflectionResult(
                    success=True,
                    feedback="工具执行成功",
                    should_retry=False,
                )
            feedback = getattr(result, "error", None) or error or "工具执行失败"
            return ReflectionResult(
                success=False,
                feedback=feedback,
                should_retry=True,
                improved_approach=f"工具 {action.tool_name} 执行失败，建议检查参数或重试",
            )

        # 仅有错误信息
        if error is not None:
            return ReflectionResult(
                success=False,
                feedback=error,
                should_retry=True,
                improved_approach=f"工具 {action.tool_name} 执行出错: {error}",
            )

        # 无结果也无错误，默认成功
        return ReflectionResult(
            success=True,
            feedback="工具执行完成",
            should_retry=False,
        )

    def _reflect_tool_call_list(
        self, action: DecisionAction, results: List[Any]
    ) -> ReflectionResult:
        """反思多个工具调用的执行结果。"""
        all_success = True
        errors: List[str] = []
        for r in results:
            if isinstance(r, dict):
                success = r.get("success", False)
                err = r.get("error")
            else:
                success = getattr(r, "success", False)
                err = getattr(r, "error", None)
            if not success:
                all_success = False
                if err:
                    errors.append(err)

        if all_success:
            return ReflectionResult(
                success=True,
                feedback="所有工具执行成功",
                should_retry=False,
            )
        feedback = "; ".join(errors) if errors else "部分工具执行失败"
        return ReflectionResult(
            success=False,
            feedback=feedback,
            should_retry=True,
            improved_approach="部分工具执行失败，建议检查参数或重试",
        )

    def summarize(
        self,
        messages: List[Dict],
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> str:
        """生成最终总结回复：构建总结提示词 -> 调用 LLM -> 返回总结。

        Args:
            messages: 对话消息列表。
            user_id: 用户 ID。
            session_id: 会话 ID。

        Returns:
            LLM 生成的总结文本。
        """
        summary_prompt = (
            "请根据以下对话历史，生成一个简洁、连贯的最终回复总结。"
            "整合工具调用结果，给出对用户问题的完整回答。"
        )

        # 构建总结消息：系统提示 + 原始对话
        summary_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": summary_prompt}
        ]
        summary_messages.extend(messages)

        request = self.build_decision_messages(summary_messages, tools=None)

        try:
            response = self.llm_service.chat_completion(
                request, user_id=user_id, session_id=session_id
            )
            return response.content
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"决策引擎总结生成失败: {exc}")
            return f"总结生成失败: {exc}"

    def build_decision_messages(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatCompletionRequest:
        """构建决策请求，将字典消息转为 ChatMessage 列表。

        Args:
            messages: 对话消息字典列表。
            tools: OpenAI 格式工具定义列表。

        Returns:
            聊天补全请求对象。
        """
        chat_messages: List[ChatMessage] = []
        for msg in messages:
            chat_messages.append(
                ChatMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                )
            )
        return ChatCompletionRequest(
            messages=chat_messages,
            model=settings.DEFAULT_MODEL,
            tools=tools,
        )

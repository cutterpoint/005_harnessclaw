"""摘要生成器 - 基于 LLM 生成对话摘要，LLM 不可用时降级为截取。"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.context.token_counter import TokenCounter
from src.llm.schemas import ChatCompletionRequest, ChatMessage
from src.monitoring.logger import Logger

if TYPE_CHECKING:
    from src.llm.service import LLMService

logger = Logger()

# 单块摘要的最大消息数
CHUNK_SIZE = 5


class Summarizer:
    """对话摘要生成器。"""

    def __init__(self, llm_service: "Optional[LLMService]" = None) -> None:
        """初始化摘要生成器。

        Args:
            llm_service: 可选的 LLM 服务实例，未提供时降级为截取摘要。
        """
        self.llm_service = llm_service
        self.token_counter = TokenCounter()

    def summarize_chunk(
        self, chunk: List[Dict[str, Any]], max_length: int = 500
    ) -> str:
        """对一段消息块生成摘要。

        Args:
            chunk: 待摘要的消息列表。
            max_length: 摘要的最大长度（字符数或 Token 上限）。

        Returns:
            生成的摘要文本，LLM 不可用时返回截取后的原文。
        """
        if not chunk:
            return ""
        text = self._messages_to_text(chunk)
        if self.llm_service is not None:
            try:
                request = ChatCompletionRequest(
                    messages=[
                        ChatMessage(
                            role="system",
                            content=(
                                f"请将以下对话内容总结为一段不超过{max_length}字的中文摘要，"
                                "保留关键信息与上下文。"
                            ),
                        ),
                        ChatMessage(role="user", content=text),
                    ],
                    max_tokens=max_length,
                    temperature=0.3,
                )
                response = self.llm_service.chat_completion(request)
                return response.content or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"LLM 摘要生成失败，降级为截取: {exc}")
        return text[:max_length]

    def merge_summaries(self, summaries: List[str]) -> str:
        """合并多个摘要为一段连贯文本。

        Args:
            summaries: 待合并的摘要列表。

        Returns:
            合并后的摘要文本，LLM 不可用时直接拼接。
        """
        if not summaries:
            return ""
        if len(summaries) == 1:
            return summaries[0]
        if self.llm_service is not None:
            try:
                combined = "\n\n".join(summaries)
                request = ChatCompletionRequest(
                    messages=[
                        ChatMessage(
                            role="system",
                            content="请将以下多段对话摘要合并为一段连贯、简洁的中文摘要。",
                        ),
                        ChatMessage(role="user", content=combined),
                    ],
                    temperature=0.3,
                )
                response = self.llm_service.chat_completion(request)
                return response.content or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"摘要合并失败，降级为拼接: {exc}")
        return "\n\n".join(summaries)

    def generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """生成完整对话摘要。

        消息数量较少时直接摘要；较多时分块摘要再合并。

        Args:
            messages: 完整对话消息列表。

        Returns:
            对话摘要文本。
        """
        if not messages:
            return ""
        if len(messages) <= CHUNK_SIZE:
            return self.summarize_chunk(messages)
        chunks = [
            messages[i : i + CHUNK_SIZE]
            for i in range(0, len(messages), CHUNK_SIZE)
        ]
        summaries = [self.summarize_chunk(chunk) for chunk in chunks]
        return self.merge_summaries(summaries)

    @staticmethod
    def _messages_to_text(messages: List[Dict[str, Any]]) -> str:
        """将消息列表转换为可读文本。"""
        lines: List[str] = []
        for msg in messages:
            role = (
                msg.get("role", "unknown")
                if isinstance(msg, dict)
                else getattr(msg, "role", "unknown")
            )
            content = (
                msg.get("content", "")
                if isinstance(msg, dict)
                else getattr(msg, "content", "")
            )
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

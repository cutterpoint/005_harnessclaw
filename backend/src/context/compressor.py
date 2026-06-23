"""上下文压缩器 - 通过摘要与裁剪控制对话 Token 数量。"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from src.context.schemas import CompressionConfig, CompressionResult
from src.context.summarizer import Summarizer
from src.context.token_counter import TokenCounter
from src.monitoring.logger import Logger

if TYPE_CHECKING:
    from src.llm.service import LLMService

logger = Logger()


class ContextCompressor:
    """上下文压缩器，支持摘要、裁剪、混合三种压缩策略。"""

    def __init__(
        self,
        llm_service: "Optional[LLMService]" = None,
        config: Optional[CompressionConfig] = None,
    ) -> None:
        """初始化上下文压缩器。

        Args:
            llm_service: 可选的 LLM 服务实例，用于生成摘要；不可用时降级为裁剪。
            config: 压缩配置，未提供时使用默认配置。
        """
        self.llm_service = llm_service
        self.config = config or CompressionConfig()
        self.token_counter = TokenCounter()
        self.summarizer = Summarizer(llm_service)

    def compress(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
    ) -> CompressionResult:
        """压缩上下文，确保 Token 数量在限制范围内。

        Args:
            messages: 待压缩的消息列表。
            max_tokens: 最大 Token 限制，未指定时使用配置中的值。

        Returns:
            压缩结果，包含压缩后的消息与统计信息。
        """
        limit = max_tokens if max_tokens is not None else self.config.max_tokens
        original_count = self.token_counter.count_messages(messages)

        # 未超限直接返回
        if original_count <= limit:
            return CompressionResult(
                messages=list(messages),
                original_token_count=original_count,
                compressed_token_count=original_count,
                compression_ratio=1.0,
                method="none",
            )

        strategy = self.config.compression_strategy
        if strategy == "trim":
            compressed = self.trim(messages, limit)
            method = "trim"
        elif strategy == "summary":
            compressed = self.summarize(messages)
            method = "summary"
        else:  # hybrid
            return self.hybrid_compress(messages, limit)

        compressed_count = self.token_counter.count_messages(compressed)
        ratio = (
            round(compressed_count / original_count, 4) if original_count else 0.0
        )
        logger.info(
            f"上下文压缩: strategy={method} original={original_count} "
            f"compressed={compressed_count} ratio={ratio}"
        )
        return CompressionResult(
            messages=compressed,
            original_token_count=original_count,
            compressed_token_count=compressed_count,
            compression_ratio=ratio,
            method=method,
        )

    def summarize(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """摘要压缩策略：将消息合并生成摘要，替换为一条 system 消息。

        Args:
            messages: 待压缩的消息列表。

        Returns:
            包含摘要的 system 消息列表。
        """
        if not messages:
            return []
        summary = self.summarizer.generate_summary(messages)
        return [{"role": "system", "content": f"之前的对话摘要: {summary}"}]

    def trim(
        self, messages: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """智能裁剪策略：保留最新消息，直到 Token 数在限制内。

        Args:
            messages: 待裁剪的消息列表。
            max_tokens: 最大 Token 限制。

        Returns:
            裁剪后的消息列表，至少保留 min_messages 条最新消息。
        """
        if not messages:
            return []
        kept: List[Dict[str, Any]] = []
        total = 0
        # 从最新消息开始向前累加
        for msg in reversed(messages):
            msg_tokens = self.token_counter.count_messages([msg])
            if (
                total + msg_tokens > max_tokens
                and len(kept) >= self.config.min_messages
            ):
                break
            kept.append(msg)
            total += msg_tokens
        kept.reverse()
        return kept

    def hybrid_compress(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
    ) -> CompressionResult:
        """混合压缩策略：先对旧消息生成摘要，若仍超限则裁剪。

        Args:
            messages: 待压缩的消息列表。
            max_tokens: 最大 Token 限制。

        Returns:
            压缩结果。
        """
        original_count = self.token_counter.count_messages(messages)
        if original_count <= max_tokens:
            return CompressionResult(
                messages=list(messages),
                original_token_count=original_count,
                compressed_token_count=original_count,
                compression_ratio=1.0,
                method="hybrid",
            )

        total = len(messages)
        # 保留最近的消息，对较早的消息生成摘要
        recent_count = max(
            self.config.min_messages, int(total * self.config.summary_ratio)
        )
        recent_count = min(recent_count, total)
        summarize_count = total - recent_count

        if summarize_count > 0:
            old_messages = messages[:summarize_count]
            recent_messages = messages[summarize_count:]
            summary = self.summarizer.generate_summary(old_messages)
            summary_msg = {
                "role": "system",
                "content": f"之前的对话摘要: {summary}",
            }
            combined: List[Dict[str, Any]] = [summary_msg] + recent_messages
        else:
            combined = list(messages)

        # 仍超限则裁剪
        if self.token_counter.count_messages(combined) > max_tokens:
            combined = self.trim(combined, max_tokens)

        compressed_count = self.token_counter.count_messages(combined)
        ratio = (
            round(compressed_count / original_count, 4) if original_count else 0.0
        )
        logger.info(
            f"上下文压缩: strategy=hybrid original={original_count} "
            f"compressed={compressed_count} ratio={ratio}"
        )
        return CompressionResult(
            messages=combined,
            original_token_count=original_count,
            compressed_token_count=compressed_count,
            compression_ratio=ratio,
            method="hybrid",
        )

    def check_and_compress(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """检查并压缩上下文。

        Args:
            messages: 待检查的消息列表。

        Returns:
            元组 (是否执行了压缩, 压缩后的消息列表)。
        """
        original_count = self.token_counter.count_messages(messages)
        if original_count <= self.config.max_tokens:
            return (False, list(messages))
        result = self.compress(messages)
        return (True, result.messages)

"""Token 计数器 - 优先使用 tiktoken，不可用时降级为字符数估算。"""
from typing import Any, Dict, List

from src.monitoring.logger import Logger

logger = Logger()


class TokenCounter:
    """文本与消息列表的 Token 计数器。"""

    # 每条消息的固定开销（近似 OpenAI 计费规则）
    PER_MESSAGE_OVERHEAD = 4

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """初始化 Token 计数器。

        尝试加载 tiktoken 编码器，失败则降级为字符数估算模式。
        """
        self._encoding = None
        try:
            import tiktoken  # type: ignore

            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"tiktoken 不可用，降级为字符数估算: {exc}")
            self._encoding = None

    def count(self, text: str) -> int:
        """计算文本的 Token 数量。

        tiktoken 可用时使用精确编码计数，否则使用字符数/4 估算。
        """
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return len(text) // 4

    def estimate(self, text: str) -> int:
        """快速估算文本的 Token 数量（始终使用字符数/4）。"""
        if not text:
            return 0
        return len(text) // 4

    def count_messages(self, messages: List[Dict[str, Any]]) -> int:
        """计算消息列表的 Token 数量。

        每条消息按固定开销加上 role 与 content 的 Token 数累加。
        """
        total = 0
        for msg in messages:
            total += self.PER_MESSAGE_OVERHEAD
            role = (
                msg.get("role", "")
                if isinstance(msg, dict)
                else getattr(msg, "role", "")
            )
            content = (
                msg.get("content", "")
                if isinstance(msg, dict)
                else getattr(msg, "content", "")
            )
            if role:
                total += self.count(str(role))
            if content:
                total += self.count(str(content))
        return total

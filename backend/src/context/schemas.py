"""上下文压缩模块数据模型定义。"""
from typing import Any, Dict, List

from pydantic import BaseModel


class CompressionConfig(BaseModel):
    """上下文压缩配置。

    Attributes:
        max_tokens: 允许的最大 Token 数量。
        compression_strategy: 压缩策略，可选 summary/trim/hybrid。
        summary_ratio: 摘要保留比例，用于混合策略中确定保留的最近消息占比。
        min_messages: 压缩后保留的最少消息数量。
    """

    max_tokens: int = 8192
    compression_strategy: str = "hybrid"  # summary/trim/hybrid
    summary_ratio: float = 0.3
    min_messages: int = 3


class CompressionResult(BaseModel):
    """上下文压缩结果。

    Attributes:
        messages: 压缩后的消息列表。
        original_token_count: 压缩前的 Token 数量。
        compressed_token_count: 压缩后的 Token 数量。
        compression_ratio: 压缩比（压缩后/压缩前）。
        method: 实际使用的压缩方法 summary/trim/hybrid/none。
    """

    messages: List[Dict[str, Any]]
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    method: str  # summary/trim/hybrid/none

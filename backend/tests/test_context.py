"""上下文压缩模块单元测试 - 使用 mock LLM，不依赖外部服务。"""
import os
import sys
import unittest
from unittest.mock import MagicMock

import pytest

# 确保后端目录在 sys.path 中
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from src.context import ContextCompressor, Summarizer, TokenCounter
from src.context.schemas import CompressionConfig, CompressionResult


# ----------------------------- TokenCounter 测试 -----------------------------
class TestTokenCounter:
    """Token 计数器测试。"""

    def test_token_counter_count(self):
        """测试文本 Token 计数。"""
        counter = TokenCounter()

        # 空文本返回 0
        assert counter.count("") == 0

        # 非空文本返回正整数
        assert counter.count("hello world") > 0

        # 更长的文本应具有更多 Token
        assert counter.count("a" * 100) > counter.count("a" * 10)

        # estimate 始终使用字符数/4 估算
        text = "hello world"
        assert counter.estimate(text) == len(text) // 4

    def test_token_counter_messages(self):
        """测试消息列表 Token 计数。"""
        counter = TokenCounter()

        # 空列表返回 0
        assert counter.count_messages([]) == 0

        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I am fine, thank you!"},
        ]
        count = counter.count_messages(messages)
        assert count > 0

        # 增加消息应增加 Token 数
        more = messages + [{"role": "user", "content": "Great!"}]
        assert counter.count_messages(more) > count

        # 单条消息计数应小于多条消息计数
        single = counter.count_messages([messages[0]])
        assert single < count


# ----------------------------- 压缩器测试 -----------------------------
class TestContextCompressor:
    """上下文压缩器测试。"""

    def test_compress_no_need(self):
        """测试未超限时不需要压缩。"""
        compressor = ContextCompressor(
            config=CompressionConfig(max_tokens=10000)
        )
        messages = [{"role": "user", "content": "hi"}]

        result = compressor.compress(messages)

        assert result.method == "none"
        assert result.original_token_count == result.compressed_token_count
        assert result.compression_ratio == 1.0
        assert result.messages == messages

    def test_compress_trim(self):
        """测试裁剪压缩策略。"""
        config = CompressionConfig(
            max_tokens=120, compression_strategy="trim", min_messages=1
        )
        compressor = ContextCompressor(config=config)
        messages = [
            {"role": "user", "content": "x" * 200},
            {"role": "assistant", "content": "y" * 200},
            {"role": "user", "content": "z" * 200},
        ]

        result = compressor.compress(messages)

        assert result.method == "trim"
        assert result.original_token_count > result.compressed_token_count
        assert result.compressed_token_count <= 120
        # 裁剪后消息数应减少
        assert len(result.messages) < len(messages)
        # 应保留最新的消息
        assert result.messages[-1]["content"] == "z" * 200

    def test_compress_summary(self):
        """测试摘要压缩策略（mock LLM）。"""
        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = MagicMock(content="这是对话摘要")

        config = CompressionConfig(
            max_tokens=50, compression_strategy="summary"
        )
        compressor = ContextCompressor(llm_service=mock_llm, config=config)
        messages = [
            {"role": "user", "content": "x" * 200},
            {"role": "assistant", "content": "y" * 200},
        ]

        result = compressor.compress(messages)

        assert result.method == "summary"
        assert result.original_token_count > result.compressed_token_count
        # 应包含 system 摘要消息
        assert any(m["role"] == "system" for m in result.messages)
        # LLM 应被调用
        assert mock_llm.chat_completion.called

    def test_compress_hybrid(self):
        """测试混合压缩策略（mock LLM）。"""
        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = MagicMock(content="旧消息摘要")

        config = CompressionConfig(
            max_tokens=100,
            compression_strategy="hybrid",
            min_messages=1,
            summary_ratio=0.3,
        )
        compressor = ContextCompressor(llm_service=mock_llm, config=config)
        messages = [
            {"role": "user", "content": "x" * 200},
            {"role": "assistant", "content": "y" * 200},
            {"role": "user", "content": "z" * 200},
        ]

        result = compressor.compress(messages)

        assert result.method == "hybrid"
        assert result.original_token_count > result.compressed_token_count
        assert result.compressed_token_count <= 100
        # 应包含 system 摘要消息
        assert any(m["role"] == "system" for m in result.messages)
        # 应保留最新的消息
        assert result.messages[-1]["content"] == "z" * 200
        # LLM 应被调用以生成旧消息摘要
        assert mock_llm.chat_completion.called

    def test_check_and_compress(self):
        """测试检查并压缩功能。"""
        # 未超限：不压缩
        compressor = ContextCompressor(
            config=CompressionConfig(max_tokens=10000)
        )
        messages = [{"role": "user", "content": "hi"}]
        compressed_flag, result_messages = compressor.check_and_compress(messages)
        assert compressed_flag is False
        assert result_messages == messages

        # 超限：执行裁剪压缩
        config = CompressionConfig(
            max_tokens=50, compression_strategy="trim", min_messages=1
        )
        compressor2 = ContextCompressor(config=config)
        big_messages = [
            {"role": "user", "content": "x" * 200} for _ in range(3)
        ]
        compressed_flag2, result_messages2 = compressor2.check_and_compress(
            big_messages
        )
        assert compressed_flag2 is True
        assert len(result_messages2) < len(big_messages)


# ----------------------------- 摘要生成器测试 -----------------------------
class TestSummarizer:
    """摘要生成器测试。"""

    def test_summarizer_merge(self):
        """测试摘要合并（无 LLM 时降级为拼接）。"""
        summarizer = Summarizer()

        # 空列表
        assert summarizer.merge_summaries([]) == ""

        # 单个摘要直接返回
        assert summarizer.merge_summaries(["唯一摘要"]) == "唯一摘要"

        # 多个摘要拼接（无 LLM 降级）
        summaries = ["摘要一", "摘要二", "摘要三"]
        merged = summarizer.merge_summaries(summaries)
        assert "摘要一" in merged
        assert "摘要二" in merged
        assert "摘要三" in merged

    def test_summarizer_merge_with_llm(self):
        """测试使用 mock LLM 合并摘要。"""
        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = MagicMock(content="合并后的摘要")
        summarizer = Summarizer(llm_service=mock_llm)

        merged = summarizer.merge_summaries(["摘要一", "摘要二"])
        assert merged == "合并后的摘要"
        assert mock_llm.chat_completion.called


# ----------------------------- 压缩结果模型测试 -----------------------------
class TestCompressionResult:
    """压缩结果数据模型测试。"""

    def test_compression_result(self):
        """测试压缩结果字段验证。"""
        result = CompressionResult(
            messages=[{"role": "system", "content": "摘要"}],
            original_token_count=100,
            compressed_token_count=25,
            compression_ratio=0.25,
            method="summary",
        )
        assert result.original_token_count == 100
        assert result.compressed_token_count == 25
        assert result.compression_ratio == 0.25
        assert result.method == "summary"
        assert len(result.messages) == 1
        assert result.messages[0]["role"] == "system"

    def test_compression_config_defaults(self):
        """测试压缩配置默认值。"""
        config = CompressionConfig()
        assert config.max_tokens == 8192
        assert config.compression_strategy == "hybrid"
        assert config.summary_ratio == 0.3
        assert config.min_messages == 3


if __name__ == "__main__":
    unittest.main()

"""LLM 模块单元测试 - 使用 mock 测试，不实际调用 OpenAI API。"""
import json
import os
import sys
import unittest
from typing import Any, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# 确保后端目录在 sys.path 中
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db.models import LLMConfig, LLMLog, User
from src.llm.schemas import (
    ChatCompletionRequest,
    ChatMessage,
    LLMConfigCreate,
    LLMConfigUpdate,
)
from src.llm.service import LLMService


# ----------------------------- 测试夹具 -----------------------------
def _build_in_memory_db():
    """构建内存数据库并创建所有表。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session():
    """每个测试用例独立的数据库会话。"""
    engine = _build_in_memory_db()
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_user(db_session) -> User:
    """创建测试用户。"""
    user = User(
        username="tester",
        email="tester@example.com",
        hashed_password="fake-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_config_create(
    name: str = "default",
    model_name: str = "gpt-4o-mini",
) -> LLMConfigCreate:
    """构造 LLMConfigCreate 实例。"""
    return LLMConfigCreate(
        name=name,
        api_key="sk-test-key",
        api_base="https://api.openai.com/v1",
        model_name=model_name,
        max_tokens=2048,
        temperature=0.5,
    )


def _make_mock_openai_response(
    content: str = "你好，我是助手。",
    tool_calls: Optional[List[Any]] = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
) -> MagicMock:
    """构造模拟的 OpenAI ChatCompletion 响应对象。"""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    response = MagicMock()
    response.id = "chatcmpl-test-123"
    response.choices = [choice]
    response.usage = usage
    return response


# ----------------------------- 配置管理测试 -----------------------------
class TestLLMConfig:
    """LLM 配置管理相关测试。"""

    def test_create_config(self, db_session, test_user):
        """测试创建 LLM 配置。"""
        service = LLMService(db_session)
        config_create = _make_config_create(name="my-config")

        created = service.create_config(config_create, user_id=test_user.id)

        assert created.id is not None
        assert created.name == "my-config"
        assert created.user_id == test_user.id
        assert created.api_key == "sk-test-key"
        assert created.model_name == "gpt-4o-mini"
        assert created.max_tokens == 2048
        assert created.temperature == 0.5
        assert created.is_active is False

        # 数据库中确实存在
        db_entry = db_session.query(LLMConfig).filter(
            LLMConfig.id == created.id
        ).first()
        assert db_entry is not None
        assert db_entry.name == "my-config"

    def test_get_configs(self, db_session, test_user):
        """测试获取用户配置列表。"""
        service = LLMService(db_session)
        # 创建 3 个配置
        for i in range(3):
            service.create_config(
                _make_config_create(name=f"config-{i}"),
                user_id=test_user.id,
            )

        configs = service.get_configs(user_id=test_user.id)
        assert len(configs) == 3
        # 验证只返回当前用户的配置
        for cfg in configs:
            assert cfg.user_id == test_user.id

    def test_activate_config(self, db_session, test_user):
        """测试激活配置 - 同一用户只能有一个激活配置。"""
        service = LLMService(db_session)
        cfg1 = service.create_config(
            _make_config_create(name="cfg1"), user_id=test_user.id
        )
        cfg2 = service.create_config(
            _make_config_create(name="cfg2"), user_id=test_user.id
        )

        # 激活 cfg1
        activated1 = service.activate_config(cfg1.id, user_id=test_user.id)
        assert activated1 is not None
        assert activated1.is_active is True

        # 激活 cfg2，cfg1 应被取消激活
        activated2 = service.activate_config(cfg2.id, user_id=test_user.id)
        assert activated2 is not None
        assert activated2.is_active is True

        db_session.refresh(cfg1)
        assert cfg1.is_active is False

        # 数据库中只有一个激活配置
        active_count = (
            db_session.query(LLMConfig)
            .filter(
                LLMConfig.user_id == test_user.id,
                LLMConfig.is_active == True,  # noqa: E712
            )
            .count()
        )
        assert active_count == 1

    def test_update_config(self, db_session, test_user):
        """测试更新配置。"""
        service = LLMService(db_session)
        created = service.create_config(
            _make_config_create(name="origin"), user_id=test_user.id
        )

        update_data = LLMConfigUpdate(
            name="updated-name",
            temperature=0.1,
            max_tokens=8192,
        )
        updated = service.update_config(created.id, update_data)

        assert updated is not None
        assert updated.name == "updated-name"
        assert updated.temperature == 0.1
        assert updated.max_tokens == 8192
        # 未更新的字段保持原值
        assert updated.api_key == "sk-test-key"
        assert updated.model_name == "gpt-4o-mini"

    def test_update_config_not_found(self, db_session, test_user):
        """测试更新不存在的配置返回 None。"""
        service = LLMService(db_session)
        result = service.update_config(9999, LLMConfigUpdate(name="x"))
        assert result is None

    def test_delete_config(self, db_session, test_user):
        """测试删除配置。"""
        service = LLMService(db_session)
        created = service.create_config(
            _make_config_create(name="to-delete"), user_id=test_user.id
        )

        deleted = service.delete_config(created.id)
        assert deleted is True

        # 数据库中已不存在
        assert service.get_config(created.id) is None

    def test_delete_config_not_found(self, db_session, test_user):
        """测试删除不存在的配置返回 False。"""
        service = LLMService(db_session)
        assert service.delete_config(9999) is False

    def test_get_config(self, db_session, test_user):
        """测试获取单个配置。"""
        service = LLMService(db_session)
        created = service.create_config(
            _make_config_create(name="single"), user_id=test_user.id
        )

        fetched = service.get_config(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "single"

    def test_activate_config_user_mismatch(self, db_session, test_user):
        """测试激活其他用户的配置返回 None。"""
        service = LLMService(db_session)
        # 创建另一个用户
        other_user = User(
            username="other",
            email="other@example.com",
            hashed_password="fake-hash",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        cfg = service.create_config(
            _make_config_create(name="cfg"), user_id=other_user.id
        )
        # test_user 试图激活 other_user 的配置
        result = service.activate_config(cfg.id, user_id=test_user.id)
        assert result is None


# ----------------------------- 聊天补全测试 -----------------------------
class TestChatCompletion:
    """聊天补全相关测试，使用 mock 不实际调用 API。"""

    def _setup_service_with_mock_client(
        self, db_session, test_user, response: MagicMock
    ) -> LLMService:
        """构造使用 mock OpenAI 客户端的 LLMService。"""
        # 先创建并激活一个配置
        service = LLMService(db_session)
        cfg = service.create_config(
            _make_config_create(name="active", model_name="gpt-4o-mini"),
            user_id=test_user.id,
        )
        service.activate_config(cfg.id, user_id=test_user.id)

        # 替换内部 client 为 mock
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = response
        service.client = mock_client
        return service

    def test_chat_completion_mock(self, db_session, test_user):
        """使用 mock 测试聊天补全。"""
        mock_response = _make_mock_openai_response(
            content="你好！",
            prompt_tokens=15,
            completion_tokens=25,
        )
        service = self._setup_service_with_mock_client(
            db_session, test_user, mock_response
        )

        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="你好")],
            model="gpt-4o-mini",
        )
        result = service.chat_completion(
            request, user_id=test_user.id, session_id=None
        )

        assert result.id == "chatcmpl-test-123"
        assert result.model == "gpt-4o-mini"
        assert result.content == "你好！"
        assert result.prompt_tokens == 15
        assert result.completion_tokens == 25
        assert result.total_tokens == 40
        assert result.tool_calls is None

        # 验证 OpenAI 客户端被调用一次
        service.client.chat.completions.create.assert_called_once()
        call_kwargs = service.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["messages"] == [
            {"role": "user", "content": "你好"}
        ]

    def test_chat_completion_with_tools(self, db_session, test_user):
        """测试带工具调用的聊天补全。"""
        # 构造带 tool_calls 的响应
        tool_call = MagicMock()
        tool_call.id = "call_abc"
        tool_call.type = "function"
        tool_call.function.name = "get_weather"
        tool_call.function.arguments = '{"city": "北京"}'

        mock_response = _make_mock_openai_response(
            content="",
            tool_calls=[tool_call],
            prompt_tokens=20,
            completion_tokens=10,
        )
        service = self._setup_service_with_mock_client(
            db_session, test_user, mock_response
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取天气",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="北京天气")],
            tools=tools,
        )
        result = service.chat_completion(
            request, user_id=test_user.id, session_id=None
        )

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["id"] == "call_abc"
        assert result.tool_calls[0]["function"]["name"] == "get_weather"
        assert (
            json.loads(result.tool_calls[0]["function"]["arguments"])["city"]
            == "北京"
        )

        # 验证 tools 参数被传递
        call_kwargs = service.client.chat.completions.create.call_args.kwargs
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == tools

    def test_chat_completion_retry(self, db_session, test_user):
        """测试请求失败时的重试机制。"""
        mock_response = _make_mock_openai_response(content="ok")
        service = self._setup_service_with_mock_client(
            db_session, test_user, mock_response
        )

        # 前两次抛异常，第三次成功
        service.client.chat.completions.create.side_effect = [
            RuntimeError("timeout"),
            RuntimeError("timeout"),
            mock_response,
        ]

        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")]
        )
        result = service.chat_completion(
            request, user_id=test_user.id, session_id=None
        )
        assert result.content == "ok"
        assert service.client.chat.completions.create.call_count == 3

    def test_chat_completion_all_retries_failed(self, db_session, test_user):
        """测试全部重试失败后抛出异常并记录失败日志。"""
        mock_response = _make_mock_openai_response(content="ok")
        service = self._setup_service_with_mock_client(
            db_session, test_user, mock_response
        )
        service.client.chat.completions.create.side_effect = RuntimeError(
            "service unavailable"
        )

        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")]
        )
        with pytest.raises(RuntimeError):
            service.chat_completion(
                request, user_id=test_user.id, session_id=None
            )

        # 验证调用次数等于最大重试次数
        assert (
            service.client.chat.completions.create.call_count
            == LLMService.MAX_RETRIES
        )

        # 验证失败日志被记录
        logs = db_session.query(LLMLog).all()
        assert len(logs) == 1
        assert logs[0].success is False
        assert "service unavailable" in logs[0].error_message


# ----------------------------- 日志记录测试 -----------------------------
class TestLLMLogRecording:
    """LLM 日志记录相关测试。"""

    def test_llm_log_recording(self, db_session, test_user):
        """验证 LLM 调用后日志被正确记录（含 Token 消耗和费用）。"""
        mock_response = _make_mock_openai_response(
            content="回复内容",
            prompt_tokens=100,
            completion_tokens=50,
        )
        # 创建并激活配置
        service = LLMService(db_session)
        cfg = service.create_config(
            _make_config_create(name="active", model_name="gpt-4o"),
            user_id=test_user.id,
        )
        service.activate_config(cfg.id, user_id=test_user.id)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        service.client = mock_client

        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="测试")],
            model="gpt-4o",
        )
        service.chat_completion(
            request, user_id=test_user.id, session_id=None
        )

        # 验证 LLMLog 表中存在记录
        logs = db_session.query(LLMLog).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.user_id == test_user.id
        assert log.model_name == "gpt-4o"
        assert log.prompt_tokens == 100
        assert log.completion_tokens == 50
        assert log.total_tokens == 150
        assert log.success is True
        assert log.response_content == "回复内容"
        assert log.cost_usd is not None
        # gpt-4o 费用: 100/1000 * 0.0025 + 50/1000 * 0.01 = 0.00025 + 0.0005 = 0.00075
        assert log.cost_usd == pytest.approx(0.00075, rel=1e-6)
        # 验证请求消息被记录
        request_messages = json.loads(log.request_messages)
        assert request_messages == [
            {"role": "user", "content": "测试"}
        ]

    def test_llm_log_recording_failure(self, db_session, test_user):
        """验证 LLM 调用失败时也会记录日志。"""
        service = LLMService(db_session)
        cfg = service.create_config(
            _make_config_create(name="active", model_name="gpt-4o-mini"),
            user_id=test_user.id,
        )
        service.activate_config(cfg.id, user_id=test_user.id)

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError(
            "api error"
        )
        service.client = mock_client

        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")]
        )
        with pytest.raises(RuntimeError):
            service.chat_completion(
                request, user_id=test_user.id, session_id=None
            )

        logs = db_session.query(LLMLog).all()
        assert len(logs) == 1
        assert logs[0].success is False
        assert logs[0].prompt_tokens == 0
        assert logs[0].completion_tokens == 0
        assert "api error" in logs[0].error_message


# ----------------------------- 流式与模型列表测试 -----------------------------
class TestStreamAndModels:
    """流式补全与模型列表测试。"""

    def test_stream_chat_completion(self, db_session, test_user):
        """测试流式聊天补全。"""
        # 构造模拟的流式响应块
        def make_chunk(content: Optional[str]) -> MagicMock:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta = MagicMock()
            chunk.choices[0].delta.content = content
            return chunk

        chunks = [make_chunk("你"), make_chunk("好"), make_chunk("！"), make_chunk(None)]

        service = LLMService(db_session)
        cfg = service.create_config(
            _make_config_create(name="active"), user_id=test_user.id
        )
        service.activate_config(cfg.id, user_id=test_user.id)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter(chunks)
        service.client = mock_client

        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")],
            stream=True,
        )
        collected = list(
            service.stream_chat_completion(
                request, user_id=test_user.id, session_id=None
            )
        )
        assert collected == ["你", "好", "！"]

        # 验证流式调用时传入了 stream=True
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["stream"] is True

        # 验证日志被记录
        logs = db_session.query(LLMLog).all()
        assert len(logs) == 1
        assert logs[0].success is True
        assert logs[0].response_content == "你好！"

    def test_get_models(self, db_session, test_user):
        """测试获取可用模型列表。"""
        service = LLMService(db_session)
        cfg = service.create_config(
            _make_config_create(name="active"), user_id=test_user.id
        )
        service.activate_config(cfg.id, user_id=test_user.id)

        # 替换为 mock 客户端
        mock_client = MagicMock()
        service.client = mock_client

        # mock models.list()
        model1 = MagicMock()
        model1.id = "gpt-4o"
        model1.created = 1700000000
        model1.owned_by = "openai"
        model2 = MagicMock()
        model2.id = "gpt-4o-mini"
        model2.created = 1700000001
        model2.owned_by = "openai"

        models_list = MagicMock()
        models_list.data = [model1, model2]
        mock_client.models.list.return_value = models_list

        models = service.get_models()
        assert len(models) == 2
        assert models[0]["id"] == "gpt-4o"
        assert models[1]["id"] == "gpt-4o-mini"

    def test_get_models_fallback(self, db_session, test_user):
        """测试获取模型列表失败时返回默认模型。"""
        service = LLMService(db_session)
        cfg = service.create_config(
            _make_config_create(name="active", model_name="gpt-4o-mini"),
            user_id=test_user.id,
        )
        service.activate_config(cfg.id, user_id=test_user.id)

        # 替换为 mock 客户端
        mock_client = MagicMock()
        service.client = mock_client
        mock_client.models.list.side_effect = RuntimeError("network error")

        models = service.get_models()
        assert len(models) == 1
        assert models[0]["id"] == "gpt-4o-mini"


if __name__ == "__main__":
    unittest.main()

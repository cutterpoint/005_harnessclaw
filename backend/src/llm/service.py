"""LLM 服务模块 - 封装 OpenAI 兼容 API 调用、配置管理和日志记录。"""
import json
import time
from typing import Any, Dict, Iterator, List, Optional

from openai import OpenAI
from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.models import LLMConfig
from src.llm.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    LLMConfigCreate,
    LLMConfigUpdate,
)
from src.monitoring.logger import Logger


class LLMService:
    """LLM 服务主类，提供聊天补全、配置管理等功能。"""

    # 重试相关常量
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # 初始退避秒数

    def __init__(self, db: Session):
        """初始化 LLM 服务，从数据库加载激活的配置。"""
        self.db = db
        self.logger = Logger(db=db)
        self._config: Optional[LLMConfig] = self._load_active_config()
        self.client: Optional[OpenAI] = None
        if self._config is not None:
            self.client = self._build_client(self._config)

    # ---- 内部辅助方法 ----
    def _load_active_config(self) -> Optional[LLMConfig]:
        """从数据库加载当前激活的 LLM 配置。"""
        if self.db is None:
            return None
        return (
            self.db.query(LLMConfig)
            .filter(LLMConfig.is_active == True)  # noqa: E712
            .order_by(LLMConfig.id.desc())
            .first()
        )

    def _build_client(self, config: LLMConfig) -> OpenAI:
        """根据配置构建 OpenAI 客户端。"""
        return OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def _get_default_client(self) -> OpenAI:
        """使用 settings 默认配置构建客户端。"""
        return OpenAI(
            api_key=settings.OPENAI_API_KEY or "missing-api-key",
            base_url=settings.OPENAI_API_BASE,
        )

    def _get_active_client_and_model(self) -> tuple[OpenAI, str, Optional[LLMConfig]]:
        """获取当前可用的客户端、模型名以及配置对象。

        若数据库存在激活配置则使用之，否则回退到 settings 默认配置。
        """
        if self._config is not None and self.client is not None:
            return self.client, self._config.model_name, self._config
        return self._get_default_client(), settings.DEFAULT_MODEL, None

    def _messages_to_dicts(
        self, messages: List[Any]
    ) -> List[Dict[str, Any]]:
        """将 ChatMessage 列表转换为字典列表。"""
        result: List[Dict[str, Any]] = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                result.append(msg.model_dump())
            elif isinstance(msg, dict):
                result.append(msg)
            else:
                result.append({"role": msg.role, "content": msg.content})
        return result

    def _call_with_retry(
        self, client: OpenAI, **kwargs: Any
    ) -> Any:
        """带重试的 OpenAI 调用，最多重试 3 次，指数退避。"""
        last_error: Optional[Exception] = None
        backoff = self.INITIAL_BACKOFF
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise
        # 理论不可达
        raise last_error  # type: ignore[misc]

    # ---- 聊天补全 ----
    def chat_completion(
        self,
        request: ChatCompletionRequest,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> ChatCompletionResponse:
        """调用 OpenAI 兼容 API 完成聊天补全，并记录 LLM 日志。"""
        client, default_model, config = self._get_active_client_and_model()
        model_name = request.model or default_model
        max_tokens = request.max_tokens or (
            config.max_tokens if config else 4096
        )
        temperature = request.temperature if request.temperature is not None else (
            config.temperature if config is not None else 0.7
        )

        messages_dicts = self._messages_to_dicts(request.messages)
        request_payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages_dicts,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if request.tools:
            request_payload["tools"] = request.tools

        request_messages_json = json.dumps(messages_dicts, ensure_ascii=False)
        start_time = time.time()
        success = False
        error_message: Optional[str] = None
        response: Any = None
        try:
            response = self._call_with_retry(client, **request_payload)
            success = True
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            latency_ms = int((time.time() - start_time) * 1000)
            self.logger.log_llm(
                model_name=model_name,
                prompt_tokens=0,
                completion_tokens=0,
                request_messages=request_messages_json,
                success=False,
                error_message=error_message,
                latency_ms=latency_ms,
                user_id=user_id,
                session_id=session_id,
            )
            raise

        latency_ms = int((time.time() - start_time) * 1000)

        # 解析响应
        choice = response.choices[0]
        message = choice.message
        content = message.content or ""
        tool_calls_list: Optional[List[Dict[str, Any]]] = None
        if getattr(message, "tool_calls", None):
            tool_calls_list = []
            for tc in message.tool_calls:
                tc_dict: Dict[str, Any] = {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                tool_calls_list.append(tc_dict)

        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else (
            prompt_tokens + completion_tokens
        )

        # 记录 LLM 日志（含 Token 消耗和费用计算）
        self.logger.log_llm(
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            request_messages=request_messages_json,
            success=success,
            response_content=content,
            tool_calls=json.dumps(tool_calls_list, ensure_ascii=False)
            if tool_calls_list
            else None,
            latency_ms=latency_ms,
            error_message=error_message,
            user_id=user_id,
            session_id=session_id,
        )

        return ChatCompletionResponse(
            id=response.id,
            model=model_name,
            content=content,
            tool_calls=tool_calls_list,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def stream_chat_completion(
        self,
        request: ChatCompletionRequest,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> Iterator[str]:
        """流式聊天补全，逐块返回内容文本。"""
        client, default_model, config = self._get_active_client_and_model()
        model_name = request.model or default_model
        max_tokens = request.max_tokens or (
            config.max_tokens if config else 4096
        )
        temperature = request.temperature if request.temperature is not None else (
            config.temperature if config is not None else 0.7
        )

        messages_dicts = self._messages_to_dicts(request.messages)
        request_payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages_dicts,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if request.tools:
            request_payload["tools"] = request.tools

        request_messages_json = json.dumps(messages_dicts, ensure_ascii=False)
        start_time = time.time()
        collected_content: List[str] = []
        success = False
        error_message: Optional[str] = None

        try:
            stream = self._call_with_retry(client, **request_payload)
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if getattr(delta, "content", None):
                    collected_content.append(delta.content)
                    yield delta.content
            success = True
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            latency_ms = int((time.time() - start_time) * 1000)
            self.logger.log_llm(
                model_name=model_name,
                prompt_tokens=0,
                completion_tokens=0,
                request_messages=request_messages_json,
                success=False,
                error_message=error_message,
                latency_ms=latency_ms,
                user_id=user_id,
                session_id=session_id,
            )
            raise

        latency_ms = int((time.time() - start_time) * 1000)
        full_content = "".join(collected_content)
        # 流式接口无法精确获取 token，使用粗略估算（字符数 / 4）
        approx_completion_tokens = max(1, len(full_content) // 4)
        approx_prompt_tokens = max(
            1, sum(len(m.get("content", "")) for m in messages_dicts) // 4
        )
        self.logger.log_llm(
            model_name=model_name,
            prompt_tokens=approx_prompt_tokens,
            completion_tokens=approx_completion_tokens,
            request_messages=request_messages_json,
            success=success,
            response_content=full_content,
            latency_ms=latency_ms,
            error_message=error_message,
            user_id=user_id,
            session_id=session_id,
        )

    def get_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表。"""
        client, _, config = self._get_active_client_and_model()
        try:
            models = client.models.list()
            result: List[Dict[str, Any]] = []
            for model in models.data:
                result.append(
                    {
                        "id": model.id,
                        "created": getattr(model, "created", None),
                        "owned_by": getattr(model, "owned_by", None),
                    }
                )
            return result
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"获取模型列表失败: {exc}")
            # 返回默认模型作为兜底
            default_model = config.model_name if config else settings.DEFAULT_MODEL
            return [{"id": default_model, "created": None, "owned_by": None}]

    # ---- 配置管理 ----
    def create_config(
        self, config: LLMConfigCreate, user_id: int
    ) -> LLMConfig:
        """创建 LLM 配置。"""
        entry = LLMConfig(
            user_id=user_id,
            name=config.name,
            api_key=config.api_key,
            api_base=config.api_base,
            model_name=config.model_name,
            max_tokens=config.max_tokens if config.max_tokens is not None else 4096,
            temperature=config.temperature
            if config.temperature is not None
            else 0.7,
            is_active=False,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_configs(self, user_id: int) -> List[LLMConfig]:
        """获取指定用户的全部 LLM 配置列表。"""
        return (
            self.db.query(LLMConfig)
            .filter(LLMConfig.user_id == user_id)
            .order_by(LLMConfig.created_at.desc())
            .all()
        )

    def get_config(self, config_id: int) -> Optional[LLMConfig]:
        """获取单个 LLM 配置。"""
        return self.db.query(LLMConfig).filter(LLMConfig.id == config_id).first()

    def update_config(
        self, config_id: int, config: LLMConfigUpdate
    ) -> Optional[LLMConfig]:
        """更新 LLM 配置，仅更新非 None 字段。"""
        entry = self.get_config(config_id)
        if entry is None:
            return None
        update_data = config.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        self.db.commit()
        self.db.refresh(entry)

        # 若更新的是当前激活配置，重建客户端
        if entry.is_active and self._config and self._config.id == entry.id:
            self._config = entry
            self.client = self._build_client(entry)
        return entry

    def delete_config(self, config_id: int) -> bool:
        """删除 LLM 配置，返回是否删除成功。"""
        entry = self.get_config(config_id)
        if entry is None:
            return False
        was_active = entry.is_active
        self.db.delete(entry)
        self.db.commit()

        # 若删除的是当前激活配置，回退到默认配置
        if was_active and self._config and self._config.id == config_id:
            self._config = None
            self.client = None
        return True

    def activate_config(self, config_id: int, user_id: int) -> Optional[LLMConfig]:
        """激活指定配置，同一用户只能有一个激活配置。"""
        entry = self.get_config(config_id)
        if entry is None or entry.user_id != user_id:
            return None

        # 先将该用户所有配置置为非激活
        self.db.query(LLMConfig).filter(
            LLMConfig.user_id == user_id
        ).update({LLMConfig.is_active: False})
        # 激活目标配置
        entry.is_active = True
        self.db.commit()
        self.db.refresh(entry)

        # 更新当前服务实例的激活配置和客户端
        self._config = entry
        self.client = self._build_client(entry)
        return entry

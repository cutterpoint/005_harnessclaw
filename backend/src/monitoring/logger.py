"""日志监控模块 - 支持系统操作日志、外部交互日志、LLM交互日志(含Token消耗)。"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.models import SystemLog, ExternalLog, LLMLog


# 模型费用表 ($/1K tokens)
MODEL_PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}


def _setup_file_logger() -> logging.Logger:
    """配置文件日志记录器。"""
    logger = logging.getLogger("harnessclaw")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s - %(message)s")
        )
        logger.addHandler(console_handler)

    return logger


_file_logger = _setup_file_logger()


class Logger:
    """统一日志记录器，支持系统日志、外部交互日志、LLM日志。"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def set_db(self, db: Session) -> None:
        """设置数据库会话。"""
        self.db = db

    # ---- 标准日志 ----
    def info(self, message: str, **kwargs: Any) -> None:
        _file_logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        _file_logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        _file_logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        _file_logger.debug(message, extra=kwargs)

    # ---- 系统操作日志 ----
    def log_system(
        self,
        log_type: str,
        module: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """记录系统操作日志。"""
        _file_logger.info(f"[{log_type}] {module}.{action}: {details}")

        if self.db:
            entry = SystemLog(
                user_id=user_id,
                session_id=session_id,
                log_type=log_type,
                module=module,
                action=action,
                details=json.dumps(details, ensure_ascii=False) if details else None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(entry)
            self.db.commit()

    # ---- 外部交互日志 ----
    def log_external(
        self,
        service_name: str,
        operation: str,
        success: bool,
        request_url: Optional[str] = None,
        request_method: Optional[str] = None,
        request_body: Optional[str] = None,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        latency_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> None:
        """记录外部交互日志。"""
        _file_logger.info(
            f"[EXTERNAL] {service_name}.{operation} success={success} "
            f"latency={latency_ms}ms"
        )

        if self.db:
            entry = ExternalLog(
                user_id=user_id,
                session_id=session_id,
                service_name=service_name,
                operation=operation,
                request_url=request_url,
                request_method=request_method,
                request_body=request_body,
                response_status=response_status,
                response_body=response_body,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
            )
            self.db.add(entry)
            self.db.commit()

    # ---- LLM 交互日志 ----
    def log_llm(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        request_messages: str,
        success: bool,
        response_content: Optional[str] = None,
        tool_calls: Optional[str] = None,
        latency_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> Optional[float]:
        """记录 LLM 交互日志，返回费用(USD)。"""
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(model_name, prompt_tokens, completion_tokens)

        _file_logger.info(
            f"[LLM] model={model_name} prompt_tokens={prompt_tokens} "
            f"completion_tokens={completion_tokens} total={total_tokens} "
            f"cost=${cost:.6f} success={success} latency={latency_ms}ms"
        )

        if self.db:
            entry = LLMLog(
                user_id=user_id,
                session_id=session_id,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_messages=request_messages,
                response_content=response_content,
                tool_calls=tool_calls,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
                cost_usd=cost,
            )
            self.db.add(entry)
            self.db.commit()

        return cost

    @staticmethod
    def calculate_cost(
        model_name: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """计算 LLM 调用费用(USD)。"""
        pricing = MODEL_PRICING.get(model_name, {"input": 0.0, "output": 0.0})
        cost = (
            (prompt_tokens / 1000) * pricing["input"]
            + (completion_tokens / 1000) * pricing["output"]
        )
        return round(cost, 6)

    # ---- 日志查询 ----
    def get_system_logs(
        self,
        user_id: Optional[int] = None,
        log_type: Optional[str] = None,
        module: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """查询系统日志。"""
        if not self.db:
            return {"items": [], "total": 0, "page": page, "limit": limit}

        query = self.db.query(SystemLog)
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        if log_type:
            query = query.filter(SystemLog.log_type == log_type)
        if module:
            query = query.filter(SystemLog.module == module)

        total = query.count()
        items = (
            query.order_by(SystemLog.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {
            "items": [_system_log_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def get_llm_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取 LLM 调用统计信息。"""
        if not self.db:
            return self._empty_statistics()

        query = self.db.query(LLMLog)
        if user_id:
            query = query.filter(LLMLog.user_id == user_id)
        if start_time:
            query = query.filter(LLMLog.created_at >= start_time)
        if end_time:
            query = query.filter(LLMLog.created_at <= end_time)

        logs = query.all()
        if not logs:
            return self._empty_statistics()

        total_calls = len(logs)
        total_prompt = sum(l.prompt_tokens for l in logs)
        total_completion = sum(l.completion_tokens for l in logs)
        total_tokens = sum(l.total_tokens for l in logs)
        total_cost = sum(l.cost_usd or 0 for l in logs)
        success_count = sum(1 for l in logs if l.success)
        latencies = [l.latency_ms for l in logs if l.latency_ms]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # 按模型分组
        model_breakdown: Dict[str, Dict[str, Any]] = {}
        for log in logs:
            if log.model_name not in model_breakdown:
                model_breakdown[log.model_name] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                }
            model_breakdown[log.model_name]["calls"] += 1
            model_breakdown[log.model_name]["tokens"] += log.total_tokens
            model_breakdown[log.model_name]["cost_usd"] += log.cost_usd or 0

        return {
            "total_calls": total_calls,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_latency_ms": round(avg_latency, 1),
            "success_rate": round(success_count / total_calls, 4),
            "model_breakdown": model_breakdown,
        }

    @staticmethod
    def _empty_statistics() -> Dict[str, Any]:
        return {
            "total_calls": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0,
            "success_rate": 0.0,
            "model_breakdown": {},
        }


def _system_log_to_dict(log: SystemLog) -> Dict[str, Any]:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "session_id": log.session_id,
        "log_type": log.log_type,
        "module": log.module,
        "action": log.action,
        "details": json.loads(log.details) if log.details else None,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


# 全局日志实例（不带数据库连接，仅文件日志）
logger = Logger()

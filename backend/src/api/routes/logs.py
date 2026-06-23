"""日志路由模块 - 系统日志、LLM 日志与统计信息查询。"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import LLMLog, User
from src.monitoring.logger import Logger

router = APIRouter()


def _llm_log_to_dict(log: LLMLog) -> Dict[str, Any]:
    """将 LLMLog ORM 对象转为响应字典。"""
    return {
        "id": log.id,
        "user_id": log.user_id,
        "session_id": log.session_id,
        "model_name": log.model_name,
        "prompt_tokens": log.prompt_tokens,
        "completion_tokens": log.completion_tokens,
        "total_tokens": log.total_tokens,
        "response_content": log.response_content,
        "latency_ms": log.latency_ms,
        "success": log.success,
        "error_message": log.error_message,
        "cost_usd": log.cost_usd,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/system")
def get_system_logs(
    log_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询系统日志。"""
    logger = Logger(db=db)
    result = logger.get_system_logs(
        user_id=current_user.id,
        log_type=log_type,
        module=module,
        page=page,
        limit=limit,
    )
    return success_response(data=result, message="success")


@router.get("/llm")
def get_llm_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询 LLM 日志。"""
    query = db.query(LLMLog).filter(LLMLog.user_id == current_user.id)
    total = query.count()
    items = (
        query.order_by(LLMLog.created_at.desc(), LLMLog.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    data = {
        "items": [_llm_log_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "limit": limit,
    }
    return success_response(data=data, message="success")


@router.get("/llm/statistics")
def get_llm_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 LLM 统计信息。"""
    logger = Logger(db=db)
    statistics = logger.get_llm_statistics(user_id=current_user.id)
    return success_response(data=statistics, message="success")

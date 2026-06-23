"""LLM 配置路由模块 - 配置的 CRUD、激活与模型列表查询。"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import User
from src.llm.schemas import LLMConfigCreate, LLMConfigUpdate
from src.llm.service import LLMService

router = APIRouter()


def _mask_api_key(key: str) -> str:
    """脱敏 API Key，仅保留首尾各 4 位。"""
    if not key or len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


def _config_to_dict(config) -> Dict[str, Any]:
    """将 LLMConfig ORM 对象转为响应字典（脱敏 api_key）。"""
    return {
        "id": config.id,
        "user_id": config.user_id,
        "name": config.name,
        "api_key": _mask_api_key(config.api_key),
        "api_base": config.api_base,
        "model_name": config.model_name,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat()
        if config.created_at
        else None,
    }


@router.post("/configs")
def create_config(
    body: LLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建 LLM 配置。"""
    service = LLMService(db)
    config = service.create_config(body, user_id=current_user.id)
    return success_response(
        data=_config_to_dict(config), message="创建成功"
    )


@router.get("/configs")
def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的 LLM 配置列表。"""
    service = LLMService(db)
    configs = service.get_configs(user_id=current_user.id)
    data = [_config_to_dict(c) for c in configs]
    return success_response(data=data, message="success")


@router.get("/configs/{config_id}")
def get_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个 LLM 配置。"""
    service = LLMService(db)
    config = service.get_config(config_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    if config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该配置",
        )
    return success_response(data=_config_to_dict(config), message="success")


@router.put("/configs/{config_id}")
def update_config(
    config_id: int,
    body: LLMConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新 LLM 配置。"""
    service = LLMService(db)
    existing = service.get_config(config_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该配置",
        )
    updated = service.update_config(config_id, body)
    return success_response(
        data=_config_to_dict(updated), message="更新成功"
    )


@router.delete("/configs/{config_id}")
def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除 LLM 配置。"""
    service = LLMService(db)
    existing = service.get_config(config_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该配置",
        )
    service.delete_config(config_id)
    return success_response(data=None, message="删除成功")


@router.post("/configs/{config_id}/activate")
def activate_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """激活 LLM 配置。"""
    service = LLMService(db)
    config = service.activate_config(config_id, user_id=current_user.id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在或无权激活",
        )
    return success_response(
        data=_config_to_dict(config), message="激活成功"
    )


@router.get("/models")
def get_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取可用模型列表。"""
    service = LLMService(db)
    models = service.get_models()
    return success_response(data=models, message="success")

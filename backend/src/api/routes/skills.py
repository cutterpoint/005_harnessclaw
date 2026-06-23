"""技能路由模块 - 技能的 CRUD、执行与训练。"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import User
from src.llm.service import LLMService
from src.skills.schemas import (
    SkillCreate,
    SkillExecutionRequest,
    SkillTrainRequest,
    SkillUpdate,
)
from src.skills.service import SkillManager

router = APIRouter()


@router.post("")
def create_skill(
    body: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建技能。"""
    manager = SkillManager(db)
    skill = manager.create_skill(user_id=current_user.id, skill=body)
    return success_response(
        data=skill.model_dump(mode="json"), message="创建成功"
    )


@router.get("")
def list_skills(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的技能列表。"""
    manager = SkillManager(db)
    result = manager.get_skills(
        user_id=current_user.id, page=page, limit=limit
    )
    data = {
        "items": [item.model_dump(mode="json") for item in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
    }
    return success_response(data=data, message="success")


@router.get("/{skill_id}")
def get_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个技能。"""
    manager = SkillManager(db)
    skill = manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在",
        )
    if skill.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该技能",
        )
    return success_response(
        data=skill.model_dump(mode="json"), message="success"
    )


@router.put("/{skill_id}")
def update_skill(
    skill_id: int,
    body: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新技能。"""
    manager = SkillManager(db)
    existing = manager.get_skill(skill_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该技能",
        )
    try:
        updated = manager.update_skill(skill_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(
        data=updated.model_dump(mode="json"), message="更新成功"
    )


@router.delete("/{skill_id}")
def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除技能。"""
    manager = SkillManager(db)
    existing = manager.get_skill(skill_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该技能",
        )
    manager.delete_skill(skill_id)
    return success_response(data=None, message="删除成功")


@router.post("/{skill_id}/execute")
def execute_skill(
    skill_id: int,
    body: SkillExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """执行技能。"""
    manager = SkillManager(db, llm_service=LLMService(db))
    existing = manager.get_skill(skill_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权执行该技能",
        )
    result = manager.execute_skill(
        skill_id=skill_id,
        input_text=body.input,
        user_id=current_user.id,
        session_id=body.session_id,
    )
    return success_response(
        data=result.model_dump(mode="json"), message="success"
    )


@router.post("/train")
def train_skill(
    body: SkillTrainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """训练技能 - 分析执行历史生成新技能。"""
    manager = SkillManager(db, llm_service=LLMService(db))
    try:
        skill = manager.train_skill(body, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(
        data=skill.model_dump(mode="json"), message="训练成功"
    )

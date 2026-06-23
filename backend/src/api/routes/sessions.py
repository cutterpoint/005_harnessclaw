"""会话路由模块 - 会话的创建、查询、更新、删除及消息管理。"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import User
from src.session.schemas import (
    MessageCreate,
    SessionCreate,
    SessionUpdate,
)
from src.session.service import SessionManager

router = APIRouter()


@router.post("")
def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建会话。"""
    manager = SessionManager(db)
    session = manager.create_session(user_id=current_user.id, title=body.title)
    return success_response(
        data=session.model_dump(mode="json"), message="创建成功"
    )


@router.get("")
def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的会话列表。"""
    manager = SessionManager(db)
    result = manager.get_user_sessions(
        user_id=current_user.id, page=page, limit=limit
    )
    data = {
        "items": [item.model_dump(mode="json") for item in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
    }
    return success_response(data=data, message="success")


@router.get("/{session_id}")
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个会话。"""
    manager = SessionManager(db)
    session = manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    # 校验会话归属
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该会话",
        )
    return success_response(
        data=session.model_dump(mode="json"), message="success"
    )


@router.put("/{session_id}")
def update_session(
    session_id: int,
    body: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新会话。"""
    manager = SessionManager(db)
    existing = manager.get_session(session_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该会话",
        )
    try:
        updated = manager.update_session(session_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(
        data=updated.model_dump(mode="json"), message="更新成功"
    )


@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除会话（软删除）。"""
    manager = SessionManager(db)
    existing = manager.get_session(session_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该会话",
        )
    manager.delete_session(session_id)
    return success_response(data=None, message="删除成功")


@router.get("/{session_id}/messages")
def get_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话消息列表。"""
    manager = SessionManager(db)
    existing = manager.get_session(session_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该会话",
        )
    result = manager.get_messages(session_id, page=page, limit=limit)
    data = {
        "items": [item.model_dump(mode="json") for item in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
    }
    return success_response(data=data, message="success")


@router.post("/{session_id}/messages")
def add_message(
    session_id: int,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """向会话添加消息。"""
    manager = SessionManager(db)
    existing = manager.get_session(session_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该会话",
        )
    try:
        message = manager.add_message(session_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(
        data=message.model_dump(mode="json"), message="添加成功"
    )

"""认证路由模块 - 用户注册、登录、令牌刷新与当前用户信息。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    Token,
    UserCreate,
    UserResponse,
)
from src.auth.service import AuthService
from src.db.database import get_db
from src.db.models import User

router = APIRouter()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册。"""
    auth_service = AuthService(db)
    try:
        created = auth_service.register(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(data=created.model_dump(mode="json"), message="注册成功")


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录。"""
    auth_service = AuthService(db)
    try:
        token = auth_service.login(
            username=request.username, password=request.password
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return success_response(data=token.model_dump(mode="json"), message="登录成功")


@router.post("/refresh")
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """刷新访问令牌。"""
    auth_service = AuthService(db)
    try:
        token = auth_service.refresh_token(request.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return success_response(data=token.model_dump(mode="json"), message="刷新成功")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息。"""
    user_response = UserResponse.model_validate(current_user)
    return success_response(
        data=user_response.model_dump(mode="json"), message="success"
    )

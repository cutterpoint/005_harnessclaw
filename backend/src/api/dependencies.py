"""API 依赖注入模块 - 提供认证依赖与统一响应工具。"""
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.auth.service import AuthService
from src.db.database import get_db
from src.db.models import User

# OAuth2 令牌提取器，指向登录接口
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 JWT Token 获取当前用户。

    Args:
        token: 访问令牌。
        db: 数据库会话。

    Returns:
        当前用户对象。

    Raises:
        HTTPException: 令牌无效或用户不存在时抛出 401 异常。
    """
    auth_service = AuthService(db)
    try:
        user = auth_service.get_current_user(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def success_response(data: Any = None, message: str = "success") -> dict:
    """构造统一成功响应。

    Args:
        data: 响应数据。
        message: 响应消息。

    Returns:
        统一格式的成功响应字典。
    """
    return {"code": 0, "message": message, "data": data}


def error_response(code: int, message: str) -> dict:
    """构造统一错误响应。

    Args:
        code: 错误码。
        message: 错误消息。

    Returns:
        统一格式的错误响应字典。
    """
    return {"code": code, "message": message, "data": None}

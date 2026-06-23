"""认证模块的 Pydantic 数据模型定义。"""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """用户注册请求模型。"""

    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """用户信息响应模型。"""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """令牌响应模型。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """登录请求模型。"""

    username: str
    password: str


class RefreshRequest(BaseModel):
    """刷新令牌请求模型。"""

    refresh_token: str

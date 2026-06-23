"""安全工具模块 - 密码哈希与 JWT 令牌管理。"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from src.core.config import settings


# 密码哈希上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码与哈希值是否匹配。"""
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    """生成密码的 bcrypt 哈希值。"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """创建访问令牌。

    Args:
        data: 需要编码到 JWT 中的负载数据，应包含 "sub" 字段（用户标识）。

    Returns:
        编码后的 JWT 字符串。
    """
    to_encode: Dict[str, Any] = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌。

    Args:
        data: 需要编码到 JWT 中的负载数据，应包含 "sub" 字段（用户标识）。

    Returns:
        编码后的 JWT 字符串。
    """
    to_encode: Dict[str, Any] = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT 令牌。

    Args:
        token: JWT 令牌字符串。

    Returns:
        解码后的负载字典；若令牌无效或已过期，返回 None。
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

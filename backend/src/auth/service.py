"""认证服务模块 - 用户注册、登录、令牌管理业务逻辑。"""
from typing import Optional

from sqlalchemy.orm import Session

from src.auth.schemas import UserCreate, UserResponse, Token
from src.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.db.models import User
from src.monitoring.logger import Logger


class AuthService:
    """认证服务，封装用户认证相关业务逻辑。"""

    def __init__(self, db: Session):
        """初始化认证服务。

        Args:
            db: SQLAlchemy 数据库会话。
        """
        self.db = db
        # 使用当前数据库会话初始化日志记录器，便于记录认证相关日志
        self.logger = Logger(db=db)

    def register(self, user: UserCreate) -> UserResponse:
        """用户注册。

        检查用户名和邮箱唯一性后创建新用户。

        Args:
            user: 用户注册数据。

        Returns:
            注册成功的用户信息。

        Raises:
            ValueError: 用户名或邮箱已被注册。
        """
        # 检查用户名唯一性
        if self.get_user_by_username(user.username):
            self.logger.log_system(
                log_type="event",
                module="auth",
                action="register_failed",
                details={"reason": "duplicate_username", "username": user.username},
            )
            raise ValueError("用户名已被注册")

        # 检查邮箱唯一性
        if self.db.query(User).filter(User.email == user.email).first():
            self.logger.log_system(
                log_type="event",
                module="auth",
                action="register_failed",
                details={"reason": "duplicate_email", "email": user.email},
            )
            raise ValueError("邮箱已被注册")

        # 创建用户记录
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        self.logger.log_system(
            log_type="event",
            module="auth",
            action="register_success",
            details={"user_id": db_user.id, "username": db_user.username},
            user_id=db_user.id,
        )

        return UserResponse.model_validate(db_user)

    def login(self, username: str, password: str) -> Token:
        """用户登录。

        Args:
            username: 用户名。
            password: 明文密码。

        Returns:
            包含访问令牌和刷新令牌的 Token 对象。

        Raises:
            ValueError: 用户名或密码错误。
        """
        user = self.authenticate(username, password)
        if not user:
            self.logger.log_system(
                log_type="event",
                module="auth",
                action="login_failed",
                details={"reason": "invalid_credentials", "username": username},
            )
            raise ValueError("用户名或密码错误")

        if not user.is_active:
            self.logger.log_system(
                log_type="event",
                module="auth",
                action="login_failed",
                details={"reason": "inactive_user", "username": username},
                user_id=user.id,
            )
            raise ValueError("用户已被禁用")

        # 生成令牌
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        self.logger.log_system(
            log_type="event",
            module="auth",
            action="login_success",
            details={"username": user.username},
            user_id=user.id,
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def refresh_token(self, refresh_token: str) -> Token:
        """刷新访问令牌。

        Args:
            refresh_token: 刷新令牌。

        Returns:
            包含新访问令牌和刷新令牌的 Token 对象。

        Raises:
            ValueError: 刷新令牌无效或已过期。
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            self.logger.log_system(
                log_type="event",
                module="auth",
                action="refresh_failed",
                details={"reason": "invalid_refresh_token"},
            )
            raise ValueError("刷新令牌无效或已过期")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("刷新令牌无效或已过期")

        user = self.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            raise ValueError("刷新令牌无效或已过期")

        # 生成新的令牌对
        token_data = {"sub": str(user.id), "username": user.username}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        self.logger.log_system(
            log_type="event",
            module="auth",
            action="refresh_success",
            details={"username": user.username},
            user_id=user.id,
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户。"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据用户 ID 获取用户。"""
        return self.db.query(User).filter(User.id == user_id).first()

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """验证用户名与密码。

        Args:
            username: 用户名。
            password: 明文密码。

        Returns:
            验证成功返回 User 对象，失败返回 None。
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def get_current_user(self, token: str) -> User:
        """从访问令牌中获取当前用户。

        Args:
            token: 访问令牌。

        Returns:
            当前用户对象。

        Raises:
            ValueError: 令牌无效、已过期或用户不存在。
        """
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise ValueError("访问令牌无效或已过期")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("访问令牌无效或已过期")

        user = self.get_user_by_id(int(user_id))
        if not user:
            raise ValueError("用户不存在")
        if not user.is_active:
            raise ValueError("用户已被禁用")

        return user

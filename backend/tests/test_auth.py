"""认证服务模块单元测试。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.schemas import UserCreate
from src.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)
from src.auth.service import AuthService
from src.db.database import Base
from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata


@pytest.fixture
def db_session():
    """创建内存 SQLite 数据库会话，每个测试函数独立隔离。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_service(db_session):
    """创建认证服务实例。"""
    return AuthService(db_session)


@pytest.fixture
def sample_user_data():
    """测试用户数据。"""
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="SecurePassword123",
    )


class TestRegister:
    """用户注册相关测试。"""

    def test_register_success(self, auth_service, sample_user_data):
        """测试成功注册用户。"""
        response = auth_service.register(sample_user_data)

        assert response.id is not None
        assert response.username == sample_user_data.username
        assert response.email == sample_user_data.email
        assert response.is_active is True
        assert response.created_at is not None

    def test_register_duplicate_username(self, auth_service, sample_user_data):
        """测试重复用户名注册失败。"""
        # 第一次注册
        auth_service.register(sample_user_data)

        # 第二次使用相同用户名（不同邮箱）应失败
        duplicate = UserCreate(
            username=sample_user_data.username,
            email="another@example.com",
            password="AnotherPassword456",
        )
        with pytest.raises(ValueError, match="用户名已被注册"):
            auth_service.register(duplicate)

    def test_register_duplicate_email(self, auth_service, sample_user_data):
        """测试重复邮箱注册失败。"""
        # 第一次注册
        auth_service.register(sample_user_data)

        # 第二次使用相同邮箱（不同用户名）应失败
        duplicate = UserCreate(
            username="anotheruser",
            email=sample_user_data.email,
            password="AnotherPassword456",
        )
        with pytest.raises(ValueError, match="邮箱已被注册"):
            auth_service.register(duplicate)


class TestLogin:
    """用户登录相关测试。"""

    def test_login_success(self, auth_service, sample_user_data):
        """测试成功登录。"""
        auth_service.register(sample_user_data)

        token = auth_service.login(
            username=sample_user_data.username,
            password=sample_user_data.password,
        )

        assert token.access_token is not None
        assert token.refresh_token is not None
        assert token.token_type == "bearer"

        # 验证访问令牌可解码且类型正确
        payload = decode_token(token.access_token)
        assert payload is not None
        assert payload.get("type") == "access"
        assert payload.get("username") == sample_user_data.username

    def test_login_wrong_password(self, auth_service, sample_user_data):
        """测试密码错误登录失败。"""
        auth_service.register(sample_user_data)

        with pytest.raises(ValueError, match="用户名或密码错误"):
            auth_service.login(
                username=sample_user_data.username,
                password="WrongPassword",
            )

    def test_login_nonexistent_user(self, auth_service):
        """测试不存在的用户登录失败。"""
        with pytest.raises(ValueError, match="用户名或密码错误"):
            auth_service.login(
                username="nonexistent",
                password="AnyPassword",
            )


class TestRefreshToken:
    """令牌刷新相关测试。"""

    def test_refresh_token(self, auth_service, sample_user_data):
        """测试刷新令牌。"""
        auth_service.register(sample_user_data)
        token = auth_service.login(
            username=sample_user_data.username,
            password=sample_user_data.password,
        )

        # 使用刷新令牌获取新令牌
        new_token = auth_service.refresh_token(token.refresh_token)

        assert new_token.access_token is not None
        assert new_token.refresh_token is not None
        assert new_token.token_type == "bearer"

        # 新访问令牌应可正常解码
        payload = decode_token(new_token.access_token)
        assert payload is not None
        assert payload.get("type") == "access"
        assert payload.get("username") == sample_user_data.username

    def test_refresh_token_invalid(self, auth_service):
        """测试无效刷新令牌。"""
        with pytest.raises(ValueError, match="刷新令牌无效或已过期"):
            auth_service.refresh_token("invalid.refresh.token")


class TestGetCurrentUser:
    """获取当前用户相关测试。"""

    def test_get_current_user(self, auth_service, sample_user_data):
        """测试从令牌获取当前用户。"""
        auth_service.register(sample_user_data)
        token = auth_service.login(
            username=sample_user_data.username,
            password=sample_user_data.password,
        )

        user = auth_service.get_current_user(token.access_token)

        assert user is not None
        assert user.username == sample_user_data.username
        assert user.email == sample_user_data.email
        assert user.is_active is True


class TestPasswordHashing:
    """密码哈希相关测试。"""

    def test_password_hashing(self):
        """测试密码哈希和验证。"""
        plain_password = "MySecretPassword123"

        # 生成哈希
        hashed = get_password_hash(plain_password)

        # 哈希值不应等于明文
        assert hashed != plain_password
        assert hashed is not None
        assert len(hashed) > 0

        # 正确密码应验证通过
        assert verify_password(plain_password, hashed) is True

        # 错误密码应验证失败
        assert verify_password("WrongPassword", hashed) is False

    def test_password_hash_uniqueness(self):
        """测试相同密码生成不同的哈希值（bcrypt 盐值）。"""
        password = "SamePassword456"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # 由于盐值不同，两次哈希结果应不同
        assert hash1 != hash2

        # 但都能正确验证
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenCreation:
    """令牌创建相关测试。"""

    def test_access_token_creation(self):
        """测试访问令牌创建与解码。"""
        data = {"sub": "1", "username": "testuser"}
        token = create_access_token(data)

        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "1"
        assert payload.get("username") == "testuser"
        assert payload.get("type") == "access"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        """测试解码无效令牌返回 None。"""
        result = decode_token("invalid.token.here")
        assert result is None

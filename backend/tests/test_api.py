"""API 集成测试 - 使用 FastAPI TestClient 和内存 SQLite。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata
from src.db.database import Base, get_db


@pytest.fixture
def test_engine():
    """创建内存 SQLite 测试引擎（StaticPool 共享同一连接）。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_engine):
    """创建测试客户端，覆盖数据库依赖。"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client):
    """注册用户并登录，返回访问令牌。"""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "SecurePassword123"},
    )
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """获取认证请求头。"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAPI:
    """API 集成测试。"""

    def test_root(self, client):
        """测试根路径。"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["service"] == "HarnessClaw API"

    def test_register_and_login(self, client):
        """测试注册并登录。"""
        # 注册
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePassword123",
            },
        )
        assert response.status_code == 200
        assert response.json()["code"] == 0

        # 登录
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "newuser", "password": "SecurePassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_create_session(self, client, auth_headers):
        """测试创建会话（需认证）。"""
        response = client.post(
            "/api/v1/sessions",
            json={"title": "测试会话"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["title"] == "测试会话"
        assert data["data"]["status"] == "active"

    def test_create_skill(self, client, auth_headers):
        """测试创建技能（需认证）。"""
        response = client.post(
            "/api/v1/skills",
            json={
                "name": "翻译技能",
                "description": "将文本翻译为英文",
                "prompt": "请将以下文本翻译为英文：",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "翻译技能"

    def test_register_tool(self, client, auth_headers):
        """测试注册工具（需认证）。"""
        response = client.post(
            "/api/v1/tools",
            json={
                "name": "calculator",
                "description": "简单计算器",
                "function_name": "calculate",
                "module_path": "src.tools.builtin.calculator",
                "parameters": [
                    {
                        "name": "expression",
                        "type": "string",
                        "required": True,
                        "description": "计算表达式",
                    }
                ],
                "return_type": "string",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "calculator"

    def test_create_workflow(self, client, auth_headers):
        """测试创建工作流（需认证）。"""
        response = client.post(
            "/api/v1/workflows",
            json={
                "name": "测试工作流",
                "description": "用于测试的工作流",
                "nodes": [
                    {"name": "start", "type": "summary", "config": {}}
                ],
                "edges": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "测试工作流"

    def test_create_llm_config(self, client, auth_headers):
        """测试创建 LLM 配置（需认证）。"""
        response = client.post(
            "/api/v1/llm/configs",
            json={
                "name": "测试配置",
                "api_key": "sk-test-key-1234567890",
                "api_base": "https://api.openai.com/v1",
                "model_name": "gpt-4o",
                "max_tokens": 4096,
                "temperature": 0.7,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "测试配置"
        # 验证 api_key 已脱敏
        assert "***" in data["data"]["api_key"]

    def test_unauthorized_access(self, client):
        """测试未认证访问受保护资源。"""
        response = client.get("/api/v1/sessions")
        assert response.status_code == 401

    def test_get_logs(self, client, auth_headers):
        """测试获取日志（需认证）。"""
        response = client.get("/api/v1/logs/system", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # 注册和登录操作应产生系统日志
        assert data["data"]["total"] > 0

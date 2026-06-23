"""工具模块单元测试。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata
from src.db.models import User
from src.tools.schemas import Parameter, ToolCreate, ToolUpdate
from src.tools.registry import ToolRegistry
from src.tools.validator import ToolValidator
from src.tools.executor import ToolExecutor


# ---------------------------------------------------------------------------
# 公共夹具
# ---------------------------------------------------------------------------

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
def registry(db_session):
    """创建工具注册表实例。"""
    return ToolRegistry(db_session)


@pytest.fixture
def validator():
    """创建工具验证器实例。"""
    return ToolValidator()


@pytest.fixture
def executor(db_session):
    """创建工具执行器实例。"""
    return ToolExecutor(db_session)


@pytest.fixture
def sample_tool_data():
    """测试工具数据（计算器工具）。"""
    return ToolCreate(
        name="calculator",
        description="简单计算器工具",
        function_name="calculate",
        module_path="src.tools.builtin.calculator",
        parameters=[
            Parameter(
                name="expression",
                type="string",
                required=True,
                description="数学表达式",
            )
        ],
        return_type="object",
    )


@pytest.fixture
def sample_user(db_session):
    """创建测试用户，用于工具执行记录的外键关联。"""
    user = User(
        username="tooluser",
        email="tool@example.com",
        hashed_password="fakehash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# 注册表测试
# ---------------------------------------------------------------------------

class TestRegistry:
    """工具注册表相关测试。"""

    def test_register_tool(self, registry, sample_tool_data):
        """测试成功注册工具。"""
        tool = registry.register(sample_tool_data)

        assert tool.id is not None
        assert tool.name == sample_tool_data.name
        assert tool.function_name == sample_tool_data.function_name
        assert tool.module_path == sample_tool_data.module_path
        assert tool.is_enabled is True
        assert tool.created_at is not None
        # 参数已序列化为 JSON 字符串
        import json
        params = json.loads(tool.parameters)
        assert len(params) == 1
        assert params[0]["name"] == "expression"

    def test_register_duplicate(self, registry, sample_tool_data):
        """测试重复名称注册失败。"""
        registry.register(sample_tool_data)
        with pytest.raises(ValueError, match="工具名称已存在"):
            registry.register(sample_tool_data)

    def test_get_tool(self, registry, sample_tool_data):
        """测试按 ID 获取工具。"""
        tool = registry.register(sample_tool_data)
        fetched = registry.get(tool.id)
        assert fetched is not None
        assert fetched.id == tool.id
        assert fetched.name == tool.name

    def test_get_by_name(self, registry, sample_tool_data):
        """测试按名称获取工具。"""
        registry.register(sample_tool_data)
        fetched = registry.get_by_name("calculator")
        assert fetched is not None
        assert fetched.name == "calculator"

    def test_get_nonexistent(self, registry):
        """测试获取不存在的工具返回 None。"""
        assert registry.get(9999) is None
        assert registry.get_by_name("nonexistent") is None

    def test_list_tools(self, registry, sample_tool_data):
        """测试工具列表查询。"""
        # 注册两个工具
        registry.register(sample_tool_data)
        another = ToolCreate(
            name="another_tool",
            description="另一个工具",
            function_name="calculate",
            module_path="src.tools.builtin.calculator",
            parameters=[],
        )
        registry.register(another)

        # 默认仅返回启用的工具
        enabled = registry.list(enabled_only=True)
        assert len(enabled) == 2

        # 禁用一个后再查询
        another_tool = registry.get_by_name("another_tool")
        registry.update(another_tool.id, ToolUpdate(is_enabled=False))
        enabled = registry.list(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].name == "calculator"

        # 包含禁用的
        all_tools = registry.list(enabled_only=False)
        assert len(all_tools) == 2

    def test_update_tool(self, registry, sample_tool_data):
        """测试更新工具信息。"""
        tool = registry.register(sample_tool_data)
        updated = registry.update(
            tool.id,
            ToolUpdate(
                description="更新后的描述",
                is_enabled=False,
            ),
        )
        assert updated.description == "更新后的描述"
        assert updated.is_enabled is False
        # 未更新的字段保持不变
        assert updated.name == sample_tool_data.name

    def test_update_tool_parameters(self, registry, sample_tool_data):
        """测试更新工具参数定义。"""
        tool = registry.register(sample_tool_data)
        updated = registry.update(
            tool.id,
            ToolUpdate(
                parameters=[
                    Parameter(name="expression", type="string", required=False),
                ],
            ),
        )
        import json
        params = json.loads(updated.parameters)
        assert params[0]["required"] is False

    def test_update_nonexistent(self, registry):
        """测试更新不存在的工具抛出异常。"""
        with pytest.raises(ValueError, match="工具不存在"):
            registry.update(9999, ToolUpdate(description="x"))

    def test_delete_tool(self, registry, sample_tool_data):
        """测试删除工具。"""
        tool = registry.register(sample_tool_data)
        assert registry.delete(tool.id) is True
        assert registry.get(tool.id) is None

    def test_delete_nonexistent(self, registry):
        """测试删除不存在的工具返回 False。"""
        assert registry.delete(9999) is False


# ---------------------------------------------------------------------------
# 验证器测试
# ---------------------------------------------------------------------------

class TestValidator:
    """工具参数验证器相关测试。"""

    def test_validate_parameters(self, validator, registry, sample_tool_data):
        """测试参数验证通过。"""
        tool = registry.register(sample_tool_data)
        valid, errors = validator.validate(tool, {"expression": "1 + 2"})
        assert valid is True
        assert errors == []

    def test_validate_missing_required(self, validator, registry, sample_tool_data):
        """测试缺少必填参数验证失败。"""
        tool = registry.register(sample_tool_data)
        valid, errors = validator.validate(tool, {})
        assert valid is False
        assert any("缺少必填参数" in e for e in errors)

    def test_validate_wrong_type(self, validator, registry, sample_tool_data):
        """测试参数类型错误验证失败。"""
        tool = registry.register(sample_tool_data)
        # expression 应为 string，传入整数
        valid, errors = validator.validate(tool, {"expression": 123})
        assert valid is False
        assert any("参数类型错误" in e for e in errors)

    def test_validate_optional_param(self, validator, db_session):
        """测试可选参数缺失时验证通过。"""
        registry = ToolRegistry(db_session)
        tool = registry.register(ToolCreate(
            name="optional_tool",
            function_name="calculate",
            module_path="src.tools.builtin.calculator",
            parameters=[
                Parameter(name="expression", type="string", required=True),
                Parameter(name="verbose", type="boolean", required=False),
            ],
        ))
        valid, errors = validator.validate(tool, {"expression": "1+1"})
        assert valid is True
        assert errors == []

    def test_validate_type_integer(self, validator):
        """测试整数类型验证（排除布尔值）。"""
        assert validator.validate_type(42, "integer") is True
        assert validator.validate_type(3.14, "integer") is False
        # 布尔值不应被当作整数
        assert validator.validate_type(True, "integer") is False

    def test_validate_type_boolean(self, validator):
        """测试布尔类型验证。"""
        assert validator.validate_type(True, "boolean") is True
        assert validator.validate_type(False, "boolean") is True
        assert validator.validate_type(1, "boolean") is False

    def test_validate_type_string(self, validator):
        """测试字符串类型验证。"""
        assert validator.validate_type("hello", "string") is True
        assert validator.validate_type(123, "string") is False

    def test_validate_type_object(self, validator):
        """测试对象类型验证。"""
        assert validator.validate_type({"a": 1}, "object") is True
        assert validator.validate_type([1, 2], "object") is False

    def test_validate_type_array(self, validator):
        """测试数组类型验证。"""
        assert validator.validate_type([1, 2], "array") is True
        assert validator.validate_type({"a": 1}, "array") is False


# ---------------------------------------------------------------------------
# 执行器测试
# ---------------------------------------------------------------------------

class TestExecutor:
    """工具执行器相关测试。"""

    def test_execute_tool(self, executor, registry, sample_tool_data, sample_user):
        """测试执行内置计算器工具。"""
        registry.register(sample_tool_data)

        result = executor.execute(
            tool_name="calculator",
            arguments={"expression": "1 + 2 * 3"},
            user_id=sample_user.id,
        )

        assert result.success is True
        assert result.error is None
        assert result.tool_id is not None
        assert result.execution_time >= 0
        assert result.result["expression"] == "1 + 2 * 3"
        assert result.result["result"] == 7

    def test_execute_by_id(self, executor, registry, sample_tool_data, sample_user):
        """测试按 ID 执行工具。"""
        tool = registry.register(sample_tool_data)

        result = executor.execute_by_id(
            tool_id=tool.id,
            arguments={"expression": "10 - 4"},
            user_id=sample_user.id,
        )

        assert result.success is True
        assert result.result["result"] == 6

    def test_execute_nonexistent(self, executor):
        """测试执行不存在的工具返回失败。"""
        result = executor.execute(
            tool_name="nonexistent_tool",
            arguments={},
        )
        assert result.success is False
        assert "工具不存在" in result.error

    def test_execute_invalid_params(self, executor, registry, sample_tool_data, sample_user):
        """测试参数验证失败时执行返回失败。"""
        registry.register(sample_tool_data)

        # 缺少必填参数
        result = executor.execute(
            tool_name="calculator",
            arguments={},
            user_id=sample_user.id,
        )
        assert result.success is False
        assert "缺少必填参数" in result.error

        # 类型错误
        result = executor.execute(
            tool_name="calculator",
            arguments={"expression": 123},
            user_id=sample_user.id,
        )
        assert result.success is False
        assert "参数类型错误" in result.error

    def test_execute_records_execution(self, executor, registry, sample_tool_data, sample_user, db_session):
        """测试执行结果被记录到数据库。"""
        registry.register(sample_tool_data)

        executor.execute(
            tool_name="calculator",
            arguments={"expression": "2 + 2"},
            user_id=sample_user.id,
        )

        # 查询执行记录
        from src.db.models import ToolExecution
        records = db_session.query(ToolExecution).all()
        assert len(records) == 1
        assert records[0].success is True
        assert records[0].user_id == sample_user.id

    def test_get_tools(self, executor, registry, sample_tool_data):
        """测试获取可用工具列表。"""
        registry.register(sample_tool_data)
        tools = executor.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_get_openai_tools(self, executor, registry, sample_tool_data):
        """测试获取 OpenAI 格式工具列表。"""
        registry.register(sample_tool_data)
        openai_tools = executor.get_openai_tools()
        assert len(openai_tools) == 1

        tool_def = openai_tools[0]
        assert tool_def["type"] == "function"
        assert tool_def["function"]["name"] == "calculator"
        assert "expression" in tool_def["function"]["parameters"]["properties"]
        assert "expression" in tool_def["function"]["parameters"]["required"]


# ---------------------------------------------------------------------------
# OpenAI 格式转换测试
# ---------------------------------------------------------------------------

class TestOpenAIFormat:
    """工具转 OpenAI function calling 格式相关测试。"""

    def test_to_openai_format(self, registry, sample_tool_data):
        """测试工具转换为 OpenAI 格式。"""
        tool = registry.register(sample_tool_data)
        fmt = registry.to_openai_format(tool)

        assert fmt["type"] == "function"
        func = fmt["function"]
        assert func["name"] == "calculator"
        assert func["description"] == "简单计算器工具"

        params = func["parameters"]
        assert params["type"] == "object"
        assert "expression" in params["properties"]
        assert params["properties"]["expression"]["type"] == "string"
        assert params["required"] == ["expression"]

    def test_to_openai_format_multiple_params(self, registry):
        """测试多参数工具的 OpenAI 格式转换。"""
        tool = registry.register(ToolCreate(
            name="multi_param",
            description="多参数工具",
            function_name="calculate",
            module_path="src.tools.builtin.calculator",
            parameters=[
                Parameter(name="expr", type="string", required=True),
                Parameter(name="verbose", type="boolean", required=False),
                Parameter(name="count", type="integer", required=True),
            ],
        ))
        fmt = registry.to_openai_format(tool)
        params = fmt["function"]["parameters"]
        assert set(params["properties"].keys()) == {"expr", "verbose", "count"}
        # required 仅包含必填参数
        assert set(params["required"]) == {"expr", "count"}

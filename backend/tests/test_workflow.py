"""工作流编排模块单元测试 - 使用内存 SQLite 与 mock 依赖。"""
import os
import sys
import unittest
from unittest.mock import MagicMock

import pytest

# 确保后端目录在 sys.path 中
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata
from src.db.database import Base
from src.db.models import User, WorkflowExecution
from src.decision.schemas import DecisionAction, DecisionResult
from src.tools.schemas import ToolExecutionResult
from src.skills.schemas import SkillExecutionResult
from src.workflow.orchestrator import WorkflowOrchestrator
from src.workflow.schemas import (
    WorkflowCreate,
    WorkflowEdge,
    WorkflowNode,
    WorkflowUpdate,
)


# ----------------------------- 测试夹具 -----------------------------
@pytest.fixture()
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


@pytest.fixture()
def test_user(db_session) -> User:
    """创建测试用户。"""
    user = User(
        username="workflow_tester",
        email="workflow_tester@example.com",
        hashed_password="fake-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def mock_decision_engine():
    """创建 mock 决策引擎实例。"""
    engine = MagicMock()
    # 默认 decide 返回一个直接回复的决策结果
    engine.decide.return_value = DecisionResult(
        action=DecisionAction(
            type="direct_response",
            content="这是决策回复。",
        ),
        raw_response="这是决策回复。",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        latency_ms=100,
    )
    # 默认 summarize 返回总结文本
    engine.summarize.return_value = "这是总结回复。"
    return engine


@pytest.fixture()
def mock_tool_executor():
    """创建 mock 工具执行器实例。"""
    executor = MagicMock()
    # 默认 execute 返回成功结果
    executor.execute.return_value = ToolExecutionResult(
        tool_id=1,
        success=True,
        result={"value": 42},
        execution_time=0.01,
    )
    return executor


@pytest.fixture()
def mock_skill_manager():
    """创建 mock 技能管理器实例。"""
    manager = MagicMock()
    # 默认 execute_skill 返回成功结果
    manager.execute_skill.return_value = SkillExecutionResult(
        skill_id=1,
        success=True,
        output="这是技能执行输出。",
        execution_time=0.01,
    )
    return manager


@pytest.fixture()
def orchestrator(db_session, mock_decision_engine, mock_tool_executor, mock_skill_manager):
    """创建带全部 mock 依赖的工作流编排器实例。"""
    return WorkflowOrchestrator(
        db=db_session,
        decision_engine=mock_decision_engine,
        tool_executor=mock_tool_executor,
        skill_manager=mock_skill_manager,
    )


@pytest.fixture()
def orchestrator_no_deps(db_session):
    """创建不带任何依赖的工作流编排器实例。"""
    return WorkflowOrchestrator(db=db_session)


def _make_simple_workflow(
    name: str = "简单工作流",
) -> WorkflowCreate:
    """构造一个仅含总结节点的简单工作流。"""
    return WorkflowCreate(
        name=name,
        description="仅含一个总结节点的简单工作流",
        nodes=[
            WorkflowNode(
                name="summary_node",
                type="summary",
                config={},
            ),
        ],
        edges=[],
    )


def _make_decision_workflow(
    name: str = "决策工作流",
) -> WorkflowCreate:
    """构造一个包含决策节点和总结节点的工作流。"""
    return WorkflowCreate(
        name=name,
        description="决策 -> 总结 的工作流",
        nodes=[
            WorkflowNode(
                name="decision_node",
                type="decision",
                config={},
            ),
            WorkflowNode(
                name="summary_node",
                type="summary",
                config={},
            ),
        ],
        edges=[
            WorkflowEdge(source="decision_node", target="summary_node"),
        ],
    )


def _make_tool_workflow(
    name: str = "工具工作流",
    tool_name: str = "calculator",
) -> WorkflowCreate:
    """构造一个包含工具节点的工作流。"""
    return WorkflowCreate(
        name=name,
        description="包含工具节点的工作流",
        nodes=[
            WorkflowNode(
                name="tool_node",
                type="tool",
                config={
                    "tool_name": tool_name,
                    "arguments": {"expression": "1+1"},
                },
            ),
        ],
        edges=[],
    )


# ----------------------------- 工作流 CRUD 测试 -----------------------------
class TestWorkflowCRUD:
    """工作流增删改查相关测试。"""

    def test_create_workflow(self, orchestrator, test_user):
        """测试创建工作流。"""
        workflow_data = _make_decision_workflow()
        response = orchestrator.create_workflow(
            user_id=test_user.id, workflow=workflow_data
        )

        assert response.id is not None
        assert response.user_id == test_user.id
        assert response.name == "决策工作流"
        assert response.description == "决策 -> 总结 的工作流"
        assert response.is_enabled is True
        assert response.created_at is not None
        # 验证节点和边被正确序列化与反序列化
        assert len(response.nodes) == 2
        assert response.nodes[0].name == "decision_node"
        assert response.nodes[0].type == "decision"
        assert response.nodes[1].name == "summary_node"
        assert response.nodes[1].type == "summary"
        assert len(response.edges) == 1
        assert response.edges[0].source == "decision_node"
        assert response.edges[0].target == "summary_node"

    def test_get_workflow(self, orchestrator, test_user):
        """测试获取工作流。"""
        workflow_data = _make_simple_workflow()
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=workflow_data
        )

        fetched = orchestrator.get_workflow(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name
        assert len(fetched.nodes) == 1
        assert fetched.nodes[0].name == "summary_node"
        assert fetched.nodes[0].type == "summary"

    def test_get_workflow_not_found(self, orchestrator):
        """测试获取不存在的工作流返回 None。"""
        assert orchestrator.get_workflow(9999) is None

    def test_get_workflows(self, orchestrator, test_user):
        """测试获取工作流列表（含分页与用户隔离）。"""
        # 用户 1 创建 3 个工作流
        for i in range(3):
            orchestrator.create_workflow(
                user_id=test_user.id,
                workflow=_make_simple_workflow(name=f"工作流{i}"),
            )
        # 用户 2 创建 1 个工作流
        other_user = User(
            username="other",
            email="other@example.com",
            hashed_password="fake-hash",
            is_active=True,
        )
        orchestrator.db.add(other_user)
        orchestrator.db.commit()
        orchestrator.db.refresh(other_user)
        orchestrator.create_workflow(
            user_id=other_user.id,
            workflow=_make_simple_workflow(name="用户2工作流"),
        )

        # 获取用户 1 全部工作流
        result = orchestrator.get_workflows(user_id=test_user.id, page=1, limit=20)
        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["page"] == 1
        assert result["limit"] == 20

        # 分页：第 1 页 2 条
        result = orchestrator.get_workflows(user_id=test_user.id, page=1, limit=2)
        assert result["total"] == 3
        assert len(result["items"]) == 2

        # 分页：第 2 页 2 条（只剩 1 条）
        result = orchestrator.get_workflows(user_id=test_user.id, page=2, limit=2)
        assert result["total"] == 3
        assert len(result["items"]) == 1

        # 用户隔离：用户 2 只有 1 个工作流
        result = orchestrator.get_workflows(user_id=other_user.id)
        assert result["total"] == 1

    def test_update_workflow(self, orchestrator, test_user):
        """测试更新工作流。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow(name="原名")
        )

        # 更新名称和描述
        updated = orchestrator.update_workflow(
            created.id,
            WorkflowUpdate(name="新名称", description="新描述"),
        )
        assert updated.name == "新名称"
        assert updated.description == "新描述"
        # 未更新的字段保持原值
        assert updated.is_enabled is True

        # 更新启用状态
        updated = orchestrator.update_workflow(
            created.id, WorkflowUpdate(is_enabled=False)
        )
        assert updated.is_enabled is False
        assert updated.name == "新名称"

        # 更新节点和边
        new_nodes = [
            WorkflowNode(name="new_node", type="tool", config={"tool_name": "calc"}),
        ]
        new_edges = []
        updated = orchestrator.update_workflow(
            created.id, WorkflowUpdate(nodes=new_nodes, edges=new_edges),
        )
        assert len(updated.nodes) == 1
        assert updated.nodes[0].name == "new_node"
        assert updated.nodes[0].type == "tool"
        assert len(updated.edges) == 0

    def test_update_workflow_not_found(self, orchestrator):
        """测试更新不存在的工作流抛出异常。"""
        with pytest.raises(ValueError, match="工作流不存在"):
            orchestrator.update_workflow(9999, WorkflowUpdate(name="x"))

    def test_delete_workflow(self, orchestrator, test_user):
        """测试删除工作流。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow(name="待删除")
        )

        result = orchestrator.delete_workflow(created.id)
        assert result is True

        # 验证已删除
        assert orchestrator.get_workflow(created.id) is None

    def test_delete_workflow_not_found(self, orchestrator):
        """测试删除不存在的工作流返回 False。"""
        assert orchestrator.delete_workflow(9999) is False


# ----------------------------- 工作流执行测试 -----------------------------
class TestWorkflowExecution:
    """工作流执行相关测试。"""

    def test_execute_workflow_simple(
        self, orchestrator, mock_decision_engine, test_user
    ):
        """测试执行简单工作流（仅含总结节点，mock 依赖）。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        inputs = {"messages": [{"role": "user", "content": "你好"}]}
        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs=inputs,
            user_id=test_user.id,
        )

        assert result.execution_id is not None
        assert result.workflow_id == created.id
        assert result.status == "completed"
        assert result.error is None
        assert result.outputs is not None
        assert result.started_at is not None
        assert result.completed_at is not None

        # 验证总结节点被调用
        mock_decision_engine.summarize.assert_called_once()
        call_kwargs = mock_decision_engine.summarize.call_args
        messages = call_kwargs.args[0]
        assert messages == [{"role": "user", "content": "你好"}]

        # 验证输出中包含总结结果
        assert result.outputs["nodes"]["summary_node"]["summary"] == "这是总结回复。"

    def test_execute_workflow_with_decision(
        self, orchestrator, mock_decision_engine, test_user
    ):
        """测试执行包含决策节点的工作流。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_decision_workflow()
        )

        inputs = {"messages": [{"role": "user", "content": "1+1等于几"}]}
        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs=inputs,
            user_id=test_user.id,
        )

        assert result.status == "completed"
        assert result.error is None

        # 验证决策节点和总结节点都被调用
        mock_decision_engine.decide.assert_called_once()
        mock_decision_engine.summarize.assert_called_once()

        # 验证决策节点输出
        decision_output = result.outputs["nodes"]["decision_node"]
        assert decision_output["success"] is True
        assert decision_output["raw_response"] == "这是决策回复。"

        # 验证总结节点输出
        summary_output = result.outputs["nodes"]["summary_node"]
        assert summary_output["summary"] == "这是总结回复。"

    def test_execute_workflow_with_tool(
        self, orchestrator, mock_tool_executor, test_user
    ):
        """测试执行包含工具节点的工作流。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_tool_workflow(tool_name="calculator")
        )

        inputs = {"expression": "1+1"}
        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs=inputs,
            user_id=test_user.id,
        )

        assert result.status == "completed"
        assert result.error is None

        # 验证工具执行器被调用
        mock_tool_executor.execute.assert_called_once()
        call_kwargs = mock_tool_executor.execute.call_args
        assert call_kwargs.kwargs["tool_name"] == "calculator"
        assert call_kwargs.kwargs["arguments"] == {"expression": "1+1"}

        # 验证工具节点输出
        tool_output = result.outputs["nodes"]["tool_node"]
        assert tool_output["success"] is True
        assert tool_output["result"] == {"value": 42}
        assert tool_output["tool_name"] == "calculator"

    def test_execute_workflow_with_skill(
        self, orchestrator, mock_skill_manager, test_user
    ):
        """测试执行包含技能节点的工作流。"""
        workflow_data = WorkflowCreate(
            name="技能工作流",
            description="包含技能节点的工作流",
            nodes=[
                WorkflowNode(
                    name="skill_node",
                    type="skill",
                    config={"skill_id": 1, "input_text": "翻译这段话"},
                ),
            ],
            edges=[],
        )
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=workflow_data
        )

        inputs = {}
        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs=inputs,
            user_id=test_user.id,
        )

        assert result.status == "completed"
        assert result.error is None

        # 验证技能管理器被调用
        mock_skill_manager.execute_skill.assert_called_once()
        call_kwargs = mock_skill_manager.execute_skill.call_args
        assert call_kwargs.kwargs["skill_id"] == 1
        assert call_kwargs.kwargs["input_text"] == "翻译这段话"

        # 验证技能节点输出
        skill_output = result.outputs["nodes"]["skill_node"]
        assert skill_output["success"] is True
        assert skill_output["output"] == "这是技能执行输出。"

    def test_execute_workflow_not_found(self, orchestrator, test_user):
        """测试执行不存在的工作流抛出异常。"""
        with pytest.raises(ValueError, match="工作流不存在"):
            orchestrator.execute_workflow(
                workflow_id=9999,
                inputs={},
                user_id=test_user.id,
            )

    def test_execute_workflow_records_execution(
        self, orchestrator, test_user, db_session
    ):
        """测试执行结果被记录到数据库。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": []},
            user_id=test_user.id,
        )

        records = db_session.query(WorkflowExecution).all()
        assert len(records) == 1
        record = records[0]
        assert record.workflow_id == created.id
        assert record.user_id == test_user.id
        assert record.status == "completed"
        assert record.error is None
        assert record.outputs is not None
        assert record.started_at is not None
        assert record.completed_at is not None

    def test_execute_workflow_failure_records_error(
        self, orchestrator, mock_decision_engine, test_user, db_session
    ):
        """测试执行失败时记录错误信息并更新状态为 failed。"""
        # 构造一个会失败的工作流：决策引擎抛出异常
        mock_decision_engine.summarize.side_effect = RuntimeError("LLM 服务不可用")
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": []},
            user_id=test_user.id,
        )

        assert result.status == "failed"
        assert "LLM 服务不可用" in result.error

        # 验证数据库记录
        record = db_session.query(WorkflowExecution).first()
        assert record.status == "failed"
        assert "LLM 服务不可用" in record.error

    def test_execute_workflow_no_deps_raises(
        self, orchestrator_no_deps, test_user
    ):
        """测试缺少依赖时执行节点抛出异常。"""
        created = orchestrator_no_deps.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        result = orchestrator_no_deps.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": []},
            user_id=test_user.id,
        )

        # 缺少决策引擎应导致失败
        assert result.status == "failed"
        assert "决策引擎未配置" in result.error

    def test_execute_workflow_conditional_edge(
        self, orchestrator, mock_tool_executor, test_user
    ):
        """测试带条件的边：工具成功后执行总结节点。"""
        workflow_data = WorkflowCreate(
            name="条件工作流",
            description="工具成功后执行总结",
            nodes=[
                WorkflowNode(
                    name="tool_node",
                    type="tool",
                    config={"tool_name": "calc", "arguments": {}},
                ),
                WorkflowNode(
                    name="summary_node",
                    type="summary",
                    config={},
                ),
            ],
            edges=[
                WorkflowEdge(
                    source="tool_node",
                    target="summary_node",
                    condition="success",
                ),
            ],
        )
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=workflow_data
        )

        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": [{"role": "user", "content": "test"}]},
            user_id=test_user.id,
        )

        assert result.status == "completed"
        # 工具成功，应执行总结节点
        assert "summary_node" in result.outputs["nodes"]
        assert "tool_node" in result.outputs["nodes"]

    def test_execute_workflow_conditional_edge_not_traversed(
        self, orchestrator, mock_tool_executor, test_user
    ):
        """测试带条件的边：工具失败时不执行总结节点。"""
        # 让工具执行失败
        mock_tool_executor.execute.return_value = ToolExecutionResult(
            tool_id=1,
            success=False,
            error="工具执行出错",
            execution_time=0.01,
        )
        workflow_data = WorkflowCreate(
            name="条件工作流-失败",
            description="工具失败后不执行总结",
            nodes=[
                WorkflowNode(
                    name="tool_node",
                    type="tool",
                    config={"tool_name": "calc", "arguments": {}},
                ),
                WorkflowNode(
                    name="summary_node",
                    type="summary",
                    config={},
                ),
            ],
            edges=[
                WorkflowEdge(
                    source="tool_node",
                    target="summary_node",
                    condition="success",
                ),
            ],
        )
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=workflow_data
        )

        result = orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": []},
            user_id=test_user.id,
        )

        assert result.status == "completed"
        # 工具节点执行了
        assert "tool_node" in result.outputs["nodes"]
        assert result.outputs["nodes"]["tool_node"]["success"] is False
        # 总结节点不应被执行（条件不满足）
        assert "summary_node" not in result.outputs["nodes"]


# ----------------------------- 执行历史测试 -----------------------------
class TestWorkflowExecutions:
    """工作流执行历史相关测试。"""

    def test_get_executions(
        self, orchestrator, mock_decision_engine, test_user
    ):
        """测试获取执行历史。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        # 执行 3 次工作流
        for _ in range(3):
            orchestrator.execute_workflow(
                workflow_id=created.id,
                inputs={"messages": []},
                user_id=test_user.id,
            )

        # 获取全部执行历史
        result = orchestrator.get_executions(workflow_id=created.id, page=1, limit=20)
        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["page"] == 1
        assert result["limit"] == 20

        # 验证每条记录的状态
        for item in result["items"]:
            assert item.workflow_id == created.id
            assert item.status == "completed"
            assert item.started_at is not None

        # 分页：第 1 页 2 条
        result = orchestrator.get_executions(workflow_id=created.id, page=1, limit=2)
        assert result["total"] == 3
        assert len(result["items"]) == 2

        # 分页：第 2 页 2 条（只剩 1 条）
        result = orchestrator.get_executions(workflow_id=created.id, page=2, limit=2)
        assert result["total"] == 3
        assert len(result["items"]) == 1

    def test_get_executions_empty(self, orchestrator, test_user):
        """测试获取无执行记录的工作流历史。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        result = orchestrator.get_executions(workflow_id=created.id)
        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_get_executions_includes_failed(
        self, orchestrator, mock_decision_engine, test_user
    ):
        """测试执行历史包含失败记录。"""
        created = orchestrator.create_workflow(
            user_id=test_user.id, workflow=_make_simple_workflow()
        )

        # 第一次执行成功
        orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": []},
            user_id=test_user.id,
        )

        # 第二次执行失败
        mock_decision_engine.summarize.side_effect = RuntimeError("失败")
        orchestrator.execute_workflow(
            workflow_id=created.id,
            inputs={"messages": []},
            user_id=test_user.id,
        )

        result = orchestrator.get_executions(workflow_id=created.id)
        assert result["total"] == 2

        statuses = [item.status for item in result["items"]]
        assert "completed" in statuses
        assert "failed" in statuses

        # 验证失败记录有错误信息
        failed_items = [item for item in result["items"] if item.status == "failed"]
        assert len(failed_items) == 1
        assert failed_items[0].error is not None
        assert "失败" in failed_items[0].error


if __name__ == "__main__":
    unittest.main()

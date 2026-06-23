"""技能管理模块单元测试 - 使用 mock 测试 LLM 调用，不实际调用 OpenAI API。"""
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
from src.db.models import Skill, SkillExecution, User
from src.llm.schemas import ChatCompletionResponse
from src.skills.schemas import (
    SkillCreate,
    SkillTrainRequest,
    SkillUpdate,
)
from src.skills.service import SkillManager


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
        username="skill_tester",
        email="skill_tester@example.com",
        hashed_password="fake-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def mock_llm_service():
    """创建 mock LLM 服务实例。"""
    service = MagicMock()
    # 默认返回一个带 content 的响应
    response = ChatCompletionResponse(
        id="chatcmpl-skill-test",
        model="gpt-4o-mini",
        content="这是技能执行结果。",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    service.chat_completion.return_value = response
    return service


@pytest.fixture()
def skill_manager(db_session, mock_llm_service):
    """创建带 mock LLM 的技能管理器实例。"""
    return SkillManager(db_session, llm_service=mock_llm_service)


@pytest.fixture()
def skill_manager_no_llm(db_session):
    """创建不带 LLM 服务的技能管理器实例。"""
    return SkillManager(db_session, llm_service=None)


def _make_skill_create(
    name: str = "翻译技能",
    description: str = "将中文翻译为英文",
    prompt: str = "你是一个专业翻译，请将用户输入的中文翻译为英文。",
) -> SkillCreate:
    """构造 SkillCreate 实例。"""
    return SkillCreate(
        name=name,
        description=description,
        prompt=prompt,
    )


# ----------------------------- 技能 CRUD 测试 -----------------------------
class TestSkillCRUD:
    """技能增删改查相关测试。"""

    def test_create_skill(self, skill_manager, test_user):
        """测试创建技能。"""
        skill_data = _make_skill_create()
        response = skill_manager.create_skill(
            user_id=test_user.id, skill=skill_data
        )

        assert response.id is not None
        assert response.user_id == test_user.id
        assert response.name == "翻译技能"
        assert response.description == "将中文翻译为英文"
        assert response.prompt == "你是一个专业翻译，请将用户输入的中文翻译为英文。"
        assert response.is_enabled is True
        assert response.created_at is not None

    def test_get_skill(self, skill_manager, test_user):
        """测试获取技能。"""
        skill_data = _make_skill_create()
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=skill_data
        )

        fetched = skill_manager.get_skill(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name
        assert fetched.prompt == created.prompt
        assert fetched.is_enabled is True

    def test_get_skill_not_found(self, skill_manager):
        """测试获取不存在的技能返回 None。"""
        assert skill_manager.get_skill(9999) is None

    def test_get_skills(self, skill_manager, test_user):
        """测试获取技能列表（含分页）。"""
        # 用户 1 创建 5 个技能
        for i in range(5):
            skill_manager.create_skill(
                user_id=test_user.id,
                skill=_make_skill_create(name=f"技能{i}"),
            )
        # 用户 2 创建 2 个技能
        other_user = User(
            username="other",
            email="other@example.com",
            hashed_password="fake-hash",
            is_active=True,
        )
        skill_manager.db.add(other_user)
        skill_manager.db.commit()
        skill_manager.db.refresh(other_user)
        for i in range(2):
            skill_manager.create_skill(
                user_id=other_user.id,
                skill=_make_skill_create(name=f"用户2技能{i}"),
            )

        # 获取用户 1 全部技能
        result = skill_manager.get_skills(user_id=test_user.id, page=1, limit=20)
        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["limit"] == 20

        # 分页：第 1 页 2 条
        result = skill_manager.get_skills(
            user_id=test_user.id, page=1, limit=2
        )
        assert result["total"] == 5
        assert len(result["items"]) == 2

        # 分页：第 3 页 2 条（只剩 1 条）
        result = skill_manager.get_skills(
            user_id=test_user.id, page=3, limit=2
        )
        assert result["total"] == 5
        assert len(result["items"]) == 1

        # 用户隔离：用户 2 只有 2 个技能
        result = skill_manager.get_skills(user_id=other_user.id)
        assert result["total"] == 2

    def test_update_skill(self, skill_manager, test_user):
        """测试更新技能。"""
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=_make_skill_create(name="原名")
        )

        # 更新名称和描述
        updated = skill_manager.update_skill(
            created.id,
            SkillUpdate(name="新名称", description="新描述"),
        )
        assert updated.name == "新名称"
        assert updated.description == "新描述"
        # 未更新的字段保持原值
        assert updated.is_enabled is True

        # 更新启用状态
        updated = skill_manager.update_skill(
            created.id, SkillUpdate(is_enabled=False)
        )
        assert updated.is_enabled is False
        assert updated.name == "新名称"

    def test_update_skill_not_found(self, skill_manager):
        """测试更新不存在的技能抛出异常。"""
        with pytest.raises(ValueError, match="技能不存在"):
            skill_manager.update_skill(9999, SkillUpdate(name="x"))

    def test_delete_skill(self, skill_manager, test_user):
        """测试删除技能。"""
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=_make_skill_create(name="待删除")
        )

        result = skill_manager.delete_skill(created.id)
        assert result is True

        # 验证已删除
        assert skill_manager.get_skill(created.id) is None

    def test_delete_skill_not_found(self, skill_manager):
        """测试删除不存在的技能返回 False。"""
        assert skill_manager.delete_skill(9999) is False


# ----------------------------- 技能执行测试 -----------------------------
class TestSkillExecution:
    """技能执行相关测试。"""

    def test_execute_skill_mock(self, skill_manager, mock_llm_service, test_user):
        """使用 mock LLM 执行技能。"""
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=_make_skill_create()
        )

        result = skill_manager.execute_skill(
            skill_id=created.id,
            input_text="你好，世界",
            user_id=test_user.id,
        )

        assert result.skill_id == created.id
        assert result.success is True
        assert result.output == "这是技能执行结果。"
        assert result.error is None
        assert result.execution_time >= 0

        # 验证 LLM 被调用一次
        mock_llm_service.chat_completion.assert_called_once()
        call_args = mock_llm_service.chat_completion.call_args
        llm_request = call_args.args[0]
        # 验证提示词构建正确
        expected_prompt = (
            "你是一个专业翻译，请将用户输入的中文翻译为英文。"
            "\n\n用户输入: 你好，世界"
        )
        assert llm_request.messages[0].content == expected_prompt
        # 验证 user_id 和 session_id 传递
        assert call_args.kwargs["user_id"] == test_user.id

    def test_execute_skill_records_execution(
        self, skill_manager, test_user, db_session
    ):
        """测试执行结果被记录到数据库。"""
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=_make_skill_create()
        )

        skill_manager.execute_skill(
            skill_id=created.id,
            input_text="测试输入",
            user_id=test_user.id,
        )

        records = db_session.query(SkillExecution).all()
        assert len(records) == 1
        record = records[0]
        assert record.skill_id == created.id
        assert record.user_id == test_user.id
        assert record.success is True
        assert record.error_message is None
        assert record.execution_time is not None

    def test_execute_skill_not_found(self, skill_manager, test_user):
        """测试执行不存在的技能。"""
        result = skill_manager.execute_skill(
            skill_id=9999,
            input_text="测试",
            user_id=test_user.id,
        )

        assert result.skill_id == 9999
        assert result.success is False
        assert "技能不存在" in result.error
        assert result.output is None

    def test_execute_skill_disabled(self, skill_manager, test_user):
        """测试执行已禁用的技能。"""
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=_make_skill_create()
        )
        # 禁用技能
        skill_manager.update_skill(created.id, SkillUpdate(is_enabled=False))

        result = skill_manager.execute_skill(
            skill_id=created.id,
            input_text="测试",
            user_id=test_user.id,
        )

        assert result.skill_id == created.id
        assert result.success is False
        assert "技能已禁用" in result.error
        assert result.output is None

    def test_execute_skill_no_llm(self, skill_manager_no_llm, test_user):
        """测试未配置 LLM 服务时执行技能返回错误。"""
        created = skill_manager_no_llm.create_skill(
            user_id=test_user.id, skill=_make_skill_create()
        )

        result = skill_manager_no_llm.execute_skill(
            skill_id=created.id,
            input_text="测试",
            user_id=test_user.id,
        )

        assert result.skill_id == created.id
        assert result.success is False
        assert "LLM 服务未配置" in result.error

    def test_execute_skill_llm_exception(
        self, skill_manager, mock_llm_service, test_user
    ):
        """测试 LLM 调用异常时返回失败结果。"""
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=_make_skill_create()
        )
        mock_llm_service.chat_completion.side_effect = RuntimeError("API 超时")

        result = skill_manager.execute_skill(
            skill_id=created.id,
            input_text="测试",
            user_id=test_user.id,
        )

        assert result.success is False
        assert "API 超时" in result.error


# ----------------------------- 技能学习测试 -----------------------------
class TestSkillTraining:
    """技能学习相关测试。"""

    def test_train_skill_mock(self, skill_manager, mock_llm_service, test_user):
        """使用 mock LLM 训练技能。"""
        # 设置 mock 返回生成的提示词
        generated_prompt = "你是一个总结助手，请将用户输入的文本总结为要点。"
        mock_llm_service.chat_completion.return_value = ChatCompletionResponse(
            id="chatcmpl-train-test",
            model="gpt-4o-mini",
            content=generated_prompt,
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80,
        )

        execution_history = [
            {"input": "长文本1...", "output": "要点1"},
            {"input": "长文本2...", "output": "要点2"},
        ]
        request = SkillTrainRequest(
            execution_history=execution_history,
            skill_name="总结技能",
            description="将长文本总结为要点",
        )

        response = skill_manager.train_skill(request, user_id=test_user.id)

        assert response.id is not None
        assert response.user_id == test_user.id
        assert response.name == "总结技能"
        assert response.description == "将长文本总结为要点"
        assert response.prompt == generated_prompt
        assert response.is_enabled is True

        # 验证 LLM 被调用
        mock_llm_service.chat_completion.assert_called_once()
        call_args = mock_llm_service.chat_completion.call_args
        llm_request = call_args.args[0]
        # 验证系统消息和用户消息存在
        assert len(llm_request.messages) == 2
        assert llm_request.messages[0].role == "system"
        assert llm_request.messages[1].role == "user"
        # 验证执行历史被传入
        assert "总结技能" in llm_request.messages[1].content

    def test_train_skill_no_llm(self, skill_manager_no_llm, test_user):
        """测试未配置 LLM 服务时训练技能抛出异常。"""
        request = SkillTrainRequest(
            execution_history=[],
            skill_name="测试技能",
        )

        with pytest.raises(ValueError, match="LLM 服务未配置"):
            skill_manager_no_llm.train_skill(request, user_id=test_user.id)

    def test_train_skill_saves_training_data(
        self, skill_manager, mock_llm_service, test_user, db_session
    ):
        """测试训练技能时保存训练数据。"""
        mock_llm_service.chat_completion.return_value = ChatCompletionResponse(
            id="chatcmpl-train-data",
            model="gpt-4o-mini",
            content="生成的提示词",
            prompt_tokens=10,
            completion_tokens=10,
            total_tokens=20,
        )

        execution_history = [
            {"input": "输入1", "output": "输出1"},
        ]
        request = SkillTrainRequest(
            execution_history=execution_history,
            skill_name="新技能",
        )

        response = skill_manager.train_skill(request, user_id=test_user.id)

        # 验证训练数据被保存到数据库
        import json
        skill_entry = db_session.query(Skill).filter(Skill.id == response.id).first()
        assert skill_entry is not None
        assert skill_entry.training_data is not None
        saved_history = json.loads(skill_entry.training_data)
        assert saved_history == execution_history


# ----------------------------- 提示词构建测试 -----------------------------
class TestSkillPrompt:
    """技能提示词构建相关测试。"""

    def test_get_skill_prompt(self, skill_manager, test_user):
        """测试验证技能提示词构建。"""
        skill_data = SkillCreate(
            name="测试技能",
            description="测试描述",
            prompt="你是一个助手。",
        )
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=skill_data
        )

        # 从数据库获取原始 Skill 对象
        skill_obj = (
            skill_manager.db.query(Skill)
            .filter(Skill.id == created.id)
            .first()
        )
        prompt = skill_manager.get_skill_prompt(skill_obj, "用户的问题")

        assert prompt == "你是一个助手。\n\n用户输入: 用户的问题"

    def test_get_skill_prompt_empty_prompt(self, skill_manager, test_user):
        """测试技能 prompt 为空时的提示词构建。"""
        skill_data = SkillCreate(
            name="空提示词技能",
            description="测试",
            prompt=None,
        )
        created = skill_manager.create_skill(
            user_id=test_user.id, skill=skill_data
        )

        skill_obj = (
            skill_manager.db.query(Skill)
            .filter(Skill.id == created.id)
            .first()
        )
        prompt = skill_manager.get_skill_prompt(skill_obj, "用户输入")

        # prompt 为 None 时应被当作空字符串处理
        assert prompt == "\n\n用户输入: 用户输入"


if __name__ == "__main__":
    unittest.main()

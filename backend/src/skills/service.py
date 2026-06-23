"""技能管理服务模块 - 提供技能的注册、执行和学习闭环功能。"""
import json
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.db.models import Skill, SkillExecution
from src.llm.schemas import ChatCompletionRequest, ChatMessage
from src.llm.service import LLMService
from src.monitoring.logger import Logger
from src.skills.schemas import (
    SkillCreate,
    SkillExecutionResult,
    SkillResponse,
    SkillTrainRequest,
    SkillUpdate,
)


class SkillManager:
    """技能管理器，封装技能注册、执行和学习相关业务逻辑。"""

    def __init__(self, db: Session, llm_service: Optional[LLMService] = None):
        """初始化技能管理器。

        Args:
            db: SQLAlchemy 数据库会话。
            llm_service: 可选的 LLM 服务实例，用于技能执行和学习。
        """
        self.db = db
        self.llm_service = llm_service
        # 使用当前数据库会话初始化日志记录器，便于记录技能相关日志
        self.logger = Logger(db=db)

    def create_skill(self, user_id: int, skill: SkillCreate) -> SkillResponse:
        """注册新技能。

        Args:
            user_id: 用户 ID。
            skill: 技能创建数据。

        Returns:
            创建的技能信息。
        """
        entry = Skill(
            user_id=user_id,
            name=skill.name,
            description=skill.description,
            prompt=skill.prompt,
            is_enabled=True,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        self.logger.log_system(
            log_type="event",
            module="skills",
            action="create_skill",
            details={"skill_id": entry.id, "name": skill.name},
            user_id=user_id,
        )

        return SkillResponse.model_validate(entry)

    def get_skill(self, skill_id: int) -> Optional[SkillResponse]:
        """获取单个技能。

        Args:
            skill_id: 技能 ID。

        Returns:
            技能信息，若不存在返回 None。
        """
        entry = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if entry is None:
            return None
        return SkillResponse.model_validate(entry)

    def get_skills(self, user_id: int, page: int = 1, limit: int = 20) -> Dict:
        """获取用户技能列表（分页）。

        Args:
            user_id: 用户 ID。
            page: 页码，从 1 开始。
            limit: 每页数量。

        Returns:
            包含 items、total、page、limit 的分页字典。
        """
        query = self.db.query(Skill).filter(Skill.user_id == user_id)
        total = query.count()
        items = (
            query.order_by(Skill.created_at.desc(), Skill.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {
            "items": [SkillResponse.model_validate(item) for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def update_skill(self, skill_id: int, update: SkillUpdate) -> SkillResponse:
        """更新技能信息。

        Args:
            skill_id: 技能 ID。
            update: 更新数据。

        Returns:
            更新后的技能信息。

        Raises:
            ValueError: 技能不存在。
        """
        entry = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if entry is None:
            raise ValueError("技能不存在")

        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        self.db.commit()
        self.db.refresh(entry)

        self.logger.log_system(
            log_type="event",
            module="skills",
            action="update_skill",
            details={"skill_id": skill_id, "fields": list(update_data.keys())},
            user_id=entry.user_id,
        )

        return SkillResponse.model_validate(entry)

    def delete_skill(self, skill_id: int) -> bool:
        """删除技能。

        Args:
            skill_id: 技能 ID。

        Returns:
            删除成功返回 True，技能不存在返回 False。
        """
        entry = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if entry is None:
            return False

        user_id = entry.user_id
        self.db.delete(entry)
        self.db.commit()

        self.logger.log_system(
            log_type="event",
            module="skills",
            action="delete_skill",
            details={"skill_id": skill_id},
            user_id=user_id,
        )

        return True

    def execute_skill(
        self,
        skill_id: int,
        input_text: str,
        user_id: int,
        session_id: Optional[int] = None,
    ) -> SkillExecutionResult:
        """执行技能。

        流程：获取技能定义 -> 构建提示词 -> 调用 LLM -> 记录执行结果 -> 返回结果。

        Args:
            skill_id: 技能 ID。
            input_text: 用户输入文本。
            user_id: 用户 ID。
            session_id: 关联的会话 ID。

        Returns:
            技能执行结果。
        """
        start_time = time.time()

        # 获取技能定义
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if skill is None:
            execution_time = time.time() - start_time
            return SkillExecutionResult(
                skill_id=skill_id,
                success=False,
                error="技能不存在",
                execution_time=execution_time,
            )

        # 检查技能是否启用
        if not skill.is_enabled:
            execution_time = time.time() - start_time
            error_msg = "技能已禁用"
            self._record_execution(
                skill_id, user_id, session_id, input_text,
                None, False, error_msg, execution_time,
            )
            return SkillExecutionResult(
                skill_id=skill_id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

        # 检查 LLM 服务是否可用
        if self.llm_service is None:
            execution_time = time.time() - start_time
            error_msg = "LLM 服务未配置"
            self._record_execution(
                skill_id, user_id, session_id, input_text,
                None, False, error_msg, execution_time,
            )
            return SkillExecutionResult(
                skill_id=skill_id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

        # 构建提示词并调用 LLM
        prompt = self.get_skill_prompt(skill, input_text)
        try:
            request = ChatCompletionRequest(
                messages=[ChatMessage(role="user", content=prompt)],
            )
            response = self.llm_service.chat_completion(
                request, user_id=user_id, session_id=session_id
            )
            output = response.content
            execution_time = time.time() - start_time

            self._record_execution(
                skill_id, user_id, session_id, input_text,
                output, True, None, execution_time,
            )

            self.logger.log_system(
                log_type="event",
                module="skills",
                action="execute_skill",
                details={"skill_id": skill_id, "success": True},
                user_id=user_id,
                session_id=session_id,
            )

            return SkillExecutionResult(
                skill_id=skill_id,
                success=True,
                output=output,
                execution_time=execution_time,
            )
        except Exception as exc:  # noqa: BLE001
            execution_time = time.time() - start_time
            error_msg = str(exc)
            self._record_execution(
                skill_id, user_id, session_id, input_text,
                None, False, error_msg, execution_time,
            )
            return SkillExecutionResult(
                skill_id=skill_id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

    def train_skill(self, request: SkillTrainRequest, user_id: int) -> SkillResponse:
        """技能学习 - 分析执行历史并生成新技能。

        流程：分析执行历史 -> 调用 LLM 生成技能 prompt -> 创建新技能。

        Args:
            request: 技能训练请求，包含执行历史和技能信息。
            user_id: 用户 ID。

        Returns:
            新创建的技能信息。

        Raises:
            ValueError: LLM 服务未配置。
        """
        if self.llm_service is None:
            raise ValueError("LLM 服务未配置，无法进行技能学习")

        # 构建分析提示词，将执行历史传给 LLM 分析
        history_json = json.dumps(request.execution_history, ensure_ascii=False)
        system_prompt = (
            "你是一个技能学习助手。请分析以下技能执行历史，"
            "总结出通用的技能提示词模板。"
            "提示词模板应能指导 AI 完成类似任务。"
            "请直接输出提示词内容，不要包含其他说明。"
        )
        user_content = (
            f"技能名称: {request.skill_name}\n"
            f"技能描述: {request.description or '无'}\n"
            f"执行历史:\n{history_json}"
        )

        llm_request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_content),
            ],
        )
        response = self.llm_service.chat_completion(
            llm_request, user_id=user_id, session_id=None
        )
        generated_prompt = response.content

        # 创建新技能，将执行历史保存为训练数据
        entry = Skill(
            user_id=user_id,
            name=request.skill_name,
            description=request.description,
            prompt=generated_prompt,
            is_enabled=True,
            training_data=history_json,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        self.logger.log_system(
            log_type="event",
            module="skills",
            action="train_skill",
            details={
                "skill_id": entry.id,
                "skill_name": request.skill_name,
                "history_count": len(request.execution_history),
            },
            user_id=user_id,
        )

        return SkillResponse.model_validate(entry)

    def get_skill_prompt(self, skill: Skill, input_text: str) -> str:
        """构建技能执行提示词。

        Args:
            skill: 技能对象。
            input_text: 用户输入文本。

        Returns:
            拼接后的提示词：技能 prompt + 用户输入。
        """
        skill_prompt = skill.prompt or ""
        return f"{skill_prompt}\n\n用户输入: {input_text}"

    def _record_execution(
        self,
        skill_id: int,
        user_id: int,
        session_id: Optional[int],
        input_text: str,
        output: Optional[str],
        success: bool,
        error: Optional[str],
        execution_time: float,
    ) -> None:
        """记录技能执行结果到数据库。

        数据库记录失败不应影响执行结果返回，因此使用 try/except 保护。
        """
        input_json = json.dumps({"input": input_text}, ensure_ascii=False)
        output_json = (
            json.dumps({"output": output}, ensure_ascii=False) if output else None
        )

        try:
            execution = SkillExecution(
                skill_id=skill_id,
                user_id=user_id,
                session_id=session_id,
                input_data=input_json,
                output_data=output_json,
                success=success,
                error_message=error,
                execution_time=execution_time,
            )
            self.db.add(execution)
            self.db.commit()
        except Exception:  # noqa: BLE001
            # 记录失败不应影响执行结果
            self.db.rollback()

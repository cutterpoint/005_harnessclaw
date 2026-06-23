"""技能管理模块 - 提供技能注册、执行和学习闭环功能。"""
from src.skills.schemas import (
    SkillCreate,
    SkillExecutionRequest,
    SkillExecutionResult,
    SkillResponse,
    SkillTrainRequest,
    SkillUpdate,
)
from src.skills.service import SkillManager

__all__ = [
    "SkillManager",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "SkillExecutionRequest",
    "SkillExecutionResult",
    "SkillTrainRequest",
]

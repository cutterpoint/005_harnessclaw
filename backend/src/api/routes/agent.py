"""Agent 路由模块 - 发起对话与获取 Agent 状态。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.agent.engine import AgentEngine
from src.agent.schemas import AgentRunRequest
from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import User
from src.decision.engine import DecisionEngine
from src.llm.service import LLMService
from src.memory.manager import MemorySystem
from src.prompt.builder import PromptBuilder
from src.session.service import SessionManager
from src.skills.service import SkillManager
from src.tools.executor import ToolExecutor
from src.workflow.orchestrator import WorkflowOrchestrator

router = APIRouter()


def get_agent_engine(db: Session) -> AgentEngine:
    """工厂函数：创建 AgentEngine 及其所有依赖。

    Args:
        db: 数据库会话。

    Returns:
        初始化完成的 AgentEngine 实例。
    """
    # 创建 LLM 服务
    llm_service = LLMService(db)

    # 创建工具执行器
    tool_executor = ToolExecutor(db)

    # 创建会话管理器
    session_manager = SessionManager(db)

    # 创建技能管理器
    skill_manager = SkillManager(db, llm_service=llm_service)

    # 创建记忆系统（向量库依赖缺失时降级为 None）
    try:
        memory_system = MemorySystem(db)
    except Exception:  # noqa: BLE001
        memory_system = None

    # 创建提示词构建器
    prompt_builder = PromptBuilder(
        memory_system=memory_system,
        tool_executor=tool_executor,
        skill_manager=skill_manager,
    )

    # 创建决策引擎
    decision_engine = DecisionEngine(
        llm_service=llm_service,
        prompt_builder=prompt_builder,
        tool_executor=tool_executor,
    )

    # 创建工作流编排器
    workflow_orchestrator = WorkflowOrchestrator(
        db=db,
        decision_engine=decision_engine,
        tool_executor=tool_executor,
        skill_manager=skill_manager,
    )

    # 创建并返回 Agent 引擎
    return AgentEngine(
        db=db,
        decision_engine=decision_engine,
        memory_system=memory_system,
        prompt_builder=prompt_builder,
        session_manager=session_manager,
        workflow_orchestrator=workflow_orchestrator,
    )


@router.post("/chat")
async def chat(
    body: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发起对话，由 Agent 引擎处理。"""
    # 注入当前用户 ID
    request = AgentRunRequest(
        message=body.message,
        session_id=body.session_id,
        user_id=current_user.id,
    )
    engine = get_agent_engine(db)
    response = await engine.run(request)
    return success_response(
        data=response.model_dump(mode="json"), message="success"
    )


@router.get("/status/{session_id}")
def get_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 Agent 状态。"""
    engine = get_agent_engine(db)
    agent_status = engine.get_status(session_id)
    return success_response(
        data=agent_status.model_dump(mode="json"), message="success"
    )

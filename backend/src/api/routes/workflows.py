"""工作流路由模块 - 工作流的 CRUD、执行与执行历史查询。"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import User
from src.workflow.orchestrator import WorkflowOrchestrator
from src.workflow.schemas import WorkflowCreate, WorkflowUpdate

router = APIRouter()


@router.post("")
def create_workflow(
    body: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建工作流。"""
    orchestrator = WorkflowOrchestrator(db)
    workflow = orchestrator.create_workflow(
        user_id=current_user.id, workflow=body
    )
    return success_response(
        data=workflow.model_dump(mode="json"), message="创建成功"
    )


@router.get("")
def list_workflows(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的工作流列表。"""
    orchestrator = WorkflowOrchestrator(db)
    result = orchestrator.get_workflows(
        user_id=current_user.id, page=page, limit=limit
    )
    data = {
        "items": [item.model_dump(mode="json") for item in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
    }
    return success_response(data=data, message="success")


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个工作流。"""
    orchestrator = WorkflowOrchestrator(db)
    workflow = orchestrator.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )
    if workflow.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该工作流",
        )
    return success_response(
        data=workflow.model_dump(mode="json"), message="success"
    )


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: int,
    body: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新工作流。"""
    orchestrator = WorkflowOrchestrator(db)
    existing = orchestrator.get_workflow(workflow_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该工作流",
        )
    try:
        updated = orchestrator.update_workflow(workflow_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(
        data=updated.model_dump(mode="json"), message="更新成功"
    )


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除工作流。"""
    orchestrator = WorkflowOrchestrator(db)
    existing = orchestrator.get_workflow(workflow_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该工作流",
        )
    orchestrator.delete_workflow(workflow_id)
    return success_response(data=None, message="删除成功")


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: int,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """执行工作流。"""
    orchestrator = WorkflowOrchestrator(db)
    existing = orchestrator.get_workflow(workflow_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权执行该工作流",
        )
    try:
        result = orchestrator.execute_workflow(
            workflow_id=workflow_id,
            inputs=body,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(
        data=result.model_dump(mode="json"), message="success"
    )


@router.get("/{workflow_id}/executions")
def get_executions(
    workflow_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取工作流执行历史。"""
    orchestrator = WorkflowOrchestrator(db)
    existing = orchestrator.get_workflow(workflow_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该工作流",
        )
    result = orchestrator.get_executions(
        workflow_id=workflow_id, page=page, limit=limit
    )
    data = {
        "items": [item.model_dump(mode="json") for item in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
    }
    return success_response(data=data, message="success")

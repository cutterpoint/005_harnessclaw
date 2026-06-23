"""工具路由模块 - 工具的注册、查询、更新、删除与执行。"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, success_response
from src.db.database import get_db
from src.db.models import User
from src.tools.executor import ToolExecutor
from src.tools.registry import ToolRegistry
from src.tools.schemas import ToolCreate, ToolResponse, ToolUpdate

router = APIRouter()


def _tool_to_dict(tool) -> Dict[str, Any]:
    """将 Tool ORM 对象转为响应字典。"""
    response = ToolResponse.model_validate(tool)
    return response.model_dump(mode="json")


@router.post("")
def register_tool(
    body: ToolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """注册工具。"""
    registry = ToolRegistry(db)
    try:
        tool = registry.register(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(data=_tool_to_dict(tool), message="注册成功")


@router.get("")
def list_tools(
    enabled_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取工具列表。"""
    registry = ToolRegistry(db)
    tools = registry.list(enabled_only=enabled_only)
    data = [_tool_to_dict(t) for t in tools]
    return success_response(data=data, message="success")


@router.get("/{tool_id}")
def get_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个工具。"""
    registry = ToolRegistry(db)
    tool = registry.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在",
        )
    return success_response(data=_tool_to_dict(tool), message="success")


@router.put("/{tool_id}")
def update_tool(
    tool_id: int,
    body: ToolUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新工具。"""
    registry = ToolRegistry(db)
    try:
        tool = registry.update(tool_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return success_response(data=_tool_to_dict(tool), message="更新成功")


@router.delete("/{tool_id}")
def delete_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除工具。"""
    registry = ToolRegistry(db)
    deleted = registry.delete(tool_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在",
        )
    return success_response(data=None, message="删除成功")


@router.post("/{tool_id}/execute")
def execute_tool(
    tool_id: int,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """执行工具。"""
    executor = ToolExecutor(db)
    result = executor.execute_by_id(
        tool_id=tool_id,
        arguments=body,
        user_id=current_user.id,
    )
    return success_response(
        data=result.model_dump(mode="json"), message="success"
    )

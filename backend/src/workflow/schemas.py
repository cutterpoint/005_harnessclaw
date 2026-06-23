"""工作流编排模块的 Pydantic 数据模型定义。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WorkflowNode(BaseModel):
    """工作流节点定义。"""

    name: str
    type: str  # decision/tool/skill/summary
    config: Optional[Dict[str, Any]] = None


class WorkflowEdge(BaseModel):
    """工作流边定义，描述节点间的连接关系。"""

    source: str
    target: str
    condition: Optional[str] = None


class WorkflowCreate(BaseModel):
    """工作流创建请求模型。"""

    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]


class WorkflowUpdate(BaseModel):
    """工作流更新请求模型，仅更新非 None 字段。"""

    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    is_enabled: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """工作流信息响应模型。"""

    id: int
    user_id: int
    name: str
    description: Optional[str]
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecutionResult(BaseModel):
    """工作流执行结果模型。"""

    execution_id: int
    workflow_id: int
    status: str
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

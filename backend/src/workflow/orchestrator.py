"""工作流编排模块 - 管理工作流定义与执行，使用简单的节点遍历实现。"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.models import Workflow, WorkflowExecution
from src.decision.engine import DecisionEngine
from src.monitoring.logger import Logger
from src.skills.service import SkillManager
from src.tools.executor import ToolExecutor
from src.workflow.schemas import (
    WorkflowCreate,
    WorkflowEdge,
    WorkflowExecutionResult,
    WorkflowNode,
    WorkflowResponse,
    WorkflowUpdate,
)


class WorkflowOrchestrator:
    """工作流编排器，负责工作流的 CRUD 管理与节点遍历执行。"""

    def __init__(
        self,
        db: Session,
        decision_engine: Optional[DecisionEngine] = None,
        tool_executor: Optional[ToolExecutor] = None,
        skill_manager: Optional[SkillManager] = None,
    ):
        """初始化工作流编排器。

        Args:
            db: SQLAlchemy 数据库会话。
            decision_engine: 决策引擎实例（可选），用于决策与总结节点。
            tool_executor: 工具执行器实例（可选），用于工具节点。
            skill_manager: 技能管理器实例（可选），用于技能节点。
        """
        self.db = db
        self.decision_engine = decision_engine
        self.tool_executor = tool_executor
        self.skill_manager = skill_manager
        self.logger = Logger(db=db)

    # ----------------------------- 工作流 CRUD -----------------------------

    def create_workflow(
        self, user_id: int, workflow: WorkflowCreate
    ) -> WorkflowResponse:
        """创建新工作流。

        Args:
            user_id: 用户 ID。
            workflow: 工作流创建数据。

        Returns:
            创建的工作流信息。
        """
        definition = self._serialize_definition(workflow.nodes, workflow.edges)
        entry = Workflow(
            user_id=user_id,
            name=workflow.name,
            description=workflow.description,
            definition=definition,
            is_enabled=True,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        self.logger.log_system(
            log_type="event",
            module="workflow",
            action="create_workflow",
            details={"workflow_id": entry.id, "name": workflow.name},
            user_id=user_id,
        )

        return self._to_response(entry)

    def get_workflow(self, workflow_id: int) -> Optional[WorkflowResponse]:
        """获取单个工作流。

        Args:
            workflow_id: 工作流 ID。

        Returns:
            工作流信息，若不存在返回 None。
        """
        entry = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if entry is None:
            return None
        return self._to_response(entry)

    def get_workflows(
        self, user_id: int, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """获取用户工作流列表（分页）。

        Args:
            user_id: 用户 ID。
            page: 页码，从 1 开始。
            limit: 每页数量。

        Returns:
            包含 items、total、page、limit 的分页字典。
        """
        query = self.db.query(Workflow).filter(Workflow.user_id == user_id)
        total = query.count()
        items = (
            query.order_by(Workflow.created_at.desc(), Workflow.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {
            "items": [self._to_response(item) for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def update_workflow(
        self, workflow_id: int, update: WorkflowUpdate
    ) -> WorkflowResponse:
        """更新工作流信息。

        Args:
            workflow_id: 工作流 ID。
            update: 更新数据。

        Returns:
            更新后的工作流信息。

        Raises:
            ValueError: 工作流不存在。
        """
        entry = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if entry is None:
            raise ValueError("工作流不存在")

        if update.name is not None:
            entry.name = update.name
        if update.description is not None:
            entry.description = update.description
        if update.is_enabled is not None:
            entry.is_enabled = update.is_enabled
        # 节点或边有更新时，重新序列化 definition
        if update.nodes is not None or update.edges is not None:
            nodes = update.nodes if update.nodes is not None else []
            edges = update.edges if update.edges is not None else []
            entry.definition = self._serialize_definition(nodes, edges)

        self.db.commit()
        self.db.refresh(entry)

        self.logger.log_system(
            log_type="event",
            module="workflow",
            action="update_workflow",
            details={"workflow_id": workflow_id},
            user_id=entry.user_id,
        )

        return self._to_response(entry)

    def delete_workflow(self, workflow_id: int) -> bool:
        """删除工作流。

        Args:
            workflow_id: 工作流 ID。

        Returns:
            删除成功返回 True，工作流不存在返回 False。
        """
        entry = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if entry is None:
            return False

        user_id = entry.user_id
        self.db.delete(entry)
        self.db.commit()

        self.logger.log_system(
            log_type="event",
            module="workflow",
            action="delete_workflow",
            details={"workflow_id": workflow_id},
            user_id=user_id,
        )

        return True

    # ----------------------------- 工作流执行 -----------------------------

    def execute_workflow(
        self,
        workflow_id: int,
        inputs: Dict[str, Any],
        user_id: int,
        session_id: Optional[int] = None,
    ) -> WorkflowExecutionResult:
        """执行工作流。

        流程：获取工作流定义 -> 创建执行记录 -> 按节点顺序执行 -> 更新状态 -> 返回结果。

        Args:
            workflow_id: 工作流 ID。
            inputs: 输入参数字典。
            user_id: 用户 ID。
            session_id: 关联的会话 ID。

        Returns:
            工作流执行结果。
        """
        # 获取工作流定义
        entry = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if entry is None:
            raise ValueError(f"工作流不存在: id={workflow_id}")

        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            user_id=user_id,
            session_id=session_id,
            inputs=json.dumps(inputs, ensure_ascii=False),
            status="running",
            started_at=datetime.now(),
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        self.logger.log_system(
            log_type="event",
            module="workflow",
            action="execute_workflow",
            details={
                "workflow_id": workflow_id,
                "execution_id": execution.id,
            },
            user_id=user_id,
            session_id=session_id,
        )

        # 解析工作流定义
        nodes, edges = self._deserialize_definition(entry.definition)

        try:
            outputs = self._run_nodes(
                nodes, edges, inputs, user_id, session_id
            )
            # 执行成功，更新状态
            execution.status = "completed"
            execution.outputs = json.dumps(outputs, ensure_ascii=False)
            execution.completed_at = datetime.now()
            self.db.commit()
            self.db.refresh(execution)

            return WorkflowExecutionResult(
                execution_id=execution.id,
                workflow_id=workflow_id,
                status="completed",
                outputs=outputs,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
            )
        except Exception as exc:  # noqa: BLE001
            # 执行失败，记录错误并更新状态
            self.db.rollback()
            error_msg = str(exc)
            execution.status = "failed"
            execution.error = error_msg
            execution.completed_at = datetime.now()
            self.db.commit()
            self.db.refresh(execution)

            self.logger.error(
                f"工作流执行失败 workflow_id={workflow_id} "
                f"execution_id={execution.id}: {error_msg}"
            )

            return WorkflowExecutionResult(
                execution_id=execution.id,
                workflow_id=workflow_id,
                status="failed",
                error=error_msg,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
            )

    def get_executions(
        self, workflow_id: int, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """获取工作流执行历史（分页）。

        Args:
            workflow_id: 工作流 ID。
            page: 页码，从 1 开始。
            limit: 每页数量。

        Returns:
            包含 items、total、page、limit 的分页字典。
        """
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        )
        total = query.count()
        items = (
            query.order_by(
                WorkflowExecution.started_at.desc(), WorkflowExecution.id.desc()
            )
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {
            "items": [self._execution_to_result(item) for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }

    # ----------------------------- 内部方法：序列化 -----------------------------

    @staticmethod
    def _serialize_definition(
        nodes: List[WorkflowNode], edges: List[WorkflowEdge]
    ) -> str:
        """将节点和边列表序列化为 definition JSON 字符串。"""
        definition = {
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges],
        }
        return json.dumps(definition, ensure_ascii=False)

    @staticmethod
    def _deserialize_definition(
        definition: str,
    ) -> tuple[List[WorkflowNode], List[WorkflowEdge]]:
        """从 definition JSON 字符串反序列化节点和边。"""
        data = json.loads(definition)
        nodes = [WorkflowNode(**n) for n in data.get("nodes", [])]
        edges = [WorkflowEdge(**e) for e in data.get("edges", [])]
        return nodes, edges

    @staticmethod
    def _to_response(entry: Workflow) -> WorkflowResponse:
        """将 Workflow 模型转换为 WorkflowResponse。"""
        nodes, edges = WorkflowOrchestrator._deserialize_definition(entry.definition)
        return WorkflowResponse(
            id=entry.id,
            user_id=entry.user_id,
            name=entry.name,
            description=entry.description,
            nodes=nodes,
            edges=edges,
            is_enabled=entry.is_enabled,
            created_at=entry.created_at,
        )

    @staticmethod
    def _execution_to_result(execution: WorkflowExecution) -> WorkflowExecutionResult:
        """将 WorkflowExecution 模型转换为 WorkflowExecutionResult。"""
        outputs = None
        if execution.outputs:
            try:
                outputs = json.loads(execution.outputs)
            except (json.JSONDecodeError, ValueError):
                outputs = None
        return WorkflowExecutionResult(
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            outputs=outputs,
            error=execution.error,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
        )

    # ----------------------------- 内部方法：节点执行 -----------------------------

    def _run_nodes(
        self,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        inputs: Dict[str, Any],
        user_id: int,
        session_id: Optional[int],
    ) -> Dict[str, Any]:
        """按节点顺序遍历执行工作流。

        流程：找到起始节点 -> 按边遍历 -> 执行每个节点 -> 传递上下文。

        Args:
            nodes: 节点列表。
            edges: 边列表。
            inputs: 输入参数。
            user_id: 用户 ID。
            session_id: 会话 ID。

        Returns:
            包含所有节点输出的上下文字典。
        """
        # 构建节点映射
        node_map: Dict[str, WorkflowNode] = {n.name: n for n in nodes}
        # 构建邻接表：source -> [(target, condition)]
        adjacency: Dict[str, List[tuple[str, Optional[str]]]] = {
            n.name: [] for n in nodes
        }
        # 记录每个节点的入边数，用于找起始节点
        in_degree: Dict[str, int] = {n.name: 0 for n in nodes}
        for edge in edges:
            if edge.source in adjacency:
                adjacency[edge.source].append((edge.target, edge.condition))
            if edge.target in in_degree:
                in_degree[edge.target] += 1

        # 找到起始节点（入度为 0 的节点）
        start_nodes = [name for name, deg in in_degree.items() if deg == 0]
        if not start_nodes:
            # 若所有节点都有入边（存在环），则取第一个节点作为起点
            start_nodes = [nodes[0].name] if nodes else []

        # 初始化上下文：拷贝输入参数
        context: Dict[str, Any] = {
            "inputs": dict(inputs),
            "nodes": {},  # 记录每个节点的输出
        }

        # 按拓扑顺序遍历执行
        visited: set = set()
        queue: List[str] = list(start_nodes)
        iteration = 0
        max_iterations = settings.MAX_ITERATIONS * len(nodes) if nodes else settings.MAX_ITERATIONS

        while queue and iteration < max_iterations:
            iteration += 1
            current_name = queue.pop(0)
            if current_name in visited:
                continue
            visited.add(current_name)

            node = node_map.get(current_name)
            if node is None:
                continue

            # 执行当前节点
            output = self._execute_node(node, context, user_id, session_id)
            context["nodes"][current_name] = output

            # 将节点输出合并到上下文顶层（便于后续节点读取）
            if isinstance(output, dict):
                for key, value in output.items():
                    context[key] = value

            # 根据边和条件决定后续节点
            for target, condition in adjacency.get(current_name, []):
                if self._should_traverse(condition, output):
                    queue.append(target)

        return context

    def _execute_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        user_id: int,
        session_id: Optional[int],
    ) -> Dict[str, Any]:
        """根据节点类型执行单个节点。

        Args:
            node: 工作流节点。
            context: 当前上下文。
            user_id: 用户 ID。
            session_id: 会话 ID。

        Returns:
            节点输出字典。

        Raises:
            ValueError: 不支持的节点类型或缺少必要依赖。
        """
        node_type = node.type
        if node_type == "decision":
            return self._execute_decision_node(node, context, user_id, session_id)
        elif node_type == "tool":
            return self._execute_tool_node(node, context, user_id, session_id)
        elif node_type == "skill":
            return self._execute_skill_node(node, context, user_id, session_id)
        elif node_type == "summary":
            return self._execute_summary_node(node, context, user_id, session_id)
        else:
            raise ValueError(f"不支持的节点类型: {node_type}")

    def _execute_decision_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        user_id: int,
        session_id: Optional[int],
    ) -> Dict[str, Any]:
        """执行决策节点：调用 DecisionEngine.decide()。"""
        if self.decision_engine is None:
            raise ValueError("决策引擎未配置，无法执行决策节点")

        config = node.config or {}
        # 从上下文获取消息，默认使用 inputs 中的 messages
        messages = context.get("messages") or context.get("inputs", {}).get("messages", [])
        # 允许通过 config 指定消息来源
        messages_key = config.get("messages_key")
        if messages_key:
            messages = context.get(messages_key, messages)

        result = self.decision_engine.decide(
            messages, user_id=user_id, session_id=session_id
        )

        return {
            "action": result.action.model_dump() if result.action else None,
            "raw_response": result.raw_response,
            "tool_calls": result.tool_calls,
            "messages": messages,
            "success": True,
        }

    def _execute_tool_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        user_id: int,
        session_id: Optional[int],
    ) -> Dict[str, Any]:
        """执行工具节点：调用 ToolExecutor.execute()。"""
        if self.tool_executor is None:
            raise ValueError("工具执行器未配置，无法执行工具节点")

        config = node.config or {}
        tool_name = config.get("tool_name")
        if not tool_name:
            raise ValueError(f"工具节点 {node.name} 缺少 tool_name 配置")

        # 获取参数：优先使用 config 中的 arguments，否则使用上下文
        arguments = config.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}

        result = self.tool_executor.execute(
            tool_name=tool_name,
            arguments=arguments,
            user_id=user_id,
            session_id=session_id,
        )

        return {
            "tool_name": tool_name,
            "success": result.success,
            "result": result.result,
            "error": result.error,
        }

    def _execute_skill_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        user_id: int,
        session_id: Optional[int],
    ) -> Dict[str, Any]:
        """执行技能节点：调用 SkillManager.execute_skill()。"""
        if self.skill_manager is None:
            raise ValueError("技能管理器未配置，无法执行技能节点")

        config = node.config or {}
        skill_id = config.get("skill_id")
        if skill_id is None:
            raise ValueError(f"技能节点 {node.name} 缺少 skill_id 配置")

        # 获取输入文本：优先使用 config 中的 input_text，其次从上下文读取
        input_text = config.get("input_text")
        if input_text is None:
            input_key = config.get("input_key", "input")
            input_text = context.get(input_key, "")
        if not isinstance(input_text, str):
            input_text = str(input_text)

        result = self.skill_manager.execute_skill(
            skill_id=skill_id,
            input_text=input_text,
            user_id=user_id,
            session_id=session_id,
        )

        return {
            "skill_id": skill_id,
            "success": result.success,
            "output": result.output,
            "error": result.error,
        }

    def _execute_summary_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        user_id: int,
        session_id: Optional[int],
    ) -> Dict[str, Any]:
        """执行总结节点：调用 DecisionEngine.summarize()。"""
        if self.decision_engine is None:
            raise ValueError("决策引擎未配置，无法执行总结节点")

        config = node.config or {}
        # 从上下文获取消息，默认使用 inputs 中的 messages
        messages = context.get("messages") or context.get("inputs", {}).get("messages", [])
        messages_key = config.get("messages_key")
        if messages_key:
            messages = context.get(messages_key, messages)

        summary = self.decision_engine.summarize(
            messages, user_id=user_id, session_id=session_id
        )

        return {
            "summary": summary,
            "success": True,
        }

    @staticmethod
    def _should_traverse(
        condition: Optional[str], output: Dict[str, Any]
    ) -> bool:
        """判断是否应该遍历到目标节点。

        支持的 condition 取值：
        - None：无条件遍历
        - "success"：上一节点输出 success 为 True 时遍历
        - "failed"：上一节点输出 success 为 False 时遍历
        - 其他字符串：按 key==value 格式解析

        Args:
            condition: 条件字符串。
            output: 上一节点的输出。

        Returns:
            是否遍历。
        """
        if condition is None:
            return True

        if not isinstance(output, dict):
            return True

        if condition == "success":
            return bool(output.get("success", False))
        if condition == "failed":
            return not bool(output.get("success", False))

        # 支持 key==value 格式
        if "==" in condition:
            key, value = condition.split("==", 1)
            key = key.strip()
            value = value.strip()
            actual = output.get(key)
            # 尝试类型转换比较
            if actual is None:
                return False
            return str(actual) == value

        return True

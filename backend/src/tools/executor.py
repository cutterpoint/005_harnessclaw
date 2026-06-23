"""工具执行器模块 - 动态加载并执行工具，记录执行结果。"""
import importlib
import json
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models import Tool, ToolExecution
from src.monitoring.logger import Logger
from src.tools.registry import ToolRegistry
from src.tools.schemas import ToolExecutionResult
from src.tools.validator import ToolValidator


class ToolExecutor:
    """工具执行器，负责工具的动态加载、执行与结果记录。"""

    def __init__(self, db: Session):
        """初始化工具执行器。

        Args:
            db: SQLAlchemy 数据库会话。
        """
        self.db = db
        self.logger = Logger(db=db)
        self.registry = ToolRegistry(db=db)
        self.validator = ToolValidator()

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> ToolExecutionResult:
        """按名称执行工具。

        Args:
            tool_name: 工具名称。
            arguments: 调用参数字典。
            user_id: 触发执行的用户 ID。
            session_id: 关联的会话 ID。

        Returns:
            工具执行结果。
        """
        tool = self.registry.get_by_name(tool_name)
        if tool is None:
            return ToolExecutionResult(
                tool_id=0,
                success=False,
                error=f"工具不存在: {tool_name}",
                execution_time=0.0,
            )
        return self._execute_tool(tool, arguments, user_id, session_id)

    def execute_by_id(
        self,
        tool_id: int,
        arguments: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> ToolExecutionResult:
        """按 ID 执行工具。

        Args:
            tool_id: 工具 ID。
            arguments: 调用参数字典。
            user_id: 触发执行的用户 ID。
            session_id: 关联的会话 ID。

        Returns:
            工具执行结果。
        """
        tool = self.registry.get(tool_id)
        if tool is None:
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error=f"工具不存在: id={tool_id}",
                execution_time=0.0,
            )
        return self._execute_tool(tool, arguments, user_id, session_id)

    def get_tools(self) -> List[Tool]:
        """获取可用（已启用）的工具列表。"""
        return self.registry.list(enabled_only=True)

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """获取 OpenAI function calling 格式的工具列表。"""
        return [self.registry.to_openai_format(t) for t in self.get_tools()]

    # ---- 内部方法 ----

    def _execute_tool(
        self,
        tool: Tool,
        arguments: Dict[str, Any],
        user_id: Optional[int],
        session_id: Optional[int],
    ) -> ToolExecutionResult:
        """执行单个工具的完整流程：验证 -> 动态导入 -> 调用 -> 记录。"""
        start_time = time.time()

        # 检查工具是否启用
        if not tool.is_enabled:
            execution_time = time.time() - start_time
            error_msg = f"工具已禁用: {tool.name}"
            self._record_execution(
                tool.id, user_id, session_id, arguments,
                None, False, error_msg, execution_time,
            )
            return ToolExecutionResult(
                tool_id=tool.id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

        # 验证参数
        valid, errors = self.validator.validate(tool, arguments)
        if not valid:
            execution_time = time.time() - start_time
            error_msg = "; ".join(errors)
            self._record_execution(
                tool.id, user_id, session_id, arguments,
                None, False, error_msg, execution_time,
            )
            return ToolExecutionResult(
                tool_id=tool.id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

        # 动态导入模块并调用函数
        try:
            module = importlib.import_module(tool.module_path)
            func = getattr(module, tool.function_name)
            result = func(**arguments)
            execution_time = time.time() - start_time

            self._record_execution(
                tool.id, user_id, session_id, arguments,
                result, True, None, execution_time,
            )
            return ToolExecutionResult(
                tool_id=tool.id,
                success=True,
                result=result,
                execution_time=execution_time,
            )
        except Exception as exc:  # noqa: BLE001
            execution_time = time.time() - start_time
            error_msg = str(exc)
            self._record_execution(
                tool.id, user_id, session_id, arguments,
                None, False, error_msg, execution_time,
            )
            return ToolExecutionResult(
                tool_id=tool.id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

    def _record_execution(
        self,
        tool_id: int,
        user_id: Optional[int],
        session_id: Optional[int],
        arguments: Dict[str, Any],
        result: Any,
        success: bool,
        error: Optional[str],
        execution_time: float,
    ) -> None:
        """记录工具执行结果到数据库，并写入外部交互日志。

        数据库记录失败不应影响执行结果返回，因此使用 try/except 保护。
        """
        arguments_json = json.dumps(arguments, ensure_ascii=False)
        result_json = json.dumps(result, ensure_ascii=False) if result is not None else None

        # 记录外部交互日志（含工具执行情况）
        self.logger.log_external(
            service_name="tool",
            operation=f"execute:{tool_id}",
            success=success,
            request_body=arguments_json,
            response_body=result_json,
            latency_ms=int(execution_time * 1000),
            error_message=error,
            user_id=user_id,
            session_id=session_id,
        )

        # 记录工具执行记录到数据库
        try:
            execution = ToolExecution(
                tool_id=tool_id,
                user_id=user_id,
                session_id=session_id,
                arguments=arguments_json,
                result=result_json,
                success=success,
                error_message=error,
                execution_time=execution_time,
            )
            self.db.add(execution)
            self.db.commit()
        except Exception:  # noqa: BLE001
            # 记录失败不应影响执行结果
            self.db.rollback()

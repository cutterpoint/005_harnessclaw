"""工具注册表模块 - 管理工具的注册、查询、更新和删除。"""
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models import Tool
from src.monitoring.logger import Logger
from src.tools.schemas import ToolCreate, ToolUpdate


class ToolRegistry:
    """工具注册表，封装工具的 CRUD 操作与格式转换。"""

    def __init__(self, db: Session):
        """初始化工具注册表。

        Args:
            db: SQLAlchemy 数据库会话。
        """
        self.db = db
        self.logger = Logger(db=db)

    def register(self, tool: ToolCreate) -> Tool:
        """注册新工具，检查名称唯一性。

        Args:
            tool: 工具创建数据。

        Returns:
            创建成功的工具 ORM 对象。

        Raises:
            ValueError: 工具名称已存在。
        """
        # 检查名称唯一性
        if self.get_by_name(tool.name):
            self.logger.log_system(
                log_type="event",
                module="tools",
                action="register_failed",
                details={"reason": "duplicate_name", "name": tool.name},
            )
            raise ValueError(f"工具名称已存在: {tool.name}")

        # 序列化参数为 JSON 字符串存储
        db_tool = Tool(
            name=tool.name,
            description=tool.description,
            function_name=tool.function_name,
            module_path=tool.module_path,
            parameters=json.dumps(
                [p.model_dump() for p in tool.parameters], ensure_ascii=False
            ),
            return_type=tool.return_type,
            is_enabled=True,
        )
        self.db.add(db_tool)
        self.db.commit()
        self.db.refresh(db_tool)

        self.logger.log_system(
            log_type="event",
            module="tools",
            action="register_success",
            details={"tool_id": db_tool.id, "name": db_tool.name},
        )
        return db_tool

    def get(self, tool_id: int) -> Optional[Tool]:
        """根据 ID 获取工具。"""
        return self.db.query(Tool).filter(Tool.id == tool_id).first()

    def get_by_name(self, name: str) -> Optional[Tool]:
        """根据名称获取工具。"""
        return self.db.query(Tool).filter(Tool.name == name).first()

    def list(self, enabled_only: bool = True) -> List[Tool]:
        """获取工具列表。

        Args:
            enabled_only: 是否仅返回启用的工具。

        Returns:
            工具列表，按 ID 升序排列。
        """
        query = self.db.query(Tool)
        if enabled_only:
            query = query.filter(Tool.is_enabled == True)  # noqa: E712
        return query.order_by(Tool.id.asc()).all()

    def update(self, tool_id: int, update: ToolUpdate) -> Tool:
        """更新工具信息，仅更新非 None 字段。

        Args:
            tool_id: 工具 ID。
            update: 工具更新数据。

        Returns:
            更新后的工具 ORM 对象。

        Raises:
            ValueError: 工具不存在，或新名称与其他工具冲突。
        """
        db_tool = self.get(tool_id)
        if db_tool is None:
            raise ValueError(f"工具不存在: id={tool_id}")

        update_data = update.model_dump(exclude_unset=True)

        # 若更新名称，需检查唯一性
        if "name" in update_data and update_data["name"] != db_tool.name:
            existing = self.get_by_name(update_data["name"])
            if existing and existing.id != tool_id:
                raise ValueError(f"工具名称已存在: {update_data['name']}")

        # 参数需序列化为 JSON 字符串
        if "parameters" in update_data and update_data["parameters"] is not None:
            update_data["parameters"] = json.dumps(
                [p.model_dump() for p in update.parameters], ensure_ascii=False
            )

        for field, value in update_data.items():
            setattr(db_tool, field, value)

        self.db.commit()
        self.db.refresh(db_tool)

        self.logger.log_system(
            log_type="event",
            module="tools",
            action="update_success",
            details={"tool_id": tool_id, "fields": list(update_data.keys())},
        )
        return db_tool

    def delete(self, tool_id: int) -> bool:
        """删除工具。

        Args:
            tool_id: 工具 ID。

        Returns:
            删除成功返回 True，工具不存在返回 False。
        """
        db_tool = self.get(tool_id)
        if db_tool is None:
            return False

        tool_name = db_tool.name
        self.db.delete(db_tool)
        self.db.commit()

        self.logger.log_system(
            log_type="event",
            module="tools",
            action="delete_success",
            details={"tool_id": tool_id, "name": tool_name},
        )
        return True

    def to_openai_format(self, tool: Tool) -> Dict[str, Any]:
        """将工具转换为 OpenAI function calling 格式。

        Args:
            tool: 工具 ORM 对象。

        Returns:
            符合 OpenAI tools 规范的字典。
        """
        # 反序列化参数定义
        parameters = tool.parameters
        if isinstance(parameters, str):
            parameters = json.loads(parameters)

        properties: Dict[str, Any] = {}
        required: List[str] = []
        for param in parameters:
            name = param.get("name")
            properties[name] = {
                "type": param.get("type", "string"),
                "description": param.get("description") or "",
            }
            if param.get("required", True):
                required.append(name)

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

"""工具参数验证器模块 - 校验调用参数是否符合工具定义。"""
import json
from typing import Any, Dict, List, Tuple

from src.db.models import Tool


class ToolValidator:
    """工具参数验证器，检查必填参数与类型匹配。"""

    # 参数类型到 Python 类型的映射
    _TYPE_MAP: Dict[str, type] = {
        "string": str,
        "integer": int,
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    def validate(self, tool: Tool, arguments: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证调用参数是否符合工具定义。

        Args:
            tool: 工具定义（ORM 对象）。
            arguments: 调用参数字典。

        Returns:
            元组 (是否通过验证, 错误信息列表)。
        """
        errors: List[str] = []
        parameters = self._normalize_parameters(tool.parameters)

        # 检查必填参数是否提供
        for param in parameters:
            name = param.get("name")
            required = param.get("required", True)
            if required and name not in arguments:
                errors.append(f"缺少必填参数: {name}")

        # 检查已提供参数的类型
        for param in parameters:
            name = param.get("name")
            if name in arguments:
                expected_type = param.get("type")
                if not self.validate_type(arguments[name], expected_type):
                    errors.append(
                        f"参数类型错误: {name} 应为 {expected_type}"
                    )

        return (len(errors) == 0, errors)

    def validate_type(self, value: Any, expected_type: str) -> bool:
        """验证值是否符合预期类型。

        Args:
            value: 待验证的值。
            expected_type: 预期类型名称(string/integer/boolean/object/array)。

        Returns:
            类型匹配返回 True，否则返回 False。
        """
        # 布尔类型需单独处理，因为 bool 是 int 的子类
        if expected_type == "boolean":
            return isinstance(value, bool)
        # 整数类型需排除布尔值
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)

        py_type = self._TYPE_MAP.get(expected_type)
        if py_type is None:
            # 未知类型不做限制
            return True
        return isinstance(value, py_type)

    @staticmethod
    def _normalize_parameters(parameters: Any) -> List[Dict[str, Any]]:
        """将参数定义统一为字典列表形式。

        数据库中存储为 JSON 字符串，需反序列化；
        也兼容已是列表或 Parameter 对象的情况。
        """
        if isinstance(parameters, str):
            parameters = json.loads(parameters)
        if not isinstance(parameters, list):
            return []
        result: List[Dict[str, Any]] = []
        for item in parameters:
            if hasattr(item, "model_dump"):
                result.append(item.model_dump())
            elif isinstance(item, dict):
                result.append(item)
        return result

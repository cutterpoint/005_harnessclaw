"""内置计算器工具 - 安全地计算数学表达式。"""
import ast
import operator


# 支持的运算符映射
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,  # 一元负号
    ast.UAdd: operator.pos,  # 一元正号
}


def calculate(expression: str) -> dict:
    """简单计算器工具，安全地计算数学表达式。

    仅支持加减乘除、括号和数字常量，通过 AST 解析避免
    执行任意代码。

    Args:
        expression: 数学表达式字符串，如 "1 + 2 * 3"。

    Returns:
        包含表达式和计算结果的字典，如 {"expression": "1+2", "result": 3}。

    Raises:
        ValueError: 表达式包含不支持的运算或语法错误。
    """
    def _eval(node: ast.AST) -> float:
        """递归求值 AST 节点。"""
        if isinstance(node, ast.Constant):  # 数字常量
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
        if isinstance(node, ast.BinOp):  # 二元运算
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type not in _OPS:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
            return _OPS[op_type](left, right)
        if isinstance(node, ast.UnaryOp):  # 一元运算
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type not in _OPS:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
            return _OPS[op_type](operand)
        raise ValueError(f"不支持的表达式元素: {type(node).__name__}")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"表达式语法错误: {exc}") from exc

    result = _eval(tree.body)
    return {"expression": expression, "result": result}

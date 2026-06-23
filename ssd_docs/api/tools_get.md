# GET /tools/{tool_id} - 获取单个工具

## 功能说明

获取指定ID的工具详情。

## 接口逻辑

1. 根据工具ID查询工具
2. 验证工具是否存在
3. 返回工具信息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| tool_id | integer | 是 | 工具ID |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "success",
  "data": {
    "id": "integer",
    "name": "string",
    "description": "string or null",
    "function_name": "string",
    "module_path": "string",
    "parameters": "array",
    "return_type": "string or null",
    "is_enabled": "boolean",
    "created_at": "datetime"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 工具不存在 | 指定的工具ID不存在 |

## 示例

**请求示例：**
```bash
GET /tools/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "id": 1,
    "name": "计算器",
    "description": "执行数学计算",
    "function_name": "calculate",
    "module_path": "src.tools.builtin.calculator",
    "parameters": [
      {
        "name": "expression",
        "type": "string",
        "required": true,
        "description": "数学表达式"
      }
    ],
    "return_type": "number",
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
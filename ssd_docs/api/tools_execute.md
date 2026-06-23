# POST /tools/{tool_id}/execute - 执行工具

## 功能说明

执行指定工具，传入参数获取执行结果。

## 接口逻辑

1. 根据工具ID查询工具
2. 验证工具是否存在且已启用
3. 调用工具执行器执行工具
4. 返回执行结果

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| tool_id | integer | 是 | 工具ID |

### 请求体（JSON）

请求体为工具所需的参数键值对，具体参数取决于工具定义。

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
    "tool_id": "integer",
    "success": "boolean",
    "result": "any",
    "error": "string or null",
    "execution_time": "float"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.tool_id | integer | 工具ID |
| data.success | boolean | 工具执行是否成功 |
| data.result | any | 工具执行结果 |
| data.error | string/null | 错误信息 |
| data.execution_time | float | 执行耗时（秒） |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 工具不存在 | 指定的工具ID不存在 |

## 示例

**请求示例：**
```bash
POST /tools/1/execute
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "expression": "2 + 3 * 4"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "tool_id": 1,
    "success": true,
    "result": 14,
    "error": null,
    "execution_time": 0.1
  }
}
```
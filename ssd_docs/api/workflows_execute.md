# POST /workflows/{workflow_id}/execute - 执行工作流

## 功能说明

执行指定工作流，传入输入参数获取执行结果。

## 接口逻辑

1. 根据工作流ID查询工作流
2. 验证工作流是否存在且用户有权访问
3. 调用工作流编排器执行工作流
4. 返回执行结果

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| workflow_id | integer | 是 | 工作流ID |

### 请求体（JSON）

请求体为工作流所需的输入参数键值对，具体参数取决于工作流定义。

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
    "execution_id": "integer",
    "workflow_id": "integer",
    "status": "string",
    "outputs": "object or null",
    "error": "string or null",
    "started_at": "datetime",
    "completed_at": "datetime or null"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.execution_id | integer | 执行记录ID |
| data.workflow_id | integer | 工作流ID |
| data.status | string | 执行状态 |
| data.outputs | object/null | 输出结果 |
| data.error | string/null | 错误信息 |
| data.started_at | datetime | 开始时间 |
| data.completed_at | datetime/null | 完成时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 工作流不存在 | 指定的工作流ID不存在 |
| 403 Forbidden | 无权执行该工作流 | 用户不拥有该工作流 |
| 400 Bad Request | 无效参数 | 参数值无效 |

## 示例

**请求示例：**
```bash
POST /workflows/1/execute
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "input_data": "需要处理的数据"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "execution_id": 1,
    "workflow_id": 1,
    "status": "completed",
    "outputs": {"result": "处理完成"},
    "error": null,
    "started_at": "2024-01-01T12:00:00",
    "completed_at": "2024-01-01T12:00:05"
  }
}
```
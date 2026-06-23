# GET /workflows/{workflow_id}/executions - 获取工作流执行历史

## 功能说明

获取指定工作流的执行历史记录，支持分页。

## 接口逻辑

1. 根据工作流ID查询工作流
2. 验证工作流是否存在且用户有权访问
3. 查询该工作流的执行记录
4. 应用分页
5. 返回执行历史列表

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| workflow_id | integer | 是 | 工作流ID |

### 查询参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认20，最大100 |

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
    "items": [
      {
        "execution_id": "integer",
        "workflow_id": "integer",
        "status": "string",
        "outputs": "object or null",
        "error": "string or null",
        "started_at": "datetime",
        "completed_at": "datetime or null"
      }
    ],
    "total": "integer",
    "page": "integer",
    "limit": "integer"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 工作流不存在 | 指定的工作流ID不存在 |
| 403 Forbidden | 无权访问该工作流 | 用户不拥有该工作流 |

## 示例

**请求示例：**
```bash
GET /workflows/1/executions?page=1&limit=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "items": [
      {
        "execution_id": 1,
        "workflow_id": 1,
        "status": "completed",
        "outputs": {"result": "处理完成"},
        "error": null,
        "started_at": "2024-01-01T12:00:00",
        "completed_at": "2024-01-01T12:00:05"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```
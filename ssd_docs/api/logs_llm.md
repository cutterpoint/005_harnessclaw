# GET /logs/llm - 查询 LLM 日志

## 功能说明

查询当前用户的LLM调用日志，支持分页。

## 接口逻辑

1. 获取当前用户ID
2. 查询LLM日志表，按用户ID筛选
3. 应用分页
4. 返回日志列表

## 输入参数

### 查询参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认100，最大500 |

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
        "id": "integer",
        "user_id": "integer",
        "session_id": "integer",
        "model_name": "string",
        "prompt_tokens": "integer",
        "completion_tokens": "integer",
        "total_tokens": "integer",
        "response_content": "string",
        "latency_ms": "integer",
        "success": "boolean",
        "error_message": "string or null",
        "cost_usd": "float",
        "created_at": "datetime"
      }
    ],
    "total": "integer",
    "page": "integer",
    "limit": "integer"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.items | array | LLM日志列表 |
| data.items[].id | integer | 日志ID |
| data.items[].user_id | integer | 用户ID |
| data.items[].session_id | integer | 会话ID |
| data.items[].model_name | string | 模型名称 |
| data.items[].prompt_tokens | integer | 提示词令牌数 |
| data.items[].completion_tokens | integer | 补全令牌数 |
| data.items[].total_tokens | integer | 总令牌数 |
| data.items[].response_content | string | 响应内容 |
| data.items[].latency_ms | integer | 延迟（毫秒） |
| data.items[].success | boolean | 是否成功 |
| data.items[].error_message | string/null | 错误信息 |
| data.items[].cost_usd | float | 花费（美元） |
| data.items[].created_at | datetime | 创建时间 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.limit | integer | 每页数量 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
GET /logs/llm?page=1&limit=20
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
        "id": 1,
        "user_id": 1,
        "session_id": 1,
        "model_name": "gpt-4",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "response_content": "Hello!",
        "latency_ms": 1200,
        "success": true,
        "error_message": null,
        "cost_usd": 0.002,
        "created_at": "2024-01-01T12:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```
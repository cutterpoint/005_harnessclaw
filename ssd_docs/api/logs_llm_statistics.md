# GET /logs/llm/statistics - 获取 LLM 统计信息

## 功能说明

获取当前用户的LLM使用统计信息，包括总调用次数、总令牌数、总花费等。

## 接口逻辑

1. 获取当前用户ID
2. 统计该用户的LLM调用记录
3. 计算总调用次数、总令牌数、总花费等指标
4. 返回统计结果

## 输入参数

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
    "total_calls": "integer",
    "successful_calls": "integer",
    "failed_calls": "integer",
    "total_tokens": "integer",
    "prompt_tokens": "integer",
    "completion_tokens": "integer",
    "total_cost_usd": "float",
    "avg_latency_ms": "float"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.total_calls | integer | 总调用次数 |
| data.successful_calls | integer | 成功调用次数 |
| data.failed_calls | integer | 失败调用次数 |
| data.total_tokens | integer | 总令牌数 |
| data.prompt_tokens | integer | 提示词令牌总数 |
| data.completion_tokens | integer | 补全令牌总数 |
| data.total_cost_usd | float | 总花费（美元） |
| data.avg_latency_ms | float | 平均延迟（毫秒） |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
GET /logs/llm/statistics
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "total_calls": 100,
    "successful_calls": 98,
    "failed_calls": 2,
    "total_tokens": 15000,
    "prompt_tokens": 10000,
    "completion_tokens": 5000,
    "total_cost_usd": 15.50,
    "avg_latency_ms": 1200.5
  }
}
```
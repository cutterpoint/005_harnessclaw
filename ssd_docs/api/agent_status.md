# GET /agent/status/{session_id} - 获取 Agent 状态

## 功能说明

查询指定会话的 Agent 运行状态，包括当前迭代次数、最大迭代次数、错误信息等。

## 接口逻辑

1. 根据会话ID查询 Agent 状态
2. 返回状态信息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| session_id | integer | 是 | 会话ID |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token，格式：`Bearer <access_token>` |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "success",
  "data": {
    "state": "string",
    "iteration": "integer",
    "max_iterations": "integer",
    "session_id": "integer or null",
    "error": "string or null"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.state | string | 状态值：idle/running/finished/error |
| data.iteration | integer | 当前迭代次数 |
| data.max_iterations | integer | 最大迭代次数 |
| data.session_id | integer/null | 会话ID |
| data.error | string/null | 错误信息 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌或令牌已过期 |
| 404 Not Found | 会话不存在 | 指定的会话ID不存在 |

## 示例

**请求示例：**
```bash
GET /agent/status/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "state": "finished",
    "iteration": 3,
    "max_iterations": 10,
    "session_id": 1,
    "error": null
  }
}
```
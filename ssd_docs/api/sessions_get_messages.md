# GET /sessions/{session_id}/messages - 获取会话消息列表

## 功能说明

获取指定会话的消息列表，支持分页。

## 接口逻辑

1. 根据会话ID查询会话
2. 验证会话是否存在
3. 验证用户是否有权访问
4. 查询该会话的所有消息
5. 应用分页
6. 返回消息列表

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| session_id | integer | 是 | 会话ID |

### 查询参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认50，最大200 |

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
        "session_id": "integer",
        "role": "string",
        "content": "string",
        "tool_call": "string or null",
        "tool_call_id": "string or null",
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
| data.items | array | 消息列表 |
| data.items[].id | integer | 消息ID |
| data.items[].session_id | integer | 会话ID |
| data.items[].role | string | 角色（user/assistant/tool） |
| data.items[].content | string | 消息内容 |
| data.items[].tool_call | string/null | 工具调用信息 |
| data.items[].tool_call_id | string/null | 工具调用ID |
| data.items[].created_at | datetime | 创建时间 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.limit | integer | 每页数量 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 会话不存在 | 指定的会话ID不存在 |
| 403 Forbidden | 无权访问该会话 | 用户不拥有该会话 |

## 示例

**请求示例：**
```bash
GET /sessions/1/messages?page=1&limit=20
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
        "session_id": 1,
        "role": "user",
        "content": "你好",
        "tool_call": null,
        "tool_call_id": null,
        "created_at": "2024-01-01T12:00:00"
      },
      {
        "id": 2,
        "session_id": 1,
        "role": "assistant",
        "content": "您好！有什么可以帮助您的？",
        "tool_call": null,
        "tool_call_id": null,
        "created_at": "2024-01-01T12:00:01"
      }
    ],
    "total": 2,
    "page": 1,
    "limit": 20
  }
}
```
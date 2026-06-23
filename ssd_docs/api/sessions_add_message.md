# POST /sessions/{session_id}/messages - 添加消息

## 功能说明

向指定会话添加新消息。

## 接口逻辑

1. 根据会话ID查询会话
2. 验证会话是否存在
3. 验证用户是否有权访问
4. 创建消息记录
5. 返回消息信息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| session_id | integer | 是 | 会话ID |

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| role | string | 是 | 角色（user/assistant/tool） |
| content | string | 是 | 消息内容 |
| tool_call | string | 否 | 工具调用信息（JSON字符串） |
| tool_call_id | string | 否 | 工具调用ID |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "添加成功",
  "data": {
    "id": "integer",
    "session_id": "integer",
    "role": "string",
    "content": "string",
    "tool_call": "string or null",
    "tool_call_id": "string or null",
    "created_at": "datetime"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 会话不存在 | 指定的会话ID不存在 |
| 403 Forbidden | 无权访问该会话 | 用户不拥有该会话 |
| 400 Bad Request | 无效参数 | 参数值无效 |

## 示例

**请求示例：**
```bash
POST /sessions/1/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "role": "user",
  "content": "帮我查询天气"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "添加成功",
  "data": {
    "id": 3,
    "session_id": 1,
    "role": "user",
    "content": "帮我查询天气",
    "tool_call": null,
    "tool_call_id": null,
    "created_at": "2024-01-01T12:30:00"
  }
}
```
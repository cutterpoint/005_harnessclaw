# POST /sessions - 创建会话

## 功能说明

创建新的会话，用于存储对话历史。

## 接口逻辑

1. 接收会话创建请求
2. 生成唯一会话密钥
3. 创建会话记录
4. 返回会话信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| title | string | 否 | 会话标题 |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": "integer",
    "user_id": "integer",
    "session_key": "string",
    "title": "string or null",
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime or null"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.id | integer | 会话ID |
| data.user_id | integer | 用户ID |
| data.session_key | string | 会话密钥 |
| data.title | string/null | 会话标题 |
| data.status | string | 会话状态 |
| data.created_at | datetime | 创建时间 |
| data.updated_at | datetime/null | 更新时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
POST /sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "我的第一个会话"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "session_key": "abc123def456",
    "title": "我的第一个会话",
    "status": "active",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": null
  }
}
```
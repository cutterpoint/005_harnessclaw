# GET /sessions/{session_id} - 获取单个会话

## 功能说明

获取指定ID的会话详情。

## 接口逻辑

1. 根据会话ID查询会话
2. 验证会话是否存在
3. 验证用户是否有权访问
4. 返回会话信息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| session_id | integer | 是 | 会话ID |

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
    "user_id": "integer",
    "session_key": "string",
    "title": "string or null",
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime or null"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 会话不存在 | 指定的会话ID不存在 |
| 403 Forbidden | 无权访问该会话 | 用户不拥有该会话 |

## 示例

**请求示例：**
```bash
GET /sessions/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "id": 1,
    "user_id": 1,
    "session_key": "abc123def456",
    "title": "我的第一个会话",
    "status": "active",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:30:00"
  }
}
```
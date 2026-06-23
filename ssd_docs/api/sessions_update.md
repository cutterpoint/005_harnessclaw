# PUT /sessions/{session_id} - 更新会话

## 功能说明

更新指定会话的信息，如标题、状态等。

## 接口逻辑

1. 根据会话ID查询会话
2. 验证会话是否存在
3. 验证用户是否有权修改
4. 更新会话信息
5. 返回更新后的会话

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| session_id | integer | 是 | 会话ID |

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| title | string | 否 | 会话标题 |
| status | string | 否 | 会话状态（active/archived/deleted） |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "更新成功",
  "data": {
    "id": "integer",
    "user_id": "integer",
    "session_key": "string",
    "title": "string or null",
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 会话不存在 | 指定的会话ID不存在 |
| 403 Forbidden | 无权修改该会话 | 用户不拥有该会话 |
| 400 Bad Request | 无效参数 | 参数值无效 |

## 示例

**请求示例：**
```bash
PUT /sessions/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "更新后的会话标题",
  "status": "archived"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "更新成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "session_key": "abc123def456",
    "title": "更新后的会话标题",
    "status": "archived",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T13:00:00"
  }
}
```
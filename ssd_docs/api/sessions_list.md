# GET /sessions - 获取会话列表

## 功能说明

获取当前用户的会话列表，支持分页。

## 接口逻辑

1. 获取当前用户ID
2. 查询该用户的所有会话
3. 应用分页
4. 返回会话列表

## 输入参数

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
        "id": "integer",
        "user_id": "integer",
        "session_key": "string",
        "title": "string or null",
        "status": "string",
        "created_at": "datetime",
        "updated_at": "datetime or null"
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

## 示例

**请求示例：**
```bash
GET /sessions?page=1&limit=20
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
        "session_key": "abc123def456",
        "title": "我的第一个会话",
        "status": "active",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```
# GET /auth/me - 获取当前用户信息

## 功能说明

获取当前登录用户的详细信息。

## 接口逻辑

1. 从请求头解析并验证访问令牌
2. 获取当前用户信息
3. 返回用户数据

## 输入参数

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
    "id": "integer",
    "username": "string",
    "email": "string",
    "is_active": "boolean",
    "created_at": "datetime"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.id | integer | 用户ID |
| data.username | string | 用户名 |
| data.email | string | 邮箱地址 |
| data.is_active | boolean | 用户是否激活 |
| data.created_at | datetime | 创建时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌或令牌已过期 |

## 示例

**请求示例：**
```bash
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
# POST /auth/register - 用户注册

## 功能说明

创建新用户账户，完成用户注册流程。

## 接口逻辑

1. 接收用户注册请求（用户名、邮箱、密码）
2. 验证请求参数合法性
3. 检查用户名或邮箱是否已存在
4. 创建新用户记录（密码加密存储）
5. 返回用户信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| username | string | 是 | 用户名，需唯一 |
| email | string | 是 | 邮箱地址，需符合邮箱格式 |
| password | string | 是 | 密码，建议至少6位 |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "注册成功",
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
| 400 Bad Request | 用户名已存在 | 用户名重复 |
| 400 Bad Request | 邮箱已存在 | 邮箱重复 |
| 400 Bad Request | 无效邮箱格式 | 邮箱格式不正确 |

## 示例

**请求示例：**
```bash
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "password123"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
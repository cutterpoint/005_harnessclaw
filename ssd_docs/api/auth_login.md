# POST /auth/login - 用户登录

## 功能说明

用户登录系统，获取访问令牌和刷新令牌。

## 接口逻辑

1. 接收登录请求（用户名、密码）
2. 验证用户是否存在
3. 验证密码是否正确
4. 生成访问令牌和刷新令牌
5. 返回令牌信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "string"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.access_token | string | 访问令牌，用于API认证 |
| data.refresh_token | string | 刷新令牌，用于获取新的访问令牌 |
| data.token_type | string | 令牌类型，固定为"bearer" |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 用户不存在 | 用户名错误 |
| 401 Unauthorized | 密码错误 | 密码不匹配 |

## 示例

**请求示例：**
```bash
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "password123"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```
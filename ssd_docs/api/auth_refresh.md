# POST /auth/refresh - 刷新访问令牌

## 功能说明

使用刷新令牌获取新的访问令牌，延长会话有效期。

## 接口逻辑

1. 接收刷新令牌
2. 验证刷新令牌有效性
3. 生成新的访问令牌
4. 返回新令牌信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| refresh_token | string | 是 | 刷新令牌 |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "刷新成功",
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
| data.access_token | string | 新的访问令牌 |
| data.refresh_token | string | 新的刷新令牌 |
| data.token_type | string | 令牌类型，固定为"bearer" |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 无效的刷新令牌 | 令牌已过期或无效 |

## 示例

**请求示例：**
```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```
# DELETE /sessions/{session_id} - 删除会话

## 功能说明

软删除指定会话，将会话状态标记为deleted。

## 接口逻辑

1. 根据会话ID查询会话
2. 验证会话是否存在
3. 验证用户是否有权删除
4. 将会话状态标记为deleted（软删除）
5. 返回成功消息

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
  "message": "删除成功",
  "data": null
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 会话不存在 | 指定的会话ID不存在 |
| 403 Forbidden | 无权删除该会话 | 用户不拥有该会话 |

## 示例

**请求示例：**
```bash
DELETE /sessions/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "删除成功",
  "data": null
}
```
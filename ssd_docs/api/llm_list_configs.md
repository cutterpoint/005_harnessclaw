# GET /llm/configs - 获取 LLM 配置列表

## 功能说明

获取当前用户的所有 LLM 配置列表。

## 接口逻辑

1. 获取当前用户ID
2. 查询数据库中该用户的所有配置
3. 对API密钥进行脱敏处理
4. 返回配置列表

## 输入参数

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
  "data": [
    {
      "id": "integer",
      "user_id": "integer",
      "name": "string",
      "api_key": "string",
      "api_base": "string",
      "model_name": "string",
      "max_tokens": "integer",
      "temperature": "float",
      "is_active": "boolean",
      "created_at": "datetime"
    }
  ]
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data | array | 配置列表 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
GET /llm/configs
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "name": "OpenAI-GPT4",
      "api_key": "sk-xx***xxxx",
      "api_base": "https://api.openai.com/v1",
      "model_name": "gpt-4",
      "max_tokens": 8192,
      "temperature": 0.5,
      "is_active": true,
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```
# GET /llm/configs/{config_id} - 获取单个 LLM 配置

## 功能说明

获取指定ID的LLM配置详情。

## 接口逻辑

1. 根据配置ID查询配置
2. 验证配置是否存在
3. 验证用户是否有权访问
4. 返回脱敏后的配置信息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| config_id | integer | 是 | 配置ID |

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
    "name": "string",
    "api_key": "string",
    "api_base": "string",
    "model_name": "string",
    "max_tokens": "integer",
    "temperature": "float",
    "is_active": "boolean",
    "created_at": "datetime"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 配置不存在 | 指定的配置ID不存在 |
| 403 Forbidden | 无权访问该配置 | 用户不拥有该配置 |

## 示例

**请求示例：**
```bash
GET /llm/configs/1
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
    "name": "OpenAI-GPT4",
    "api_key": "sk-xx***xxxx",
    "api_base": "https://api.openai.com/v1",
    "model_name": "gpt-4",
    "max_tokens": 8192,
    "temperature": 0.5,
    "is_active": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
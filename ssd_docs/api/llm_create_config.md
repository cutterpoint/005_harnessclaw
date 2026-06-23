# POST /llm/configs - 创建 LLM 配置

## 功能说明

创建新的 LLM（大语言模型）配置，用于连接外部 LLM 服务（如 OpenAI、自定义模型等）。

## 接口逻辑

1. 接收配置创建请求
2. 验证参数合法性
3. 将配置保存到数据库（API Key 加密存储）
4. 返回脱敏后的配置信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 是 | 配置名称，用于标识该配置 |
| api_key | string | 是 | API密钥 |
| api_base | string | 是 | API基础URL |
| model_name | string | 是 | 模型名称 |
| max_tokens | integer | 否 | 最大令牌数，默认4096 |
| temperature | float | 否 | 温度参数，默认0.7 |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "创建成功",
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

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.id | integer | 配置ID |
| data.user_id | integer | 用户ID |
| data.name | string | 配置名称 |
| data.api_key | string | 脱敏后的API密钥（仅显示首尾各4位） |
| data.api_base | string | API基础URL |
| data.model_name | string | 模型名称 |
| data.max_tokens | integer | 最大令牌数 |
| data.temperature | float | 温度参数 |
| data.is_active | boolean | 是否为激活状态 |
| data.created_at | datetime | 创建时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
POST /llm/configs
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "OpenAI-GPT4",
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4",
  "max_tokens": 8192,
  "temperature": 0.5
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "name": "OpenAI-GPT4",
    "api_key": "sk-xx***xxxx",
    "api_base": "https://api.openai.com/v1",
    "model_name": "gpt-4",
    "max_tokens": 8192,
    "temperature": 0.5,
    "is_active": false,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
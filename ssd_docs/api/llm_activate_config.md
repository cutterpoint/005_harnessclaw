# POST /llm/configs/{config_id}/activate - 激活 LLM 配置

## 功能说明

将指定配置设置为当前激活的LLM配置，系统将使用该配置进行LLM调用。

## 接口逻辑

1. 根据配置ID查询配置
2. 将该配置设置为激活状态
3. 将用户的其他配置设置为非激活状态
4. 返回激活后的配置信息

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
  "message": "激活成功",
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
| 404 Not Found | 配置不存在或无权激活 | 配置不存在或用户无权限 |

## 示例

**请求示例：**
```bash
POST /llm/configs/1/activate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "激活成功",
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
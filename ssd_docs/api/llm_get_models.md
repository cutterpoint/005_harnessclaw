# GET /llm/models - 获取可用模型列表

## 功能说明

获取当前激活的LLM配置支持的模型列表。

## 接口逻辑

1. 获取当前用户的激活配置
2. 调用LLM服务获取模型列表
3. 返回模型列表

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
  "data": ["string"]
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data | array | 模型名称列表 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
GET /llm/models
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
}
```
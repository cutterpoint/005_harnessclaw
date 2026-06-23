# POST /agent/chat - 发起对话

## 功能说明

发起与 Agent 的对话，由 Agent 引擎处理用户输入并返回响应。该接口是整个系统的核心交互入口，支持上下文记忆、工具调用、技能执行等能力。

## 接口逻辑

1. 接收用户消息和可选的会话ID
2. 注入当前用户ID到请求中
3. 创建 AgentEngine 及其所有依赖组件（LLM服务、工具执行器、会话管理器、技能管理器、记忆系统、提示词构建器、决策引擎、工作流编排器）
4. 调用 AgentEngine.run() 处理请求
5. 返回格式化的响应结果

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| message | string | 是 | 用户输入消息内容 |
| session_id | integer | 否 | 会话ID，未提供时创建新会话 |

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
    "response": "string",
    "session_id": "integer",
    "iterations": "integer",
    "tool_calls": "array",
    "error": "string or null"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.response | string | Agent 返回的最终回复内容 |
| data.session_id | integer | 当前会话ID |
| data.iterations | integer | 实际迭代次数 |
| data.tool_calls | array | 工具调用结果列表 |
| data.error | string/null | 错误信息，无错误时为 null |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌或令牌已过期 |
| 500 Internal Server Error | 内部错误 | Agent引擎初始化失败或执行过程出错 |

## 示例

**请求示例：**
```bash
POST /agent/chat
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": "帮我查询今天的天气",
  "session_id": 1
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "response": "今天北京的天气是晴天，温度25-32度",
    "session_id": 1,
    "iterations": 2,
    "tool_calls": [
      {
        "tool_name": "weather",
        "result": "晴天，25-32度"
      }
    ],
    "error": null
  }
}
```
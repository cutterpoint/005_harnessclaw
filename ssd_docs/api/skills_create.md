# POST /skills - 创建技能

## 功能说明

创建新的技能，技能是可复用的提示词模板或业务逻辑单元。

## 接口逻辑

1. 接收技能创建请求
2. 创建技能记录
3. 返回技能信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 是 | 技能名称 |
| description | string | 否 | 技能描述 |
| prompt | string | 否 | 提示词模板 |

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
    "description": "string or null",
    "prompt": "string or null",
    "is_enabled": "boolean",
    "created_at": "datetime"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.id | integer | 技能ID |
| data.user_id | integer | 用户ID |
| data.name | string | 技能名称 |
| data.description | string/null | 技能描述 |
| data.prompt | string/null | 提示词模板 |
| data.is_enabled | boolean | 是否启用 |
| data.created_at | datetime | 创建时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
POST /skills
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "翻译技能",
  "description": "将中文翻译成英文",
  "prompt": "请将以下文本翻译成英文：{{input}}"
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
    "name": "翻译技能",
    "description": "将中文翻译成英文",
    "prompt": "请将以下文本翻译成英文：{{input}}",
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
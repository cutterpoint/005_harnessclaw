# GET /skills - 获取技能列表

## 功能说明

获取当前用户的技能列表，支持分页。

## 接口逻辑

1. 获取当前用户ID
2. 查询该用户的所有技能
3. 应用分页
4. 返回技能列表

## 输入参数

### 查询参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认20，最大100 |

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
    "items": [
      {
        "id": "integer",
        "user_id": "integer",
        "name": "string",
        "description": "string or null",
        "prompt": "string or null",
        "is_enabled": "boolean",
        "created_at": "datetime"
      }
    ],
    "total": "integer",
    "page": "integer",
    "limit": "integer"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
GET /skills?page=1&limit=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "name": "翻译技能",
        "description": "将中文翻译成英文",
        "prompt": "请将以下文本翻译成英文：{{input}}",
        "is_enabled": true,
        "created_at": "2024-01-01T12:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```
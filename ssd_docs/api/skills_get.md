# GET /skills/{skill_id} - 获取单个技能

## 功能说明

获取指定ID的技能详情。

## 接口逻辑

1. 根据技能ID查询技能
2. 验证技能是否存在
3. 验证用户是否有权访问
4. 返回技能信息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| skill_id | integer | 是 | 技能ID |

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
    "description": "string or null",
    "prompt": "string or null",
    "is_enabled": "boolean",
    "created_at": "datetime"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 技能不存在 | 指定的技能ID不存在 |
| 403 Forbidden | 无权访问该技能 | 用户不拥有该技能 |

## 示例

**请求示例：**
```bash
GET /skills/1
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
    "name": "翻译技能",
    "description": "将中文翻译成英文",
    "prompt": "请将以下文本翻译成英文：{{input}}",
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
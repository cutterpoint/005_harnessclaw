# PUT /skills/{skill_id} - 更新技能

## 功能说明

更新指定技能的信息。

## 接口逻辑

1. 根据技能ID查询技能
2. 验证技能是否存在
3. 验证用户是否有权修改
4. 更新技能信息
5. 返回更新后的技能

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| skill_id | integer | 是 | 技能ID |

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 否 | 技能名称 |
| description | string | 否 | 技能描述 |
| prompt | string | 否 | 提示词模板 |
| is_enabled | boolean | 否 | 是否启用 |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "更新成功",
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
| 403 Forbidden | 无权修改该技能 | 用户不拥有该技能 |
| 400 Bad Request | 无效参数 | 参数值无效 |

## 示例

**请求示例：**
```bash
PUT /skills/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "翻译技能(更新)",
  "is_enabled": false
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "更新成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "name": "翻译技能(更新)",
    "description": "将中文翻译成英文",
    "prompt": "请将以下文本翻译成英文：{{input}}",
    "is_enabled": false,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
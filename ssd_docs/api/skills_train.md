# POST /skills/train - 训练技能

## 功能说明

通过分析执行历史自动生成新技能。

## 接口逻辑

1. 接收训练请求（执行历史、技能名称、描述）
2. 调用LLM分析执行历史
3. 生成技能提示词
4. 创建新技能记录
5. 返回技能信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| execution_history | array | 是 | 执行历史记录列表 |
| skill_name | string | 是 | 新技能名称 |
| description | string | 否 | 技能描述 |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "训练成功",
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
| 400 Bad Request | 无效参数 | 参数值无效或执行历史为空 |

## 示例

**请求示例：**
```bash
POST /skills/train
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "execution_history": [
    {
      "input": "你好",
      "output": "Hello"
    },
    {
      "input": "谢谢",
      "output": "Thank you"
    }
  ],
  "skill_name": "中文到英文翻译",
  "description": "自动将中文短句翻译成英文"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "训练成功",
  "data": {
    "id": 2,
    "user_id": 1,
    "name": "中文到英文翻译",
    "description": "自动将中文短句翻译成英文",
    "prompt": "请将以下中文文本翻译成英文：{{input}}",
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
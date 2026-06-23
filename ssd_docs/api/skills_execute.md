# POST /skills/{skill_id}/execute - 执行技能

## 功能说明

执行指定技能，传入输入文本获取技能输出。

## 接口逻辑

1. 根据技能ID查询技能
2. 验证技能是否存在
3. 验证用户是否有权执行
4. 调用技能执行逻辑
5. 返回执行结果

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| skill_id | integer | 是 | 技能ID |

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| input | string | 是 | 输入文本 |
| session_id | integer | 否 | 会话ID |

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
    "skill_id": "integer",
    "success": "boolean",
    "output": "string or null",
    "error": "string or null",
    "execution_time": "float"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.skill_id | integer | 技能ID |
| data.success | boolean | 技能执行是否成功 |
| data.output | string/null | 技能输出结果 |
| data.error | string/null | 错误信息 |
| data.execution_time | float | 执行耗时（秒） |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 技能不存在 | 指定的技能ID不存在 |
| 403 Forbidden | 无权执行该技能 | 用户不拥有该技能 |

## 示例

**请求示例：**
```bash
POST /skills/1/execute
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "input": "你好世界",
  "session_id": 1
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "skill_id": 1,
    "success": true,
    "output": "Hello World",
    "error": null,
    "execution_time": 0.5
  }
}
```
# DELETE /skills/{skill_id} - 删除技能

## 功能说明

删除指定技能。

## 接口逻辑

1. 根据技能ID查询技能
2. 验证技能是否存在
3. 验证用户是否有权删除
4. 删除技能记录
5. 返回成功消息

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
  "message": "删除成功",
  "data": null
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 技能不存在 | 指定的技能ID不存在 |
| 403 Forbidden | 无权删除该技能 | 用户不拥有该技能 |

## 示例

**请求示例：**
```bash
DELETE /skills/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应示例：**
```json
{
  "success": true,
  "message": "删除成功",
  "data": null
}
```
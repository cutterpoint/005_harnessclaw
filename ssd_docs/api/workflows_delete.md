# DELETE /workflows/{workflow_id} - 删除工作流

## 功能说明

删除指定工作流。

## 接口逻辑

1. 根据工作流ID查询工作流
2. 验证工作流是否存在
3. 验证用户是否有权删除
4. 删除工作流记录
5. 返回成功消息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| workflow_id | integer | 是 | 工作流ID |

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
| 404 Not Found | 工作流不存在 | 指定的工作流ID不存在 |
| 403 Forbidden | 无权删除该工作流 | 用户不拥有该工作流 |

## 示例

**请求示例：**
```bash
DELETE /workflows/1
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
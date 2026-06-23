# DELETE /tools/{tool_id} - 删除工具

## 功能说明

删除指定工具。

## 接口逻辑

1. 根据工具ID查询工具
2. 验证工具是否存在
3. 删除工具记录
4. 返回成功消息

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| tool_id | integer | 是 | 工具ID |

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
| 404 Not Found | 工具不存在 | 指定的工具ID不存在 |

## 示例

**请求示例：**
```bash
DELETE /tools/1
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
# PUT /workflows/{workflow_id} - 更新工作流

## 功能说明

更新指定工作流的信息。

## 接口逻辑

1. 根据工作流ID查询工作流
2. 验证工作流是否存在
3. 验证用户是否有权修改
4. 更新工作流信息
5. 返回更新后的工作流

## 输入参数

### 路径参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| workflow_id | integer | 是 | 工作流ID |

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 否 | 工作流名称 |
| description | string | 否 | 工作流描述 |
| nodes | array | 否 | 节点定义列表 |
| edges | array | 否 | 边定义列表 |
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
    "nodes": "array",
    "edges": "array",
    "is_enabled": "boolean",
    "created_at": "datetime"
  }
}
```

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 404 Not Found | 工作流不存在 | 指定的工作流ID不存在 |
| 403 Forbidden | 无权修改该工作流 | 用户不拥有该工作流 |
| 400 Bad Request | 无效参数 | 参数值无效 |

## 示例

**请求示例：**
```bash
PUT /workflows/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "数据处理工作流(更新)",
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
    "name": "数据处理工作流(更新)",
    "description": "处理数据并生成报告",
    "nodes": [...],
    "edges": [...],
    "is_enabled": false,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
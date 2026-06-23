# GET /workflows/{workflow_id} - 获取单个工作流

## 功能说明

获取指定ID的工作流详情。

## 接口逻辑

1. 根据工作流ID查询工作流
2. 验证工作流是否存在
3. 验证用户是否有权访问
4. 返回工作流信息

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
  "message": "success",
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
| 403 Forbidden | 无权访问该工作流 | 用户不拥有该工作流 |

## 示例

**请求示例：**
```bash
GET /workflows/1
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
    "name": "数据处理工作流",
    "description": "处理数据并生成报告",
    "nodes": [...],
    "edges": [...],
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
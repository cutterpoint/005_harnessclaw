# GET /logs/system - 查询系统日志

## 功能说明

查询系统日志，支持按日志类型、模块进行筛选，支持分页。

## 接口逻辑

1. 接收查询参数（日志类型、模块、页码、每页数量）
2. 查询系统日志表
3. 应用筛选条件和分页
4. 返回日志列表

## 输入参数

### 查询参数

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| log_type | string | 否 | 日志类型筛选 |
| module | string | 否 | 模块筛选 |
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认100，最大500 |

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
    "items": [],
    "total": "integer",
    "page": "integer",
    "limit": "integer"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.items | array | 日志条目列表 |
| data.total | integer | 总记录数 |
| data.page | integer | 当前页码 |
| data.limit | integer | 每页数量 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
GET /logs/system?log_type=error&module=agent&page=1&limit=20
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
        "log_type": "error",
        "module": "agent",
        "message": "Agent execution failed",
        "created_at": "2024-01-01T12:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```
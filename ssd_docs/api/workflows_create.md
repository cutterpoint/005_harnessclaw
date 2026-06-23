# POST /workflows - 创建工作流

## 功能说明

创建新的工作流，工作流由多个节点和边组成，定义了任务的执行流程。

## 接口逻辑

1. 接收工作流创建请求
2. 创建工作流记录
3. 返回工作流信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 是 | 工作流名称 |
| description | string | 否 | 工作流描述 |
| nodes | array | 是 | 节点定义列表 |
| edges | array | 是 | 边定义列表 |

### nodes 字段结构

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 是 | 节点名称 |
| type | string | 是 | 节点类型（decision/tool/skill/summary） |
| config | object | 否 | 节点配置 |

### edges 字段结构

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| source | string | 是 | 源节点名称 |
| target | string | 是 | 目标节点名称 |
| condition | string | 否 | 条件表达式 |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "创建成功",
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

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.id | integer | 工作流ID |
| data.user_id | integer | 用户ID |
| data.name | string | 工作流名称 |
| data.description | string/null | 工作流描述 |
| data.nodes | array | 节点定义列表 |
| data.edges | array | 边定义列表 |
| data.is_enabled | boolean | 是否启用 |
| data.created_at | datetime | 创建时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |

## 示例

**请求示例：**
```bash
POST /workflows
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "数据处理工作流",
  "description": "处理数据并生成报告",
  "nodes": [
    {
      "name": "input",
      "type": "decision",
      "config": {"prompt": "分析输入数据"}
    },
    {
      "name": "process",
      "type": "tool",
      "config": {"tool_id": 1}
    },
    {
      "name": "summary",
      "type": "summary",
      "config": {"prompt": "总结结果"}
    }
  ],
  "edges": [
    {"source": "input", "target": "process"},
    {"source": "process", "target": "summary"}
  ]
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "name": "数据处理工作流",
    "description": "处理数据并生成报告",
    "nodes": [
      {"name": "input", "type": "decision", "config": {"prompt": "分析输入数据"}},
      {"name": "process", "type": "tool", "config": {"tool_id": 1}},
      {"name": "summary", "type": "summary", "config": {"prompt": "总结结果"}}
    ],
    "edges": [
      {"source": "input", "target": "process"},
      {"source": "process", "target": "summary"}
    ],
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
# POST /tools - 注册工具

## 功能说明

注册新的工具，工具是可被Agent调用的外部功能模块。

## 接口逻辑

1. 接收工具注册请求
2. 验证工具参数合法性
3. 创建工具记录
4. 返回工具信息

## 输入参数

### 请求体（JSON）

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 是 | 工具名称 |
| description | string | 否 | 工具描述 |
| function_name | string | 是 | 函数名称 |
| module_path | string | 是 | 模块路径 |
| parameters | array | 是 | 参数定义列表 |
| return_type | string | 否 | 返回类型 |

### parameters 字段结构

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| name | string | 是 | 参数名称 |
| type | string | 是 | 参数类型（string/integer/boolean/object/array） |
| required | boolean | 否 | 是否必填，默认true |
| description | string | 否 | 参数描述 |

### 请求头

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Authorization | string | 是 | Bearer token |

## 输出参数

### 成功响应（200 OK）

```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": "integer",
    "name": "string",
    "description": "string or null",
    "function_name": "string",
    "module_path": "string",
    "parameters": "array",
    "return_type": "string or null",
    "is_enabled": "boolean",
    "created_at": "datetime"
  }
}
```

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| success | boolean | 操作是否成功 |
| message | string | 响应消息 |
| data.id | integer | 工具ID |
| data.name | string | 工具名称 |
| data.description | string/null | 工具描述 |
| data.function_name | string | 函数名称 |
| data.module_path | string | 模块路径 |
| data.parameters | array | 参数定义列表 |
| data.return_type | string/null | 返回类型 |
| data.is_enabled | boolean | 是否启用 |
| data.created_at | datetime | 创建时间 |

## 错误常见

| HTTP状态码 | 错误信息 | 原因 |
| :--- | :--- | :--- |
| 401 Unauthorized | 未授权 | 缺少有效令牌 |
| 400 Bad Request | 无效参数 | 参数格式不正确或缺少必填字段 |

## 示例

**请求示例：**
```bash
POST /tools
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "计算器",
  "description": "执行数学计算",
  "function_name": "calculate",
  "module_path": "src.tools.builtin.calculator",
  "parameters": [
    {
      "name": "expression",
      "type": "string",
      "required": true,
      "description": "数学表达式"
    }
  ],
  "return_type": "number"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 1,
    "name": "计算器",
    "description": "执行数学计算",
    "function_name": "calculate",
    "module_path": "src.tools.builtin.calculator",
    "parameters": [
      {
        "name": "expression",
        "type": "string",
        "required": true,
        "description": "数学表达式"
      }
    ],
    "return_type": "number",
    "is_enabled": true,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
# PromptBuilder 模块特性设计文档

## 1. 模块概述

### 1.1 模块定位
PromptBuilder 是动态提示词构建引擎，负责根据对话上下文、工具列表、技能定义等动态组装符合 LLM 格式要求的提示词。

### 1.2 核心职责
- 系统提示词构建
- 对话历史整合
- 工具描述生成
- 技能信息注入
- 提示词格式化

### 1.3 涉及用例
| 用例ID | 用例名称 | 关联程度 |
|--------|----------|----------|
| UC1 | 发起对话 | 强 |
| UC2 | 调用工具 | 强 |
| UC7 | 训练技能 | 中 |

---

## 2. 用例图

```mermaid
flowchart TD
    subgraph Actors
        DecisionEngine[DecisionEngine]
        AgentEngine[AgentEngine]
        SkillManager[SkillManager]
        ToolExecutor[ToolExecutor]
    end
    
    subgraph PromptBuilder
        UC1[构建系统提示词]
        UC2[添加对话历史]
        UC3[添加工具描述]
        UC4[添加技能]
        UC5[格式化提示词]
    end
    
    AgentEngine --> UC1
    AgentEngine --> UC2
    ToolExecutor --> UC3
    SkillManager --> UC4
    DecisionEngine --> UC5
```

### 用例说明

| 用例 | 说明 | 前置条件 | 后置条件 |
|------|------|----------|----------|
| 构建系统提示词 | 生成系统角色定义 | 系统配置已准备 | 系统提示词已生成 |
| 添加对话历史 | 将历史消息加入提示词 | 对话历史存在 | 历史已整合 |
| 添加工具描述 | 将工具定义加入提示词 | 工具列表已获取 | 工具描述已添加 |
| 添加技能 | 将技能信息加入提示词 | 技能列表已获取 | 技能已注入 |
| 格式化提示词 | 按模型要求格式化 | 各部分内容已准备 | 提示词已格式化 |

---

## 3. 时序图

### 3.1 提示词构建流程

```mermaid
sequenceDiagram
    participant DecisionEngine
    participant PromptBuilder
    participant MemorySystem
    participant ToolExecutor
    participant SkillManager
    
    DecisionEngine->>PromptBuilder: build_prompt(session_id, user_message)
    PromptBuilder->>PromptBuilder: build_system_prompt()
    
    PromptBuilder->>MemorySystem: get_recent_memory(session_id, limit=10)
    MemorySystem-->>PromptBuilder: messages
    
    PromptBuilder->>ToolExecutor: get_tools()
    ToolExecutor-->>PromptBuilder: tools
    
    PromptBuilder->>SkillManager: get_skills()
    SkillManager-->>PromptBuilder: skills
    
    PromptBuilder->>PromptBuilder: assemble_prompt(system, messages, tools, skills)
    PromptBuilder->>PromptBuilder: format_for_model()
    PromptBuilder-->>DecisionEngine: formatted_prompt
```

### 3.2 上下文压缩流程

```mermaid
sequenceDiagram
    participant PromptBuilder
    participant ContextCompressor
    participant LLMService
    
    PromptBuilder->>PromptBuilder: check_token_limit(prompt)
    
    alt 超过Token限制
        PromptBuilder->>ContextCompressor: compress(messages)
        ContextCompressor->>LLMService: summarize(chunks)
        LLMService-->>ContextCompressor: summaries
        ContextCompressor->>ContextCompressor: merge_summaries(summaries)
        ContextCompressor-->>PromptBuilder: compressed_messages
        PromptBuilder->>PromptBuilder: rebuild_prompt(compressed_messages)
    else 未超过限制
        PromptBuilder->>PromptBuilder: prompt_ok
    end
```

---

## 4. 流程图

### 4.1 提示词构建流程

```mermaid
flowchart TD
    A[开始] --> B[接收构建请求]
    B --> C[构建系统提示词]
    C --> D[获取对话历史]
    D --> E[获取工具列表]
    E --> F[获取技能列表]
    F --> G[组装提示词各部分]
    G --> H[检查Token数量]
    H --> I{超过限制?}
    I -->|是| J[调用压缩器]
    I -->|否| K[格式化提示词]
    J --> L{压缩成功?}
    L -->|是| K
    L -->|否| M[返回错误]
    K --> N[返回提示词]
    M --> O[结束]
    N --> O
```

### 4.2 系统提示词构建流程

```mermaid
flowchart TD
    A[开始] --> B[获取系统配置]
    B --> C[构建角色定义]
    C --> D[添加指令模板]
    D --> E[添加格式说明]
    E --> F[添加约束条件]
    F --> G[添加输出格式]
    G --> H[返回系统提示词]
    H --> I[结束]
```

---

## 5. 模型设计

### 5.1 数据模型

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class Message(BaseModel):
    role: str  # system/user/assistant/tool
    content: str
    tool_call: Optional[Dict[str, Any]] = None

class ToolDescription(BaseModel):
    name: str
    description: str
    parameters: List[Dict[str, Any]]

class SkillDescription(BaseModel):
    name: str
    description: str
    prompt: str

class PromptConfig(BaseModel):
    system_prompt: str
    max_tokens: int = 8192
    model_name: str = "gpt-4o"
    include_tools: bool = True
    include_skills: bool = True
    history_limit: int = 10

class BuiltPrompt(BaseModel):
    messages: List[Message]
    token_count: int
    is_compressed: bool = False
    original_token_count: Optional[int] = None
```

---

## 6. 代码模型设计

### 6.1 目录结构

```
backend/src/prompt/
├── __init__.py
├── prompt_builder.py      # 提示词构建器
├── system_prompt.py       # 系统提示词模板
├── formatters.py          # 格式转换器
└── schemas.py             # 模型定义
```

### 6.2 关键类与方法

#### PromptBuilder 类

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `build` | 构建完整提示词 | `session_id: int`, `user_message: str`, `config: Optional[PromptConfig]` | `BuiltPrompt` |
| `build_system_prompt` | 构建系统提示词 | `config: PromptConfig` | `str` |
| `add_messages` | 添加对话历史 | `messages: List[Message]` | `None` |
| `add_tools` | 添加工具描述 | `tools: List[ToolDescription]` | `None` |
| `add_skills` | 添加技能描述 | `skills: List[SkillDescription]` | `None` |
| `format` | 格式化提示词 | `model_name: str` | `BuiltPrompt` |
| `_count_tokens` | 计算Token数量 | `text: str` | `int` |

#### SystemPrompt 类

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `generate` | 生成系统提示词 | `role: str`, `instructions: List[str]`, `constraints: List[str]` | `str` |
| `get_default` | 获取默认系统提示词 | - | `str` |
| `load_template` | 从模板加载 | `template_name: str` | `str` |

#### Formatters 类

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `format_for_openai` | 格式化为OpenAI格式 | `prompt: BuiltPrompt` | `List[Dict[str, str]]` |
| `format_for_anthropic` | 格式化为Anthropic格式 | `prompt: BuiltPrompt` | `str` |
| `format_for_ollama` | 格式化为Ollama格式 | `prompt: BuiltPrompt` | `str` |

---

## 7. 与其他模块的关系

```mermaid
graph TD
    PromptBuilder --> ContextCompressor
    PromptBuilder --> MemorySystem
    PromptBuilder --> ToolExecutor
    PromptBuilder --> SkillManager
    DecisionEngine --> PromptBuilder
```

| 模块 | 关系 | 说明 |
|------|------|------|
| ContextCompressor | 依赖 | 超过Token限制时进行压缩 |
| MemorySystem | 依赖 | 获取对话历史 |
| ToolExecutor | 依赖 | 获取可用工具列表 |
| SkillManager | 依赖 | 获取可用技能列表 |
| DecisionEngine | 依赖者 | 获取构建好的提示词 |

---

## 8. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-06 | 初始版本 |
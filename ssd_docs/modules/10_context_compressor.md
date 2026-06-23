# ContextCompressor 模块特性设计文档

## 1. 模块概述

### 1.1 模块定位
ContextCompressor 是上下文压缩引擎，负责管理对话上下文的 Token 数量，通过智能摘要和裁剪确保提示词在模型限制范围内。

### 1.2 核心职责
- 上下文压缩
- 摘要生成
- Token计数
- 智能裁剪

### 1.3 涉及用例
| 用例ID | 用例名称 | 关联程度 |
|--------|----------|----------|
| UC1 | 发起对话 | 中 |
| UC2 | 调用工具 | 中 |

---

## 2. 用例图

```mermaid
flowchart TD
    subgraph Actors
        PromptBuilder[PromptBuilder]
        DecisionEngine[DecisionEngine]
        LLMService[LLMService]
    end
    
    subgraph ContextCompressor
        UC1[上下文压缩]
        UC2[生成摘要]
        UC3[Token计数]
        UC4[智能裁剪]
    end
    
    PromptBuilder --> UC1
    PromptBuilder --> UC3
    DecisionEngine --> UC2
    UC2 --> LLMService
```

### 用例说明

| 用例 | 说明 | 前置条件 | 后置条件 |
|------|------|----------|----------|
| 上下文压缩 | 压缩对话历史到Token限制内 | 对话历史存在 | 上下文已压缩 |
| 生成摘要 | 对对话片段生成摘要 | 需要压缩的内容存在 | 摘要已生成 |
| Token计数 | 计算提示词Token数量 | 提示词内容已准备 | Token数已计算 |
| 智能裁剪 | 保留重要信息，裁剪次要内容 | 超过Token限制 | 内容已裁剪 |

---

## 3. 时序图

### 3.1 上下文压缩流程

```mermaid
sequenceDiagram
    participant PromptBuilder
    participant ContextCompressor
    participant LLMService
    
    PromptBuilder->>ContextCompressor: compress(messages, max_tokens)
    ContextCompressor->>ContextCompressor: count_tokens(messages)
    
    alt 需要压缩
        ContextCompressor->>ContextCompressor: chunk_messages(messages)
        
        loop 处理每个chunk
            ContextCompressor->>LLMService: summarize(chunk)
            LLMService-->>ContextCompressor: summary
            ContextCompressor->>ContextCompressor: add_summary(summary)
        end
        
        ContextCompressor->>ContextCompressor: merge_summaries()
        ContextCompressor-->>PromptBuilder: compressed_messages
    else 不需要压缩
        ContextCompressor-->>PromptBuilder: messages
    end
```

### 3.2 智能裁剪流程

```mermaid
sequenceDiagram
    participant ContextCompressor
    participant MemorySystem
    
    ContextCompressor->>MemorySystem: get_message_importance(messages)
    MemorySystem-->>ContextCompressor: importance_scores
    
    ContextCompressor->>ContextCompressor: sort_by_importance(messages, scores)
    ContextCompressor->>ContextCompressor: trim_until_limit(messages, max_tokens)
    ContextCompressor-->>ContextCompressor: return trimmed_messages
```

---

## 4. 流程图

### 4.1 上下文压缩流程

```mermaid
flowchart TD
    A[开始] --> B[接收压缩请求]
    B --> C[计算当前Token数]
    C --> D{超过限制?}
    D -->|否| E[返回原内容]
    D -->|是| F[判断压缩策略]
    F --> G{策略类型}
    G -->|摘要| H[分块处理]
    G -->|裁剪| I[智能裁剪]
    H --> J[生成摘要]
    J --> K[合并摘要]
    I --> L[按重要性排序]
    L --> M[裁剪次要内容]
    K --> N[检查Token数]
    M --> N
    N --> O{仍超过限制?}
    O -->|是| P[递归压缩]
    O -->|否| Q[返回压缩结果]
    P --> J
    E --> R[结束]
    Q --> R
```

### 4.2 摘要生成流程

```mermaid
flowchart TD
    A[开始] --> B[获取对话片段]
    B --> C[构建摘要提示词]
    C --> D[调用LLM生成摘要]
    D --> E{生成成功?}
    E -->|是| F[验证摘要质量]
    E -->|否| G[重试]
    F --> H{质量达标?}
    H -->|是| I[返回摘要]
    H -->|否| G
    G --> D
    I --> J[结束]
```

---

## 5. 模型设计

### 5.1 数据模型

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class CompressionResult(BaseModel):
    messages: List[Dict[str, Any]]
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    method: str  # summary/trim/hybrid

class CompressionConfig(BaseModel):
    max_tokens: int = 8192
    compression_strategy: str = "hybrid"  # summary/trim/hybrid
    summary_ratio: float = 0.3
    min_messages: int = 3
```

---

## 6. 代码模型设计

### 6.1 目录结构

```
backend/src/context/
├── __init__.py
├── context_compressor.py    # 上下文压缩器
├── token_counter.py         # Token计数器
├── summarizer.py            # 摘要生成器
└── schemas.py               # 模型定义
```

### 6.2 关键类与方法

#### ContextCompressor 类

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `compress` | 压缩上下文 | `messages: List[Dict]`, `max_tokens: int`, `config: CompressionConfig` | `CompressionResult` |
| `summarize` | 生成摘要 | `text: str` | `str` |
| `trim` | 智能裁剪 | `messages: List[Dict]`, `max_tokens: int` | `List[Dict]` |
| `hybrid_compress` | 混合压缩 | `messages: List[Dict]`, `max_tokens: int` | `CompressionResult` |

#### TokenCounter 类

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `count` | 计算Token数量 | `text: str`, `model_name: str` | `int` |
| `count_messages` | 计算消息列表Token数 | `messages: List[Dict]` | `int` |
| `estimate` | 估算Token数量 | `text: str` | `int` |

#### Summarizer 类

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `summarize_chunk` | 对单个chunk生成摘要 | `chunk: str`, `max_length: int` | `str` |
| `merge_summaries` | 合并多个摘要 | `summaries: List[str]` | `str` |
| `generate_summary` | 生成完整摘要 | `messages: List[Dict]` | `str` |

---

## 7. 与其他模块的关系

```mermaid
graph TD
    ContextCompressor --> LLMService
    ContextCompressor --> MemorySystem
    PromptBuilder --> ContextCompressor
```

| 模块 | 关系 | 说明 |
|------|------|------|
| LLMService | 依赖 | 生成摘要时调用LLM |
| MemorySystem | 依赖 | 获取消息重要性评分 |
| PromptBuilder | 依赖者 | 调用压缩功能 |

---

## 8. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-06 | 初始版本 |
# AI Agent Framework - 系统设计文档 L0

## 1. 文档概述

### 1.1 文档目的
本文档基于整体架构设计，细化第二层模块设计，整合模块与用例的映射关系，输出完整的功能模块清单。

### 1.2 文档范围
- 模块功能详细描述
- 用例与模块映射
- 功能模块清单

### 1.3 参考文档
- [01_overall_architecture.md](file:///h:/007-study/020_vibingcodeing/005_harnessclaw/ssd_docs/architecture/01_overall_architecture.md)

---

## 2. 模块详细设计

### 2.1 客户端层模块

#### 2.1.1 Web UI 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | Web UI |
| **所属层级** | 客户端层 |
| **职责描述** | 提供可视化交互界面，支持对话、技能管理、系统监控 |
| **技术实现** | Vue 3 + Element Plus |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| WEB-001 | 对话界面 | 实时消息展示、输入框、消息气泡、加载状态 |
| WEB-002 | 历史记录 | 对话列表、会话选择、历史消息查看 |
| WEB-003 | 技能管理 | 技能列表、新增/编辑/删除技能 |
| WEB-004 | 系统监控 | 运行指标展示、日志查看、状态仪表盘 |
| WEB-005 | 用户设置 | 个人信息、API配置、主题设置 |

#### 2.1.2 CLI 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | CLI |
| **所属层级** | 客户端层 |
| **职责描述** | 命令行接口，支持自动化脚本和批量操作 |
| **技术实现** | Python Click / Typer |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| CLI-001 | 启动服务 | 启动/停止/重启 Agent 服务 |
| CLI-002 | 对话交互 | 命令行对话模式 |
| CLI-003 | 技能管理 | 技能的增删改查 |
| CLI-004 | 日志查看 | 查看运行日志 |
| CLI-005 | 配置管理 | 查看/修改配置 |

---

### 2.2 API网关层模块

#### 2.2.1 REST API Gateway 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | REST API Gateway |
| **所属层级** | API网关层 |
| **职责描述** | 请求路由、认证、限流、响应格式化 |
| **技术实现** | FastAPI |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| API-001 | 请求路由 | 根据URL路径路由到对应API处理函数 |
| API-002 | 认证校验 | JWT Token验证、权限检查 |
| API-003 | 请求限流 | 基于用户/IP的请求频率限制 |
| API-004 | 响应格式化 | 统一响应格式、错误处理 |
| API-005 | API文档 | 自动生成Swagger/OpenAPI文档 |

#### 2.2.2 WebSocket Server 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | WebSocket Server |
| **所属层级** | API网关层 |
| **职责描述** | 实时消息推送、双向通信 |
| **技术实现** | FastAPI WebSocket |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| WSS-001 | 连接管理 | WebSocket连接建立/断开 |
| WSS-002 | 消息推送 | 实时推送Agent响应 |
| WSS-003 | 心跳检测 | 连接状态维持 |
| WSS-004 | 消息广播 | 多客户端消息同步 |

---

### 2.3 业务逻辑层模块

#### 2.3.1 AuthService 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | AuthService |
| **所属层级** | 业务逻辑层 |
| **职责描述** | 用户认证、权限管理 |
| **技术实现** | PyJWT |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| AUTH-001 | 用户注册 | 创建新用户账户 |
| AUTH-002 | 用户登录 | 验证身份并生成Token |
| AUTH-003 | Token刷新 | 获取新的访问Token |
| AUTH-004 | 权限校验 | 检查用户操作权限 |
| AUTH-005 | 用户注销 | 失效Token |

#### 2.3.2 SessionManager 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | SessionManager |
| **所属层级** | 业务逻辑层 |
| **职责描述** | 多用户会话隔离、会话状态管理 |
| **技术实现** | 内存 + SQLite |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| SESS-001 | 创建会话 | 为用户创建新会话 |
| SESS-002 | 获取会话 | 根据会话ID获取会话状态 |
| SESS-003 | 更新会话 | 更新会话状态 |
| SESS-004 | 删除会话 | 清理过期会话 |
| SESS-005 | 会话列表 | 获取用户的会话列表 |

#### 2.3.3 AgentEngine 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | AgentEngine |
| **所属层级** | 业务逻辑层 |
| **职责描述** | 核心Agent循环、状态管理 |
| **技术实现** | Python Async |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| AGENT-001 | 执行对话 | 完整的对话执行流程 |
| AGENT-002 | 单步执行 | 执行单个思考/动作步骤 |
| AGENT-003 | 重置状态 | 重置Agent状态 |
| AGENT-004 | 中断执行 | 中断正在执行的任务 |
| AGENT-005 | 状态查询 | 获取当前Agent状态 |

#### 2.3.4 WorkflowOrchestrator 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | WorkflowOrchestrator |
| **所属层级** | 业务逻辑层 |
| **职责描述** | LangGraph图状工作流编排 |
| **技术实现** | LangGraph |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| WF-001 | 构建工作流 | 创建LangGraph状态图 |
| WF-002 | 添加节点 | 向工作流添加节点 |
| WF-003 | 添加边 | 定义节点间的路由规则 |
| WF-004 | 执行工作流 | 运行工作流并返回结果 |
| WF-005 | 工作流状态 | 获取工作流执行状态 |

#### 2.3.5 SkillManager 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | SkillManager |
| **所属层级** | 业务逻辑层 |
| **职责描述** | 技能注册、执行、学习闭环 |
| **技术实现** | Python |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| SKILL-001 | 注册技能 | 将技能添加到技能库 |
| SKILL-002 | 执行技能 | 执行指定技能 |
| SKILL-003 | 更新技能 | 修改技能定义 |
| SKILL-004 | 删除技能 | 从技能库移除技能 |
| SKILL-005 | 技能学习 | 从执行历史中学习新技能 |
| SKILL-006 | 技能列表 | 获取所有技能 |

---

### 2.4 核心能力层模块

#### 2.4.1 DecisionEngine 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | DecisionEngine |
| **所属层级** | 核心能力层 |
| **职责描述** | LLM调用、工具选择、反思机制 |
| **技术实现** | LangChain |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| DECISION-001 | 生成决策 | 根据状态生成下一步动作 |
| DECISION-002 | 调用LLM | 调用OpenAI兼容API |
| DECISION-003 | 解析工具调用 | 从LLM响应中提取工具调用 |
| DECISION-004 | 反思评估 | 对执行结果进行反思 |
| DECISION-005 | 总结回复 | 生成最终总结回复 |

#### 2.4.2 MemorySystem 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | MemorySystem |
| **所属层级** | 核心能力层 |
| **职责描述** | 短期/长期记忆、检索 |
| **技术实现** | FAISS + SQLite |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| MEM-001 | 添加记忆 | 将内容存入记忆系统 |
| MEM-002 | 检索记忆 | 根据查询检索相关记忆 |
| MEM-003 | 更新记忆 | 修改已有记忆 |
| MEM-004 | 删除记忆 | 移除指定记忆 |
| MEM-005 | 向量搜索 | 使用向量相似度搜索 |

#### 2.4.3 ToolExecutor 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | ToolExecutor |
| **所属层级** | 核心能力层 |
| **职责描述** | 工具调用、结果处理 |
| **技术实现** | Python subprocess |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| TOOL-001 | 执行工具 | 调用指定工具 |
| TOOL-002 | 验证工具调用 | 检查工具调用参数 |
| TOOL-003 | 工具注册 | 注册新工具 |
| TOOL-004 | 工具列表 | 获取所有可用工具 |
| TOOL-005 | 工具结果处理 | 解析和处理工具返回结果 |

#### 2.4.4 PromptBuilder 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | PromptBuilder |
| **所属层级** | 核心能力层 |
| **职责描述** | 动态提示词组装 |
| **技术实现** | Python |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| PROMPT-001 | 构建系统提示词 | 生成系统角色定义 |
| PROMPT-002 | 添加对话历史 | 将历史消息加入提示词 |
| PROMPT-003 | 添加工具描述 | 将工具定义加入提示词 |
| PROMPT-004 | 添加技能 | 将技能加入提示词 |
| PROMPT-005 | 格式化提示词 | 按模型要求格式化 |

#### 2.4.5 ContextCompressor 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | ContextCompressor |
| **所属层级** | 核心能力层 |
| **职责描述** | Token管理、摘要生成 |
| **技术实现** | LangChain |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| COMPRESS-001 | 上下文压缩 | 压缩对话历史到Token限制内 |
| COMPRESS-002 | 生成摘要 | 对对话片段生成摘要 |
| COMPRESS-003 | Token计数 | 计算提示词Token数量 |
| COMPRESS-004 | 智能裁剪 | 保留重要信息，裁剪次要内容 |

---

### 2.5 基础设施层模块

#### 2.5.1 LLM Service 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | LLM Service |
| **所属层级** | 基础设施层 |
| **职责描述** | OpenAI协议兼容调用 |
| **技术实现** | OpenAI Python SDK |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| LLM-001 | 聊天补全 | 调用chat_completion接口 |
| LLM-002 | 模型列表 | 获取可用模型列表 |
| LLM-003 | 配置管理 | 管理API密钥和端点 |
| LLM-004 | 请求重试 | 处理API调用失败重试 |
| LLM-005 | 流式响应 | 支持流式输出 |

#### 2.5.2 Vector DB 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | Vector DB |
| **所属层级** | 基础设施层 |
| **职责描述** | 向量存储与检索 |
| **技术实现** | FAISS / Chroma |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| VDB-001 | 创建索引 | 创建向量索引 |
| VDB-002 | 添加向量 | 插入向量数据 |
| VDB-003 | 相似性搜索 | 查找相似向量 |
| VDB-004 | 删除向量 | 移除向量数据 |
| VDB-005 | 保存/加载 | 持久化和加载索引 |

#### 2.5.3 SQLite DB 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | SQLite DB |
| **所属层级** | 基础设施层 |
| **职责描述** | 结构化数据存储 |
| **技术实现** | SQLAlchemy + SQLite |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| DB-001 | 连接管理 | 数据库连接池管理 |
| DB-002 | 数据查询 | 执行SELECT查询 |
| DB-003 | 数据插入 | 插入新记录 |
| DB-004 | 数据更新 | 更新已有记录 |
| DB-005 | 数据删除 | 删除记录 |
| DB-006 | 事务管理 | 事务提交/回滚 |

#### 2.5.4 Logging Monitor 模块
| 属性 | 描述 |
|------|------|
| **模块名称** | Logging Monitor |
| **所属层级** | 基础设施层 |
| **职责描述** | 运行日志、指标收集 |
| **技术实现** | Structlog |

**功能列表**:
| 功能ID | 功能名称 | 功能描述 |
|--------|----------|----------|
| LOG-001 | 日志记录 | 记录系统日志 |
| LOG-002 | 指标收集 | 收集运行指标 |
| LOG-003 | 日志查询 | 查询历史日志 |
| LOG-004 | 告警通知 | 异常情况告警 |
| LOG-005 | 性能监控 | 监控系统性能 |

---

## 3. 用例与模块映射

### 3.1 用例-模块映射表

| 用例ID | 用例名称 | 涉及模块 | 关键功能 |
|--------|----------|----------|----------|
| UC1 | 发起对话 | AuthService, SessionManager, AgentEngine, DecisionEngine, MemorySystem, LLM Service | AUTH-003, SESS-001/002, AGENT-001, DECISION-001/002, MEM-002, LLM-001 |
| UC2 | 调用工具 | AgentEngine, DecisionEngine, ToolExecutor, WorkflowOrchestrator | AGENT-001, DECISION-003, TOOL-001/002, WF-004 |
| UC3 | 查看历史 | AuthService, SessionManager, SQLite DB | AUTH-003, SESS-005, DB-002 |
| UC4 | 管理技能 | AuthService, SkillManager, SQLite DB | AUTH-003, SKILL-001/002/003/004/006, DB-003/004/005 |
| UC5 | 配置Agent | AuthService, SQLite DB | AUTH-003, DB-003/004 |
| UC6 | 监控运行 | AuthService, Logging Monitor | AUTH-003, LOG-002/003/005 |
| UC7 | 训练技能 | AuthService, SkillManager, DecisionEngine, LLM Service | AUTH-003, SKILL-005, DECISION-002, LLM-001 |
| UC8 | API集成 | REST API Gateway, AuthService, AgentEngine | API-001/002, AUTH-003, AGENT-001 |

### 3.2 模块-用例覆盖矩阵

| 模块 | UC1 | UC2 | UC3 | UC4 | UC5 | UC6 | UC7 | UC8 |
|------|-----|-----|-----|-----|-----|-----|-----|-----|
| Web UI | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| CLI | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| REST API Gateway | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WebSocket Server | ✓ | ✓ | - | - | - | - | - | - |
| AuthService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SessionManager | ✓ | ✓ | ✓ | - | - | - | - | ✓ |
| AgentEngine | ✓ | ✓ | - | - | - | - | - | ✓ |
| WorkflowOrchestrator | ✓ | ✓ | - | - | - | - | - | ✓ |
| SkillManager | - | - | - | ✓ | - | - | ✓ | - |
| DecisionEngine | ✓ | ✓ | - | - | - | - | ✓ | ✓ |
| MemorySystem | ✓ | - | - | - | - | - | - | ✓ |
| ToolExecutor | - | ✓ | - | - | - | - | - | ✓ |
| PromptBuilder | ✓ | ✓ | - | - | - | - | ✓ | ✓ |
| ContextCompressor | ✓ | ✓ | - | - | - | - | - | ✓ |
| LLM Service | ✓ | ✓ | - | - | - | - | ✓ | ✓ |
| Vector DB | ✓ | - | - | - | - | - | - | ✓ |
| SQLite DB | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ |
| Logging Monitor | ✓ | ✓ | - | - | - | ✓ | ✓ | ✓ |

---

## 4. 功能模块清单

### 4.1 核心功能模块

| 模块 | 功能数量 | 核心职责 |
|------|----------|----------|
| AgentEngine | 5 | 核心Agent循环 |
| DecisionEngine | 5 | LLM决策 |
| MemorySystem | 5 | 记忆管理 |
| WorkflowOrchestrator | 5 | 工作流编排 |
| SkillManager | 6 | 技能管理 |

### 4.2 支持功能模块

| 模块 | 功能数量 | 核心职责 |
|------|----------|----------|
| AuthService | 5 | 用户认证 |
| SessionManager | 5 | 会话管理 |
| ToolExecutor | 5 | 工具执行 |
| PromptBuilder | 5 | 提示词构建 |
| ContextCompressor | 4 | 上下文压缩 |

### 4.3 基础设施模块

| 模块 | 功能数量 | 核心职责 |
|------|----------|----------|
| LLM Service | 5 | LLM调用 |
| Vector DB | 5 | 向量存储 |
| SQLite DB | 6 | 数据存储 |
| Logging Monitor | 5 | 日志监控 |

### 4.4 接口模块

| 模块 | 功能数量 | 核心职责 |
|------|----------|----------|
| Web UI | 5 | 可视化界面 |
| CLI | 5 | 命令行接口 |
| REST API Gateway | 5 | REST接口 |
| WebSocket Server | 4 | 实时通信 |

---

## 5. 功能模块与用例汇总

### 5.1 功能模块总览

| 层级 | 模块数 | 功能总数 |
|------|--------|----------|
| 客户端层 | 2 | 10 |
| API网关层 | 2 | 9 |
| 业务逻辑层 | 5 | 26 |
| 核心能力层 | 5 | 25 |
| 基础设施层 | 4 | 21 |
| **总计** | **18** | **91** |

### 5.2 用例覆盖统计

| 用例 | 涉及模块数 | 涉及功能数 |
|------|------------|------------|
| UC1 - 发起对话 | 8 | 15 |
| UC2 - 调用工具 | 5 | 10 |
| UC3 - 查看历史 | 3 | 5 |
| UC4 - 管理技能 | 3 | 8 |
| UC5 - 配置Agent | 2 | 4 |
| UC6 - 监控运行 | 2 | 5 |
| UC7 - 训练技能 | 4 | 8 |
| UC8 - API集成 | 3 | 8 |

---

## 6. 与参考项目源码对应关系

### 6.1 OpenClaw 源码对应

根据 OpenClaw GitHub 源码结构（`github.com/openclaw/openclaw`）：

| 本框架模块 | OpenClaw 对应模块 | 源码路径 |
|------------|------------------|----------|
| AgentEngine | Agent Runtime | `src/agents/` |
| WorkflowOrchestrator | Agent Loop | `src/agents/` |
| MemorySystem | Memory System | `src/memory/` |
| SkillManager | Skills | `skills/` |
| REST API Gateway | Gateway | `src/gateway/` |
| WebSocket Server | Gateway | `src/gateway/` |
| LLM Service | Providers | `src/providers/` |
| ToolExecutor | Tools | `src/tools/` |
| SessionManager | Sessions | `src/sessions/` |
| CLI | CLI | `src/cli/` |

**OpenClaw 核心特性映射**：
- **Gateway模式** → 本框架 `gateway/` + `api/` 模块
- **Channels适配器** → 本框架 `gateway/platforms/` 模块
- **Memory持久化** → 本框架 `memory/` + `db/vector_db.py`
- **Skills系统** → 本框架 `skills/` 模块
- **SOUL.md模板** → 本框架 `prompt_builder.py`

### 6.2 Hermes-agent 源码对应

根据 Hermes-agent GitHub 源码结构（`github.com/NousResearch/hermes-agent`）：

| 本框架模块 | Hermes-agent 对应模块 | 源码路径 |
|------------|---------------------|----------|
| AgentEngine | AIAgent | `run_agent.py` |
| DecisionEngine | Conversation Loop | `run_agent.py` |
| PromptBuilder | Prompt Builder | `agent/prompt_builder.py` |
| ContextCompressor | Context Compressor | `agent/context_compressor.py` |
| MemorySystem | Memory Manager | `agent/memory_manager.py` |
| ToolExecutor | Tool Dispatch | `model_tools.py` |
| SessionManager | Session Storage | `hermes_state.py` |
| CLI | HermesCLI | `cli.py` / `hermes_cli/` |
| LLM Service | Provider Resolution | `agent/runtime_provider.py` |

**Hermes-agent 核心特性映射**：
- **Self-Improving Loop** → 本框架 `skill_learning.py` + `decision_engine.py` 的反思机制
- **ContextEngine ABC** → 本框架 `context_compressor.py` 的可插拔设计
- **MemoryProvider ABC** → 本框架 `memory/` 模块的抽象接口
- **Tool Registry** → 本框架 `tool_registry.py`
- **SQLite + FTS5** → 本框架 `db/sqlite_client.py`

### 6.3 架构差异对比

| 特性 | OpenClaw | Hermes-agent | 本框架 |
|------|----------|--------------|--------|
| 主循环设计 | 线性循环 | 线性循环 + 反思 | LangGraph图状工作流 |
| 部署模式 | 本地优先 | 本地/混合 | 服务端多用户 |
| 记忆系统 | 向量存储 | 文件+向量 | 短期+长期+向量 |
| 技能系统 | Markdown定义 | 动态学习 | 注册+学习闭环 |
| 扩展方式 | Channels/Skills | Plugins | 模块化+插件 |
| 技术栈 | TypeScript/Go | Python | Python |

### 6.4 落地可行性评估

#### 可行性评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 技术成熟度 | ⭐⭐⭐⭐⭐ | 基于LangChain/LangGraph成熟框架 |
| 复杂度适中 | ⭐⭐⭐⭐ | 模块划分清晰，职责单一 |
| 可扩展性 | ⭐⭐⭐⭐⭐ | 模块化设计，易于扩展 |
| 资源需求 | ⭐⭐⭐⭐ | SQLite+FAISS本地部署，资源消耗低 |
| 技术风险 | ⭐⭐⭐⭐ | 依赖成熟组件，风险可控 |
| **综合评分** | **⭐⭐⭐⭐** | **高可行性** |

#### 实施建议

1. **分阶段实施**：先实现核心模块（AgentEngine、LLM Service、MemorySystem），再扩展辅助模块
2. **复用成熟组件**：直接使用LangChain的工具集成、LangGraph的工作流、FAISS的向量检索
3. **渐进式开发**：从单用户到多用户，从简单对话到复杂工作流
4. **测试先行**：为核心模块编写单元测试和集成测试

---

## 7. 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-06 | 架构师 | 初始版本 |
| v1.1 | 2026-06 | 架构师 | 补充OpenClaw/Hermes对应关系和可行性评估 |

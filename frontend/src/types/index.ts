// 统一响应结构
export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data: T
}

// 分页响应结构
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

// 分页查询参数
export interface PaginationParams {
  page?: number
  limit?: number
}

// ============ 认证 ============
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  email: string | null
  created_at: string
}

// ============ 会话 ============
export interface Session {
  id: number
  user_id: number
  session_key: string
  title: string | null
  status: string
  created_at: string
  updated_at: string | null
}

export interface SessionCreate {
  title?: string
}

export interface SessionUpdate {
  title?: string
  status?: string
}

export interface Message {
  id: number
  session_id: number
  role: string
  content: string
  tool_call: unknown | null
  created_at: string
}

export interface MessageCreate {
  role: string
  content: string
  tool_call?: unknown | null
}

// ============ Agent ============
export interface ChatRequest {
  message: string
  session_id?: number
}

export interface ToolCallResult {
  tool_name: string
  result: string
}

export interface ChatResponse {
  response: string
  session_id: number
  iterations: number
  tool_calls: ToolCallResult[]
  error: string | null
}

export interface AgentStatus {
  status: string
  current_session_id: number | null
  iteration: number
  max_iterations: number
}

// ============ 技能 ============
export interface Skill {
  id: number
  user_id: number
  name: string
  description: string | null
  prompt: string | null
  is_enabled: boolean
  created_at: string
}

export interface SkillCreate {
  name: string
  description?: string
  prompt?: string
  is_enabled?: boolean
}

export interface SkillUpdate {
  name?: string
  description?: string
  prompt?: string
  is_enabled?: boolean
}

export interface SkillExecuteRequest {
  input: string
}

export interface ExecutionResult {
  success: boolean
  result: string
  error?: string | null
}

export interface TrainResult {
  success: boolean
  skill_id?: number
  message: string
}

// ============ 工具 ============
export interface ToolParameter {
  name: string
  type: string
  required: boolean
  description: string
}

export interface Tool {
  id: number
  name: string
  description: string | null
  function_name: string
  module_path: string
  parameters: ToolParameter[]
  return_type: string | null
  is_enabled: boolean
  created_at: string
}

export interface ToolCreate {
  name: string
  description?: string
  function_name: string
  module_path: string
  parameters: ToolParameter[]
  return_type?: string
  is_enabled?: boolean
}

export interface ToolUpdate {
  name?: string
  description?: string
  function_name?: string
  module_path?: string
  parameters?: ToolParameter[]
  return_type?: string
  is_enabled?: boolean
}

export interface ToolExecuteRequest {
  parameters: Record<string, unknown>
}

// ============ 工作流 ============
export interface WorkflowNode {
  id: string
  type?: string
  label?: string
  [key: string]: unknown
}

export interface WorkflowEdge {
  source: string
  target: string
  condition?: string
  [key: string]: unknown
}

export interface Workflow {
  id: number
  user_id: number
  name: string
  description: string | null
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  is_enabled: boolean
  created_at: string
}

export interface WorkflowCreate {
  name: string
  description?: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  is_enabled?: boolean
}

export interface WorkflowUpdate {
  name?: string
  description?: string
  nodes?: WorkflowNode[]
  edges?: WorkflowEdge[]
  is_enabled?: boolean
}

export interface WorkflowExecution {
  id: number
  workflow_id: number
  status: string
  result: string | null
  error: string | null
  started_at: string
  finished_at: string | null
}

// ============ LLM 配置 ============
export interface LlmConfig {
  id: number
  user_id: number
  name: string
  api_key: string
  api_base: string
  model_name: string
  max_tokens: number
  temperature: number
  is_active: boolean
  created_at: string
}

export interface LlmConfigCreate {
  name: string
  api_key: string
  api_base: string
  model_name: string
  max_tokens?: number
  temperature?: number
}

export interface LlmConfigUpdate {
  name?: string
  api_key?: string
  api_base?: string
  model_name?: string
  max_tokens?: number
  temperature?: number
}

// ============ 日志 ============
export interface SystemLog {
  id: number
  user_id: number
  log_type: string
  module: string
  message: string
  created_at: string
}

export interface LlmLog {
  id: number
  user_id: number
  config_id: number
  model_name: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  latency_ms: number
  status: string
  created_at: string
}

export interface LlmStatistics {
  total_calls: number
  total_tokens: number
  avg_latency_ms: number
  success_rate: number
}

export interface SystemLogParams extends PaginationParams {
  log_type?: string
  module?: string
}

export interface LlmLogParams extends PaginationParams {
  config_id?: number
  status?: string
}

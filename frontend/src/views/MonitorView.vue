<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Activity, Zap, Clock, CheckCircle, Cpu, RefreshCw } from 'lucide-vue-next'
import { logsApi } from '@/api/logs'
import { agentApi } from '@/api/agent'
import type {
  SystemLog,
  LlmLog,
  LlmStatistics,
  AgentStatus,
  PaginatedData,
} from '@/types'
import Badge from '@/components/ui/Badge.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import LoadingState from '@/components/shared/LoadingState.vue'
import ErrorState from '@/components/shared/ErrorState.vue'

const activeTab = ref<'system' | 'llm'>('system')

// 统计
const stats = ref<LlmStatistics | null>(null)
const statsLoading = ref(true)
const statsError = ref('')

// Agent 状态
const agentSt = ref<AgentStatus | null>(null)

// 系统日志
const sysLogs = ref<SystemLog[]>([])
const sysLoading = ref(false)
const sysError = ref('')
const sysPage = ref(1)
const sysLimit = ref(20)
const sysTotal = ref(0)
const sysFilter = reactive({ log_type: '', module: '' })

// LLM 日志
const llmLogs = ref<LlmLog[]>([])
const llmLoading = ref(false)
const llmError = ref('')
const llmPage = ref(1)
const llmLimit = ref(20)
const llmTotal = ref(0)
const llmLoaded = ref(false)

async function loadStats(): Promise<void> {
  statsLoading.value = true
  statsError.value = ''
  try {
    stats.value = await logsApi.llmStatistics()
  } catch (e) {
    statsError.value = e instanceof Error ? e.message : '加载统计失败'
  } finally {
    statsLoading.value = false
  }
}

async function loadAgentStatus(): Promise<void> {
  try {
    agentSt.value = await agentApi.status()
  } catch {
    agentSt.value = null
  }
}

async function loadSysLogs(): Promise<void> {
  sysLoading.value = true
  sysError.value = ''
  try {
    const res: PaginatedData<SystemLog> = await logsApi.system({
      page: sysPage.value,
      limit: sysLimit.value,
      log_type: sysFilter.log_type || undefined,
      module: sysFilter.module || undefined,
    })
    sysLogs.value = res.items
    sysTotal.value = res.total
  } catch (e) {
    sysError.value = e instanceof Error ? e.message : '加载日志失败'
  } finally {
    sysLoading.value = false
  }
}

async function loadLlmLogs(): Promise<void> {
  llmLoading.value = true
  llmError.value = ''
  try {
    const res: PaginatedData<LlmLog> = await logsApi.llm({
      page: llmPage.value,
      limit: llmLimit.value,
    })
    llmLogs.value = res.items
    llmTotal.value = res.total
  } catch (e) {
    llmError.value = e instanceof Error ? e.message : '加载日志失败'
  } finally {
    llmLoading.value = false
    llmLoaded.value = true
  }
}

function switchTab(tab: 'system' | 'llm'): void {
  activeTab.value = tab
  if (tab === 'llm' && !llmLoaded.value) {
    loadLlmLogs()
  }
}

function applySysFilter(): void {
  sysPage.value = 1
  loadSysLogs()
}

function formatRate(v: number): string {
  return (v > 1 ? v : v * 100).toFixed(1) + '%'
}

function latencyColor(ms: number): string {
  if (ms < 1000) return 'text-status-success'
  if (ms < 3000) return 'text-status-warning'
  return 'text-status-error'
}

function logTypeVariant(t: string): 'error' | 'warning' | 'cyan' | 'default' {
  if (t === 'error') return 'error'
  if (t === 'warning') return 'warning'
  if (t === 'info') return 'cyan'
  return 'default'
}

function fmtDate(s: string): string {
  return new Date(s).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
  loadAgentStatus()
  loadSysLogs()
})
</script>

<template>
  <div class="space-y-6 p-6">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div class="card p-4">
        <div class="flex items-center gap-2 text-base-500">
          <Activity class="h-4 w-4" />
          <span class="text-label">总调用数</span>
        </div>
        <p class="mt-2 font-mono text-2xl font-bold text-zinc-100">{{ stats?.total_calls ?? '—' }}</p>
      </div>
      <div class="card p-4">
        <div class="flex items-center gap-2 text-base-500">
          <Zap class="h-4 w-4 text-amber" />
          <span class="text-label">总 Token</span>
        </div>
        <p class="mt-2 font-mono text-2xl font-bold text-amber">{{ stats?.total_tokens ?? '—' }}</p>
      </div>
      <div class="card p-4">
        <div class="flex items-center gap-2 text-base-500">
          <Clock class="h-4 w-4 text-cyan" />
          <span class="text-label">平均延迟</span>
        </div>
        <p class="mt-2 font-mono text-2xl font-bold text-cyan">
          {{ stats ? Math.round(stats.avg_latency_ms) + 'ms' : '—' }}
        </p>
      </div>
      <div class="card p-4">
        <div class="flex items-center gap-2 text-base-500">
          <CheckCircle class="h-4 w-4 text-status-success" />
          <span class="text-label">成功率</span>
        </div>
        <p class="mt-2 font-mono text-2xl font-bold text-status-success">
          {{ stats ? formatRate(stats.success_rate) : '—' }}
        </p>
      </div>
    </div>

    <!-- Agent 状态 -->
    <div class="card flex items-center gap-4 p-4">
      <Cpu class="h-5 w-5 text-amber" />
      <div class="flex items-center gap-2">
        <div
          class="h-2 w-2 rounded-full"
          :class="{
            'bg-status-success': agentSt?.status === 'idle',
            'bg-amber animate-pulse': agentSt?.status === 'running',
            'bg-status-error': agentSt?.status === 'error',
            'bg-base-500': !agentSt,
          }"
        />
        <span class="text-sm text-zinc-300">Agent 状态: {{ agentSt?.status || '未知' }}</span>
      </div>
      <span class="font-mono text-xs text-base-500">
        会话: {{ agentSt?.current_session_id ?? '—' }}
      </span>
      <span class="font-mono text-xs text-base-500">
        迭代: {{ agentSt?.iteration ?? 0 }}/{{ agentSt?.max_iterations ?? 0 }}
      </span>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-1 border-b border-base-700">
      <button
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'system' ? 'border-amber text-amber' : 'border-transparent text-base-500 hover:text-zinc-300'"
        @click="switchTab('system')"
      >系统日志</button>
      <button
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'llm' ? 'border-amber text-amber' : 'border-transparent text-base-500 hover:text-zinc-300'"
        @click="switchTab('llm')"
      >LLM 日志</button>
    </div>

    <!-- 系统日志 -->
    <div v-show="activeTab === 'system'">
      <div class="mb-3 flex items-center gap-3">
        <select v-model="sysFilter.log_type" class="input-base w-32" @change="applySysFilter">
          <option value="">全部类型</option>
          <option value="error">error</option>
          <option value="warning">warning</option>
          <option value="info">info</option>
        </select>
        <select v-model="sysFilter.module" class="input-base w-40" @change="applySysFilter">
          <option value="">全部模块</option>
          <option value="agent">agent</option>
          <option value="session">session</option>
          <option value="skill">skill</option>
          <option value="tool">tool</option>
          <option value="workflow">workflow</option>
          <option value="llm">llm</option>
          <option value="auth">auth</option>
        </select>
        <button class="btn-secondary" @click="loadSysLogs">
          <RefreshCw class="h-4 w-4" />刷新
        </button>
      </div>
      <div class="card overflow-hidden">
        <LoadingState v-if="sysLoading" text="加载日志..." />
        <ErrorState v-else-if="sysError" :text="sysError" @retry="loadSysLogs" />
        <EmptyState v-else-if="sysLogs.length === 0" text="暂无日志" />
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="border-b border-base-700 bg-base-850 text-left">
              <tr>
                <th class="px-4 py-2 text-label">ID</th>
                <th class="px-4 py-2 text-label">类型</th>
                <th class="px-4 py-2 text-label">模块</th>
                <th class="px-4 py-2 text-label">消息</th>
                <th class="px-4 py-2 text-label">时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-base-700">
              <tr v-for="log in sysLogs" :key="log.id" class="hover:bg-base-850">
                <td class="px-4 py-2 font-mono text-xs text-base-500">{{ log.id }}</td>
                <td class="px-4 py-2"><Badge :variant="logTypeVariant(log.log_type)" dot>{{ log.log_type }}</Badge></td>
                <td class="px-4 py-2 font-mono text-xs text-cyan">{{ log.module }}</td>
                <td class="max-w-md truncate px-4 py-2 text-zinc-300">{{ log.message }}</td>
                <td class="px-4 py-2 font-mono text-xs text-base-500">{{ fmtDate(log.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          v-if="sysLogs.length > 0"
          :page="sysPage" :limit="sysLimit" :total="sysTotal"
          @change="(p) => { sysPage = p; loadSysLogs() }"
        />
      </div>
    </div>

    <!-- LLM 日志 -->
    <div v-show="activeTab === 'llm'">
      <div class="card overflow-hidden">
        <LoadingState v-if="llmLoading" text="加载日志..." />
        <ErrorState v-else-if="llmError" :text="llmError" @retry="loadLlmLogs" />
        <EmptyState v-else-if="llmLogs.length === 0" text="暂无 LLM 日志" />
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="border-b border-base-700 bg-base-850 text-left">
              <tr>
                <th class="px-4 py-2 text-label">ID</th>
                <th class="px-4 py-2 text-label">模型</th>
                <th class="px-4 py-2 text-label">Prompt</th>
                <th class="px-4 py-2 text-label">Completion</th>
                <th class="px-4 py-2 text-label">Total</th>
                <th class="px-4 py-2 text-label">延迟</th>
                <th class="px-4 py-2 text-label">状态</th>
                <th class="px-4 py-2 text-label">时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-base-700">
              <tr v-for="log in llmLogs" :key="log.id" class="hover:bg-base-850">
                <td class="px-4 py-2 font-mono text-xs text-base-500">{{ log.id }}</td>
                <td class="px-4 py-2 font-mono text-xs text-cyan">{{ log.model_name }}</td>
                <td class="px-4 py-2 font-mono text-xs text-zinc-400">{{ log.prompt_tokens }}</td>
                <td class="px-4 py-2 font-mono text-xs text-zinc-400">{{ log.completion_tokens }}</td>
                <td class="px-4 py-2 font-mono text-xs text-amber">{{ log.total_tokens }}</td>
                <td class="px-4 py-2 font-mono text-xs" :class="latencyColor(log.latency_ms)">{{ log.latency_ms }}ms</td>
                <td class="px-4 py-2"><Badge :variant="log.status === 'success' ? 'success' : 'error'" dot>{{ log.status }}</Badge></td>
                <td class="px-4 py-2 font-mono text-xs text-base-500">{{ fmtDate(log.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          v-if="llmLogs.length > 0"
          :page="llmPage" :limit="llmLimit" :total="llmTotal"
          @change="(p) => { llmPage = p; loadLlmLogs() }"
        />
      </div>
    </div>
  </div>
</template>

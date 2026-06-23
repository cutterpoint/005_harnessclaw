<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  Workflow, Plus, Play, History, Pencil, Trash2, GitBranch, Share2,
  Calendar, CheckCircle2, XCircle,
} from 'lucide-vue-next'
import { workflowsApi } from '@/api/workflows'
import type {
  Workflow as WorkflowType, WorkflowNode, WorkflowEdge, WorkflowExecution,
} from '@/types'
import BaseModal from '@/components/ui/BaseModal.vue'
import Badge from '@/components/ui/Badge.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import LoadingState from '@/components/shared/LoadingState.vue'
import ErrorState from '@/components/shared/ErrorState.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'

// 列表状态
const workflows = ref<WorkflowType[]>([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const limit = ref(10)
const total = ref(0)

// 执行结果提示
const toast = ref<{ type: 'success' | 'error'; text: string } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(type: 'success' | 'error', text: string): void {
  toast.value = { type, text }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = null), 4000)
}

// 表单弹窗
const formOpen = ref(false)
const isEdit = ref(false)
const formId = ref<number | null>(null)
const formName = ref('')
const formDesc = ref('')
const formEnabled = ref(true)
const nodesJson = ref('[]')
const edgesJson = ref('[]')
const formError = ref('')
const saving = ref(false)

// 历史弹窗
const historyOpen = ref(false)
const historyList = ref<WorkflowExecution[]>([])
const historyLoading = ref(false)
const historyName = ref('')

// 删除确认
const deleteId = ref<number | null>(null)

async function fetchList(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const res = await workflowsApi.list({ page: page.value, limit: limit.value })
    workflows.value = res.items
    total.value = res.total
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number): void {
  page.value = p
  fetchList()
}

function openCreate(): void {
  isEdit.value = false
  formId.value = null
  formName.value = ''
  formDesc.value = ''
  formEnabled.value = true
  nodesJson.value = '[]'
  edgesJson.value = '[]'
  formError.value = ''
  formOpen.value = true
}

function openEdit(w: WorkflowType): void {
  isEdit.value = true
  formId.value = w.id
  formName.value = w.name
  formDesc.value = w.description ?? ''
  formEnabled.value = w.is_enabled
  nodesJson.value = JSON.stringify(w.nodes ?? [], null, 2)
  edgesJson.value = JSON.stringify(w.edges ?? [], null, 2)
  formError.value = ''
  formOpen.value = true
}

async function saveForm(): Promise<void> {
  formError.value = ''
  if (!formName.value.trim()) {
    formError.value = '请填写工作流名称'
    return
  }
  let nodes: WorkflowNode[]
  let edges: WorkflowEdge[]
  try {
    nodes = JSON.parse(nodesJson.value)
    edges = JSON.parse(edgesJson.value)
  } catch {
    formError.value = '节点或边 JSON 格式错误，请检查'
    return
  }
  saving.value = true
  try {
    const payload = {
      name: formName.value.trim(),
      description: formDesc.value.trim(),
      nodes,
      edges,
      is_enabled: formEnabled.value,
    }
    if (isEdit.value && formId.value !== null) {
      await workflowsApi.update(formId.value, payload)
      showToast('success', '工作流已更新')
    } else {
      await workflowsApi.create(payload)
      showToast('success', '工作流已创建')
    }
    formOpen.value = false
    fetchList()
  } catch (e: unknown) {
    formError.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function executeWorkflow(w: WorkflowType): Promise<void> {
  try {
    const res = await workflowsApi.execute(w.id)
    if (res.success) {
      showToast('success', `执行成功：${res.result}`)
    } else {
      showToast('error', `执行失败：${res.error ?? '未知错误'}`)
    }
  } catch (e: unknown) {
    showToast('error', e instanceof Error ? e.message : '执行失败')
  }
}

async function openHistory(w: WorkflowType): Promise<void> {
  historyOpen.value = true
  historyName.value = w.name
  historyList.value = []
  historyLoading.value = true
  try {
    historyList.value = await workflowsApi.executions(w.id)
  } catch (e: unknown) {
    showToast('error', e instanceof Error ? e.message : '加载历史失败')
  } finally {
    historyLoading.value = false
  }
}

async function doDelete(): Promise<void> {
  if (deleteId.value === null) return
  try {
    await workflowsApi.delete(deleteId.value)
    showToast('success', '工作流已删除')
    if (workflows.value.length === 1 && page.value > 1) page.value -= 1
    fetchList()
  } catch (e: unknown) {
    showToast('error', e instanceof Error ? e.message : '删除失败')
  } finally {
    deleteId.value = null
  }
}

function formatDate(s: string): string {
  return new Date(s).toLocaleString('zh-CN')
}

function statusVariant(status: string): 'success' | 'warning' | 'error' | 'default' {
  const s = status.toLowerCase()
  if (['success', 'completed', 'succeeded'].includes(s)) return 'success'
  if (['running', 'pending', 'queued'].includes(s)) return 'warning'
  if (['failed', 'error'].includes(s)) return 'error'
  return 'default'
}

onMounted(fetchList)
</script>

<template>
  <div class="mx-auto max-w-6xl p-6">
    <!-- 头部 -->
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg border border-amber/30 bg-amber/10">
          <Workflow class="h-5 w-5 text-amber" />
        </div>
        <div>
          <h1 class="text-xl font-semibold text-zinc-100">工作流管理</h1>
          <p class="font-mono text-xs text-base-500">编排 Agent 任务流程</p>
        </div>
      </div>
      <button class="btn-primary" @click="openCreate">
        <Plus class="h-4 w-4" />
        新建工作流
      </button>
    </div>

    <!-- 执行结果提示 -->
    <div
      v-if="toast"
      :class="[
        'mb-4 flex items-center gap-2 rounded-md border px-4 py-3 text-sm',
        toast.type === 'success'
          ? 'border-status-success/30 bg-status-success/10 text-status-success'
          : 'border-status-error/30 bg-status-error/10 text-status-error',
      ]"
    >
      <CheckCircle2 v-if="toast.type === 'success'" class="h-4 w-4 flex-shrink-0" />
      <XCircle v-else class="h-4 w-4 flex-shrink-0" />
      <span class="font-mono break-all">{{ toast.text }}</span>
    </div>

    <!-- 内容区 -->
    <LoadingState v-if="loading" text="加载工作流..." />
    <ErrorState v-else-if="error" :text="error" @retry="fetchList" />
    <EmptyState
      v-else-if="workflows.length === 0"
      text="暂无工作流"
      description="点击右上角新建工作流开始编排"
    />
    <template v-else>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div v-for="w in workflows" :key="w.id" class="card card-hover flex flex-col p-4">
          <div class="mb-2 flex items-center justify-between gap-2">
            <h3 class="truncate font-semibold text-zinc-100">{{ w.name }}</h3>
            <Badge :variant="w.is_enabled ? 'success' : 'default'" dot>
              {{ w.is_enabled ? '启用' : '停用' }}
            </Badge>
          </div>
          <p class="mb-3 min-h-[2.5rem] text-sm text-zinc-400">
            {{ w.description || '暂无描述' }}
          </p>
          <div class="mb-3 flex flex-wrap items-center gap-4 font-mono text-xs text-base-500">
            <span class="inline-flex items-center gap-1">
              <GitBranch class="h-3.5 w-3.5" />{{ w.nodes?.length ?? 0 }} 节点
            </span>
            <span class="inline-flex items-center gap-1">
              <Share2 class="h-3.5 w-3.5" />{{ w.edges?.length ?? 0 }} 边
            </span>
            <span class="inline-flex items-center gap-1">
              <Calendar class="h-3.5 w-3.5" />{{ formatDate(w.created_at) }}
            </span>
          </div>
          <div class="mt-auto flex items-center gap-1 border-t border-base-700 pt-3">
            <button class="btn-primary px-3 py-1.5 text-xs" @click="executeWorkflow(w)">
              <Play class="h-3.5 w-3.5" />执行
            </button>
            <button class="btn-ghost text-xs" @click="openHistory(w)">
              <History class="h-3.5 w-3.5" />历史
            </button>
            <button class="btn-ghost text-xs" @click="openEdit(w)">
              <Pencil class="h-3.5 w-3.5" />编辑
            </button>
            <button
              class="btn-ghost text-xs text-status-error hover:bg-status-error/10"
              @click="deleteId = w.id"
            >
              <Trash2 class="h-3.5 w-3.5" />删除
            </button>
          </div>
        </div>
      </div>
      <Pagination :page="page" :limit="limit" :total="total" @change="onPageChange" />
    </template>

    <!-- 新建/编辑弹窗 -->
    <BaseModal
      :model-value="formOpen"
      :title="isEdit ? '编辑工作流' : '新建工作流'"
      width="max-w-2xl"
      @update:model-value="formOpen = $event"
    >
      <div class="space-y-4">
        <div>
          <label class="text-label mb-1 block">名称</label>
          <input v-model="formName" class="input-base" placeholder="工作流名称" />
        </div>
        <div>
          <label class="text-label mb-1 block">描述</label>
          <textarea v-model="formDesc" rows="2" class="input-base" placeholder="工作流描述（可选）" />
        </div>
        <div class="flex items-center gap-2">
          <input id="wf-enabled" v-model="formEnabled" type="checkbox" class="h-4 w-4 accent-amber" />
          <label for="wf-enabled" class="text-sm text-zinc-300">启用工作流</label>
        </div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label class="text-label mb-1 block">节点 JSON</label>
            <textarea v-model="nodesJson" rows="8" class="input-base font-mono text-xs" />
          </div>
          <div>
            <label class="text-label mb-1 block">边 JSON</label>
            <textarea v-model="edgesJson" rows="8" class="input-base font-mono text-xs" />
          </div>
        </div>
        <p v-if="formError" class="text-sm text-status-error">{{ formError }}</p>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="formOpen = false">取消</button>
        <button class="btn-primary" :disabled="saving" @click="saveForm">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </BaseModal>

    <!-- 历史弹窗 -->
    <BaseModal
      :model-value="historyOpen"
      :title="`执行历史 - ${historyName}`"
      width="max-w-2xl"
      @update:model-value="historyOpen = $event"
    >
      <LoadingState v-if="historyLoading" text="加载历史..." />
      <EmptyState v-else-if="historyList.length === 0" text="暂无执行记录" />
      <div v-else class="max-h-[60vh] space-y-3 overflow-y-auto pr-1">
        <div
          v-for="ex in historyList"
          :key="ex.id"
          class="rounded-md border border-base-700 bg-base-900 p-3"
        >
          <div class="mb-1 flex items-center justify-between">
            <Badge :variant="statusVariant(ex.status)" dot>{{ ex.status }}</Badge>
            <span class="font-mono text-xs text-base-500">#{{ ex.id }}</span>
          </div>
          <p v-if="ex.result" class="mb-1 break-all text-xs text-zinc-300">
            <span class="text-base-500">结果：</span>{{ ex.result }}
          </p>
          <p v-if="ex.error" class="mb-1 break-all text-xs text-status-error">
            <span class="text-base-500">错误：</span>{{ ex.error }}
          </p>
          <div class="font-mono text-xs text-base-500">
            开始：{{ formatDate(ex.started_at) }}
            <span v-if="ex.finished_at"> · 完成：{{ formatDate(ex.finished_at) }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="historyOpen = false">关闭</button>
      </template>
    </BaseModal>

    <!-- 删除确认 -->
    <ConfirmDialog
      :model-value="deleteId !== null"
      title="删除工作流"
      text="确定要删除此工作流吗？此操作不可撤销。"
      @update:model-value="deleteId = $event ? deleteId : null"
      @confirm="doDelete"
    />
  </div>
</template>

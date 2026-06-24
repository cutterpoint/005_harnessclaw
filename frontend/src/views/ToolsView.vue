<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Play, Pencil, Trash2, Wrench, X } from 'lucide-vue-next'
import { toolsApi } from '@/api/tools'
import type { Tool, ToolParameter, ExecutionResult } from '@/types'
import BaseModal from '@/components/ui/BaseModal.vue'
import Badge from '@/components/ui/Badge.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import LoadingState from '@/components/shared/LoadingState.vue'
import ErrorState from '@/components/shared/ErrorState.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'

const tools = ref<Tool[]>([])
const loading = ref(false)
const loadError = ref('')
const toast = ref<{ type: 'success' | 'error'; text: string } | null>(null)
const enabledOnly = ref(false)
const formOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  name: '', description: '', function_name: '', module_path: '',
  return_type: '', is_enabled: true, parameters: [] as ToolParameter[],
})
const execOpen = ref(false)
const execTool = ref<Tool | null>(null)
const execParams = reactive<Record<string, string>>({})
const execResult = ref<ExecutionResult | null>(null)
const executing = ref(false)
const deleteOpen = ref(false)
const deleteTarget = ref<Tool | null>(null)

function notify(type: 'success' | 'error', text: string): void {
  toast.value = { type, text }
  setTimeout(() => (toast.value = null), 3500)
}
const formatDate = (s: string) => new Date(s).toLocaleString('zh-CN')
async function loadTools(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    tools.value = await toolsApi.list({ enabled_only: enabledOnly.value })
  } catch (e) {
    loadError.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
function resetForm(): void {
  editingId.value = null
  Object.assign(form, {
    name: '', description: '', function_name: '', module_path: '',
    return_type: '', is_enabled: true, parameters: [],
  })
}
function openCreate(): void { resetForm(); formOpen.value = true }
function openEdit(t: Tool): void {
  resetForm()
  editingId.value = t.id
  Object.assign(form, {
    name: t.name, description: t.description ?? '', function_name: t.function_name,
    module_path: t.module_path, return_type: t.return_type ?? '', is_enabled: t.is_enabled,
    parameters: t.parameters.map((p) => ({ ...p })),
  })
  formOpen.value = true
}
const addParam = () => form.parameters.push({ name: '', type: 'string', required: false, description: '' })
const removeParam = (i: number) => form.parameters.splice(i, 1)
async function saveTool(): Promise<void> {
  if (!form.name || !form.function_name || !form.module_path)
    return notify('error', '请填写名称、函数名和模块路径')
  saving.value = true
  const payload = {
    name: form.name, description: form.description || undefined, function_name: form.function_name,
    module_path: form.module_path, parameters: form.parameters.filter((p) => p.name),
    return_type: form.return_type || undefined, is_enabled: form.is_enabled,
  }
  try {
    if (editingId.value) { await toolsApi.update(editingId.value, payload); notify('success', '工具已更新') }
    else { await toolsApi.create(payload); notify('success', '工具已注册') }
    formOpen.value = false
    await loadTools()
  } catch (e) {
    notify('error', (e as Error).message)
  } finally {
    saving.value = false
  }
}
function openExec(t: Tool): void {
  execTool.value = t
  execResult.value = null
  Object.keys(execParams).forEach((k) => delete execParams[k])
  t.parameters.forEach((p) => (execParams[p.name] = ''))
  execOpen.value = true
}
function coerce(v: string, t: string): unknown {
  if (t === 'integer' || t === 'number') { const n = Number(v); return Number.isNaN(n) ? v : n }
  if (t === 'boolean') return v === 'true' || v === '1'
  try { return JSON.parse(v) } catch { return v }
}
async function runExec(): Promise<void> {
  if (!execTool.value) return
  executing.value = true
  execResult.value = null
  const params: Record<string, unknown> = {}
  execTool.value.parameters.forEach((p) => {
    if (execParams[p.name] !== '') params[p.name] = coerce(execParams[p.name], p.type)
  })
  try {
    execResult.value = await toolsApi.execute(execTool.value.id, { parameters: params })
  } catch (e) {
    execResult.value = { success: false, result: '', error: (e as Error).message }
  } finally {
    executing.value = false
  }
}
function openDelete(t: Tool): void { deleteTarget.value = t; deleteOpen.value = true }
async function confirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  try {
    await toolsApi.delete(deleteTarget.value.id)
    notify('success', '工具已删除')
    await loadTools()
  } catch (e) {
    notify('error', (e as Error).message)
  }
}
onMounted(loadTools)
</script>

<template>
  <div class="mx-auto max-w-7xl p-6">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg border border-amber/30 bg-amber/10">
          <Wrench class="h-5 w-5 text-amber" />
        </div>
        <div>
          <h1 class="text-xl font-semibold text-zinc-100">工具管理</h1>
          <p class="font-mono text-xs text-base-500">注册、编辑与执行 Agent 可用工具</p>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <label class="flex cursor-pointer items-center gap-2 text-sm text-zinc-400">
          <input v-model="enabledOnly" type="checkbox" class="h-4 w-4 rounded border-base-600 bg-base-900 accent-amber" @change="loadTools" />
          <span>仅显示启用</span>
        </label>
        <button class="btn-primary" @click="openCreate">
          <Plus class="h-4 w-4" /> 注册工具
        </button>
      </div>
    </div>

    <!-- Toast -->
    <div
      v-if="toast"
      :class="['mb-4 rounded-md border px-4 py-2.5 text-sm', toast.type === 'success' ? 'border-status-success/30 bg-status-success/10 text-status-success' : 'border-status-error/30 bg-status-error/10 text-status-error']"
    >
      {{ toast.text }}
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <LoadingState v-if="loading" text="正在加载工具列表..." />
      <ErrorState v-else-if="loadError" :text="loadError" @retry="loadTools" />
      <EmptyState v-else-if="tools.length === 0" text="暂无工具" description="点击「注册工具」添加第一个工具" />
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-base-850">
            <tr class="border-b border-base-700 text-left">
              <th class="px-4 py-3 text-label font-medium">名称</th>
              <th class="px-4 py-3 text-label font-medium">函数名</th>
              <th class="px-4 py-3 text-label font-medium">模块路径</th>
              <th class="px-4 py-3 text-label font-medium">参数</th>
              <th class="px-4 py-3 text-label font-medium">返回类型</th>
              <th class="px-4 py-3 text-label font-medium">状态</th>
              <th class="px-4 py-3 text-right text-label font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-base-800">
            <tr v-for="tool in tools" :key="tool.id" class="transition-colors hover:bg-base-800/50">
              <td class="px-4 py-3">
                <div class="font-medium text-zinc-200">{{ tool.name }}</div>
                <div v-if="tool.description" class="mt-0.5 text-xs text-base-500">{{ tool.description }}</div>
                <div class="mt-0.5 font-mono text-xs text-base-600">{{ formatDate(tool.created_at) }}</div>
              </td>
              <td class="px-4 py-3 font-mono text-xs text-cyan">{{ tool.function_name }}</td>
              <td class="px-4 py-3 font-mono text-xs text-base-500">{{ tool.module_path }}</td>
              <td class="px-4 py-3 text-center font-mono text-zinc-300">{{ tool.parameters.length }}</td>
              <td class="px-4 py-3 font-mono text-xs text-zinc-400">{{ tool.return_type || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="tool.is_enabled ? 'success' : 'default'" dot>{{ tool.is_enabled ? '启用' : '禁用' }}</Badge>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-end gap-1">
                  <button class="btn-ghost" title="执行" @click="openExec(tool)"><Play class="h-4 w-4" /></button>
                  <button class="btn-ghost" title="编辑" @click="openEdit(tool)"><Pencil class="h-4 w-4" /></button>
                  <button class="btn-ghost text-status-error" title="删除" @click="openDelete(tool)"><Trash2 class="h-4 w-4" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <BaseModal v-model="formOpen" :title="editingId ? '编辑工具' : '注册工具'" width="max-w-2xl">
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-label mb-1.5 block">名称</label>
            <input v-model="form.name" class="input-base" placeholder="如：网页搜索" />
          </div>
          <div>
            <label class="text-label mb-1.5 block">返回类型</label>
            <input v-model="form.return_type" class="input-base" placeholder="如：string" />
          </div>
        </div>
        <div>
          <label class="text-label mb-1.5 block">描述</label>
          <input v-model="form.description" class="input-base" placeholder="工具用途说明" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-label mb-1.5 block">函数名</label>
            <input v-model="form.function_name" class="input-base font-mono" placeholder="execute_search" />
          </div>
          <div>
            <label class="text-label mb-1.5 block">模块路径</label>
            <input v-model="form.module_path" class="input-base font-mono" placeholder="tools.search" />
          </div>
        </div>
        <label class="flex items-center gap-2 text-sm text-zinc-300">
          <input v-model="form.is_enabled" type="checkbox" class="h-4 w-4 rounded border-base-600 bg-base-900 accent-amber" />
          启用此工具
        </label>
        <div>
          <div class="mb-2 flex items-center justify-between">
            <span class="text-label">参数列表</span>
            <button class="btn-ghost" @click="addParam"><Plus class="h-3.5 w-3.5" /> 添加参数</button>
          </div>
          <div v-if="form.parameters.length === 0" class="rounded-md border border-dashed border-base-700 px-3 py-4 text-center text-xs text-base-500">暂无参数</div>
          <div v-else class="space-y-2">
            <div v-for="(param, i) in form.parameters" :key="i" class="grid grid-cols-12 items-center gap-2 rounded-md border border-base-700 bg-base-900 px-3 py-2">
              <input v-model="param.name" class="input-base col-span-3" placeholder="参数名" />
              <input v-model="param.type" class="input-base col-span-3 font-mono" placeholder="类型" />
              <label class="col-span-2 flex items-center gap-1.5 text-xs text-zinc-400">
                <input v-model="param.required" type="checkbox" class="h-3.5 w-3.5 rounded border-base-600 bg-base-900 accent-amber" /> 必填
              </label>
              <input v-model="param.description" class="input-base col-span-3" placeholder="说明" />
              <button class="col-span-1 flex justify-center text-base-500 hover:text-status-error" @click="removeParam(i)"><X class="h-4 w-4" /></button>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="formOpen = false">取消</button>
        <button class="btn-primary" :disabled="saving" @click="saveTool">{{ saving ? '保存中...' : '保存' }}</button>
      </template>
    </BaseModal>

    <!-- Execute Modal -->
    <BaseModal v-model="execOpen" :title="`执行工具：${execTool?.name ?? ''}`" width="max-w-xl">
      <div class="space-y-4">
        <p v-if="execTool && execTool.parameters.length === 0" class="text-sm text-base-500">该工具无参数，可直接执行。</p>
        <div v-else class="space-y-3">
          <div v-for="param in execTool?.parameters" :key="param.name">
            <label class="text-label mb-1.5 flex items-center gap-2">
              <span>{{ param.name }}</span>
              <span class="font-mono text-cyan">{{ param.type }}</span>
              <span v-if="param.required" class="text-status-error">*</span>
            </label>
            <input v-model="execParams[param.name]" class="input-base" :placeholder="param.description || `输入 ${param.type} 值`" />
          </div>
        </div>
        <div v-if="execResult" class="rounded-md border border-base-700 bg-base-950 p-3">
          <div class="mb-1.5">
            <Badge :variant="execResult.success ? 'success' : 'error'" dot>{{ execResult.success ? '成功' : '失败' }}</Badge>
          </div>
          <pre class="max-h-60 overflow-auto whitespace-pre-wrap break-all font-mono text-xs text-zinc-300">{{ execResult.success ? execResult.result : execResult.error }}</pre>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="execOpen = false">关闭</button>
        <button class="btn-primary" :disabled="executing" @click="runExec"><Play class="h-4 w-4" /> {{ executing ? '执行中...' : '执行' }}</button>
      </template>
    </BaseModal>

    <!-- Delete Confirm -->
    <ConfirmDialog
      v-model="deleteOpen"
      :title="`删除工具：${deleteTarget?.name ?? ''}`"
      :text="`确定要删除工具「${deleteTarget?.name ?? ''}」吗？此操作不可撤销。`"
      @confirm="confirmDelete"
    />
  </div>
</template>

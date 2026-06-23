<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  Plus, Search, Pencil, Trash2, Zap, Key, Server, Cpu,
  Hash, Thermometer, Calendar, Loader2,
} from 'lucide-vue-next'
import { llmApi } from '@/api/llm'
import type { LlmConfig, LlmConfigCreate, LlmConfigUpdate } from '@/types'
import BaseModal from '@/components/ui/BaseModal.vue'
import Badge from '@/components/ui/Badge.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import LoadingState from '@/components/shared/LoadingState.vue'
import ErrorState from '@/components/shared/ErrorState.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'

const configs = ref<LlmConfig[]>([])
const loading = ref(false)
const error = ref('')
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const showFormModal = ref(false)
const showModelsModal = ref(false)
const showDeleteModal = ref(false)
const editingConfig = ref<LlmConfig | null>(null)
const deleteTarget = ref<LlmConfig | null>(null)
const modelsLoading = ref(false)
const models = ref<string[]>([])
const modelsError = ref('')
const submitting = ref(false)

const form = reactive({
  name: '',
  api_key: '',
  api_base: '',
  model_name: '',
  max_tokens: 4096,
  temperature: 0.7,
})

function resetForm(): void {
  form.name = ''
  form.api_key = ''
  form.api_base = ''
  form.model_name = ''
  form.max_tokens = 4096
  form.temperature = 0.7
}

function showMessage(type: 'success' | 'error', text: string): void {
  messageType.value = type
  message.value = text
  setTimeout(() => { message.value = '' }, 3000)
}

function maskApiKey(key: string): string {
  if (!key) return '—'
  if (key.length <= 8) return key
  return `${key.slice(0, 4)}****${key.slice(-4)}`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchConfigs(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    configs.value = await llmApi.listConfigs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载配置失败'
  } finally {
    loading.value = false
  }
}

function openCreateModal(): void {
  editingConfig.value = null
  resetForm()
  showFormModal.value = true
}

function openEditModal(config: LlmConfig): void {
  editingConfig.value = config
  form.name = config.name
  form.api_key = config.api_key
  form.api_base = config.api_base
  form.model_name = config.model_name
  form.max_tokens = config.max_tokens
  form.temperature = config.temperature
  showFormModal.value = true
}

async function handleSubmit(): Promise<void> {
  if (!form.name || !form.api_key || !form.api_base || !form.model_name) {
    showMessage('error', '请填写所有必填字段')
    return
  }
  submitting.value = true
  try {
    if (editingConfig.value) {
      const data: LlmConfigUpdate = { ...form }
      await llmApi.updateConfig(editingConfig.value.id, data)
      showMessage('success', '配置已更新')
    } else {
      const data: LlmConfigCreate = { ...form }
      await llmApi.createConfig(data)
      showMessage('success', '配置已创建')
    }
    showFormModal.value = false
    await fetchConfigs()
  } catch (e) {
    showMessage('error', e instanceof Error ? e.message : '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleActivate(config: LlmConfig): Promise<void> {
  try {
    await llmApi.activateConfig(config.id)
    showMessage('success', `已激活配置：${config.name}`)
    await fetchConfigs()
  } catch (e) {
    showMessage('error', e instanceof Error ? e.message : '激活失败')
  }
}

function openDeleteModal(config: LlmConfig): void {
  deleteTarget.value = config
  showDeleteModal.value = true
}

async function handleDelete(): Promise<void> {
  if (!deleteTarget.value) return
  try {
    await llmApi.deleteConfig(deleteTarget.value.id)
    showMessage('success', '配置已删除')
    await fetchConfigs()
  } catch (e) {
    showMessage('error', e instanceof Error ? e.message : '删除失败')
  }
}

async function fetchModels(): Promise<void> {
  showModelsModal.value = true
  modelsLoading.value = true
  modelsError.value = ''
  models.value = []
  try {
    models.value = await llmApi.getModels()
  } catch (e) {
    modelsError.value = e instanceof Error ? e.message : '查询模型失败'
  } finally {
    modelsLoading.value = false
  }
}

onMounted(() => {
  fetchConfigs()
})
</script>

<template>
  <div class="mx-auto max-w-6xl p-6">
    <!-- 头部 -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-zinc-100">LLM 配置</h1>
        <p class="mt-1 font-mono text-xs text-base-500">管理大语言模型接入与调度</p>
      </div>
      <div class="flex gap-3">
        <button class="btn-secondary" @click="fetchModels">
          <Search class="h-4 w-4" />
          查询可用模型
        </button>
        <button class="btn-primary" @click="openCreateModal">
          <Plus class="h-4 w-4" />
          新建配置
        </button>
      </div>
    </div>

    <!-- 内联消息 -->
    <div
      v-if="message"
      :class="[
        'mb-4 rounded-md border px-4 py-2.5 text-sm',
        messageType === 'success'
          ? 'border-status-success/30 bg-status-success/10 text-status-success'
          : 'border-status-error/30 bg-status-error/10 text-status-error',
      ]"
    >
      {{ message }}
    </div>

    <!-- 内容区 -->
    <LoadingState v-if="loading" text="加载配置列表..." />
    <ErrorState v-else-if="error" :text="error" @retry="fetchConfigs" />
    <EmptyState
      v-else-if="configs.length === 0"
      text="暂无 LLM 配置"
      description="点击「新建配置」开始接入第一个模型"
    />
    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div
        v-for="config in configs"
        :key="config.id"
        class="card card-hover flex flex-col p-5"
      >
        <!-- 名称与状态 -->
        <div class="mb-3 flex items-start justify-between gap-2">
          <h3 class="truncate text-base font-semibold text-zinc-100">{{ config.name }}</h3>
          <Badge v-if="config.is_active" variant="amber" dot>活跃</Badge>
          <Badge v-else variant="default">未激活</Badge>
        </div>

        <!-- 详情 -->
        <div class="mb-4 space-y-2">
          <div class="flex items-center gap-2">
            <Cpu class="h-3.5 w-3.5 flex-shrink-0 text-cyan" />
            <span class="font-mono text-sm text-cyan">{{ config.model_name }}</span>
          </div>
          <div class="flex items-center gap-2">
            <Server class="h-3.5 w-3.5 flex-shrink-0 text-base-500" />
            <span class="truncate font-mono text-xs text-base-500">{{ config.api_base }}</span>
          </div>
          <div class="flex items-center gap-2">
            <Key class="h-3.5 w-3.5 flex-shrink-0 text-base-500" />
            <span class="font-mono text-xs text-base-500">{{ maskApiKey(config.api_key) }}</span>
          </div>
          <div class="flex items-center gap-4">
            <span class="flex items-center gap-1.5">
              <Hash class="h-3.5 w-3.5 text-base-500" />
              <span class="text-label">tokens</span>
              <span class="font-mono text-xs text-zinc-300">{{ config.max_tokens }}</span>
            </span>
            <span class="flex items-center gap-1.5">
              <Thermometer class="h-3.5 w-3.5 text-base-500" />
              <span class="text-label">temp</span>
              <span class="font-mono text-xs text-zinc-300">{{ config.temperature }}</span>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <Calendar class="h-3.5 w-3.5 flex-shrink-0 text-base-500" />
            <span class="font-mono text-xs text-base-500">{{ formatDate(config.created_at) }}</span>
          </div>
        </div>

        <!-- 操作 -->
        <div class="mt-auto flex items-center gap-2 border-t border-base-700 pt-3">
          <button
            v-if="!config.is_active"
            class="btn-primary px-3 py-1.5 text-xs"
            @click="handleActivate(config)"
          >
            <Zap class="h-3.5 w-3.5" />
            激活
          </button>
          <button class="btn-ghost text-xs" @click="openEditModal(config)">
            <Pencil class="h-3.5 w-3.5" />
            编辑
          </button>
          <button class="btn-ghost ml-auto text-xs text-status-error hover:bg-status-error/10" @click="openDeleteModal(config)">
            <Trash2 class="h-3.5 w-3.5" />
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <BaseModal
      :model-value="showFormModal"
      :title="editingConfig ? '编辑配置' : '新建配置'"
      width="max-w-xl"
      @update:model-value="showFormModal = $event"
    >
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label class="text-label mb-1.5 block">配置名称</label>
          <input v-model="form.name" type="text" class="input-base" placeholder="例如：默认接入" />
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label class="text-label mb-1.5 block">API Base</label>
            <input v-model="form.api_base" type="text" class="input-base" placeholder="https://api.openai.com/v1" />
          </div>
          <div>
            <label class="text-label mb-1.5 block">模型名称</label>
            <input v-model="form.model_name" type="text" class="input-base" placeholder="gpt-4o" />
          </div>
        </div>
        <div>
          <label class="text-label mb-1.5 block">API Key</label>
          <input v-model="form.api_key" type="password" class="input-base" placeholder="sk-..." autocomplete="off" />
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label class="text-label mb-1.5 block">最大 Tokens</label>
            <input v-model.number="form.max_tokens" type="number" min="1" class="input-base" />
          </div>
          <div>
            <label class="text-label mb-1.5 flex items-center justify-between">
              <span>温度</span>
              <span class="font-mono text-amber">{{ form.temperature.toFixed(1) }}</span>
            </label>
            <input
              v-model.number="form.temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              class="h-2 w-full cursor-pointer appearance-none rounded-full bg-base-700 accent-amber"
            />
          </div>
        </div>
      </form>
      <template #footer>
        <button class="btn-secondary" @click="showFormModal = false">取消</button>
        <button class="btn-primary" :disabled="submitting" @click="handleSubmit">
          <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
          {{ editingConfig ? '保存' : '创建' }}
        </button>
      </template>
    </BaseModal>

    <!-- 模型列表弹窗 -->
    <BaseModal v-model="showModelsModal" title="可用模型列表" width="max-w-lg">
      <LoadingState v-if="modelsLoading" text="查询模型中..." />
      <ErrorState v-else-if="modelsError" :text="modelsError" />
      <EmptyState v-else-if="models.length === 0" text="暂无可用模型" />
      <div v-else class="max-h-80 space-y-1.5 overflow-y-auto">
        <div
          v-for="model in models"
          :key="model"
          class="rounded-md border border-base-700 bg-base-900 px-3 py-2 font-mono text-sm text-cyan"
        >
          {{ model }}
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="showModelsModal = false">关闭</button>
      </template>
    </BaseModal>

    <!-- 删除确认 -->
    <ConfirmDialog
      v-model="showDeleteModal"
      :title="`删除配置：${deleteTarget?.name ?? ''}`"
      text="删除后无法恢复，确定要删除该 LLM 配置吗？"
      @confirm="handleDelete"
    />
  </div>
</template>

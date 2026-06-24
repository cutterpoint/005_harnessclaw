<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Sparkles, Play, Pencil, Trash2, CheckCircle2, XCircle } from 'lucide-vue-next'
import { skillsApi } from '@/api/skills'
import type { Skill, SkillCreate, ExecutionResult } from '@/types'
import BaseModal from '@/components/ui/BaseModal.vue'
import Badge from '@/components/ui/Badge.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import LoadingState from '@/components/shared/LoadingState.vue'
import ErrorState from '@/components/shared/ErrorState.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'

const skills = ref<Skill[]>([])
const loading = ref(false)
const loadError = ref('')
const page = ref(1)
const limit = ref(12)
const total = ref(0)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)

const showFormModal = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', description: '', prompt: '', is_enabled: true })
const submitting = ref(false)

const showExecuteModal = ref(false)
const executingSkill = ref<Skill | null>(null)
const executeInput = ref('')
const executeResult = ref<ExecutionResult | null>(null)
const executing = ref(false)

const showDeleteDialog = ref(false)
const deletingSkill = ref<Skill | null>(null)
const training = ref(false)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function showMessage(type: 'success' | 'error', text: string): void {
  message.value = { type, text }
  setTimeout(() => {
    if (message.value?.text === text) message.value = null
  }, 4000)
}

async function loadSkills(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    const res = await skillsApi.list({ page: page.value, limit: limit.value })
    skills.value = res.items
    total.value = res.total
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : '加载技能列表失败'
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editingId.value = null
  Object.assign(form, { name: '', description: '', prompt: '', is_enabled: true })
  showFormModal.value = true
}

function openEdit(skill: Skill): void {
  editingId.value = skill.id
  Object.assign(form, {
    name: skill.name,
    description: skill.description || '',
    prompt: skill.prompt || '',
    is_enabled: skill.is_enabled,
  })
  showFormModal.value = true
}

async function submitForm(): Promise<void> {
  if (!form.name.trim()) return showMessage('error', '技能名称不能为空')
  submitting.value = true
  try {
    const payload: SkillCreate = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      prompt: form.prompt.trim() || undefined,
      is_enabled: form.is_enabled,
    }
    if (editingId.value !== null) {
      await skillsApi.update(editingId.value, payload)
      showMessage('success', '技能更新成功')
    } else {
      await skillsApi.create(payload)
      showMessage('success', '技能创建成功')
    }
    showFormModal.value = false
    await loadSkills()
  } catch (e) {
    showMessage('error', e instanceof Error ? e.message : '保存技能失败')
  } finally {
    submitting.value = false
  }
}

function openExecute(skill: Skill): void {
  executingSkill.value = skill
  executeInput.value = ''
  executeResult.value = null
  showExecuteModal.value = true
}

async function runExecute(): Promise<void> {
  if (!executingSkill.value || !executeInput.value.trim()) return
  executing.value = true
  executeResult.value = null
  try {
    executeResult.value = await skillsApi.execute(executingSkill.value.id, { input: executeInput.value })
  } catch (e) {
    executeResult.value = { success: false, result: '', error: e instanceof Error ? e.message : '执行失败' }
  } finally {
    executing.value = false
  }
}

function openDelete(skill: Skill): void {
  deletingSkill.value = skill
  showDeleteDialog.value = true
}

async function confirmDelete(): Promise<void> {
  if (!deletingSkill.value) return
  try {
    await skillsApi.delete(deletingSkill.value.id)
    showMessage('success', '技能已删除')
    if (skills.value.length === 1 && page.value > 1) page.value -= 1
    await loadSkills()
  } catch (e) {
    showMessage('error', e instanceof Error ? e.message : '删除技能失败')
  } finally {
    deletingSkill.value = null
  }
}

async function handleTrain(): Promise<void> {
  training.value = true
  try {
    const res = await skillsApi.train()
    showMessage('success', res.message || '训练完成')
    await loadSkills()
  } catch (e) {
    showMessage('error', e instanceof Error ? e.message : '训练失败')
  } finally {
    training.value = false
  }
}

function handlePageChange(p: number): void {
  page.value = p
  loadSkills()
}

onMounted(loadSkills)
</script>

<template>
  <div class="mx-auto max-w-7xl p-6">
    <!-- 标题区 -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-zinc-100">技能管理</h1>
        <p class="mt-1 font-mono text-xs text-base-500">管理 Agent 技能、提示词与执行</p>
      </div>
      <div class="flex items-center gap-3">
        <button class="btn-secondary" :disabled="training" @click="handleTrain">
          <Sparkles class="h-4 w-4" />
          {{ training ? '训练中...' : '训练技能' }}
        </button>
        <button class="btn-primary" @click="openCreate">
          <Plus class="h-4 w-4" />
          新建技能
        </button>
      </div>
    </div>

    <!-- 消息提示 -->
    <div
      v-if="message"
      class="mb-4 flex items-center gap-2 rounded-md border px-4 py-3 text-sm"
      :class="message.type === 'success'
        ? 'border-status-success/30 bg-status-success/10 text-status-success'
        : 'border-status-error/30 bg-status-error/10 text-status-error'"
    >
      <CheckCircle2 v-if="message.type === 'success'" class="h-4 w-4 flex-shrink-0" />
      <XCircle v-else class="h-4 w-4 flex-shrink-0" />
      {{ message.text }}
    </div>

    <!-- 列表区 -->
    <div class="card overflow-hidden">
      <LoadingState v-if="loading" text="加载技能..." />
      <ErrorState v-else-if="loadError" :text="loadError" @retry="loadSkills" />
      <EmptyState v-else-if="skills.length === 0" text="暂无技能" description="点击「新建技能」创建第一个技能" />
      <template v-else>
        <div class="grid grid-cols-1 gap-4 p-4 md:grid-cols-2 lg:grid-cols-3">
          <div v-for="skill in skills" :key="skill.id" class="card card-hover flex flex-col p-4">
            <div class="mb-2 flex items-start justify-between gap-2">
              <h3 class="truncate font-semibold text-zinc-100">{{ skill.name }}</h3>
              <Badge :variant="skill.is_enabled ? 'success' : 'default'" dot>
                {{ skill.is_enabled ? '启用' : '禁用' }}
              </Badge>
            </div>
            <p class="mb-2 line-clamp-2 text-sm text-zinc-400">{{ skill.description || '无描述' }}</p>
            <p class="mb-3 line-clamp-2 font-mono text-xs text-base-500">{{ skill.prompt || '无提示词' }}</p>
            <p class="mb-3 font-mono text-xs text-base-600">{{ formatDate(skill.created_at) }}</p>
            <div class="mt-auto flex items-center gap-1 border-t border-base-700 pt-3">
              <button class="btn-ghost" @click="openExecute(skill)"><Play class="h-3.5 w-3.5" />执行</button>
              <button class="btn-ghost" @click="openEdit(skill)"><Pencil class="h-3.5 w-3.5" />编辑</button>
              <button class="btn-ghost ml-auto text-status-error hover:bg-status-error/10" @click="openDelete(skill)">
                <Trash2 class="h-3.5 w-3.5" />删除
              </button>
            </div>
          </div>
        </div>
        <div class="border-t border-base-700 px-4">
          <Pagination :page="page" :limit="limit" :total="total" @change="handlePageChange" />
        </div>
      </template>
    </div>

    <!-- 创建/编辑弹窗 -->
    <BaseModal :model-value="showFormModal" :title="editingId !== null ? '编辑技能' : '新建技能'" width="max-w-xl" @update:model-value="showFormModal = $event">
      <div class="space-y-4">
        <div>
          <label class="text-label mb-1.5 block">名称</label>
          <input v-model="form.name" class="input-base" placeholder="输入技能名称" />
        </div>
        <div>
          <label class="text-label mb-1.5 block">描述</label>
          <textarea v-model="form.description" rows="2" class="input-base resize-none" placeholder="技能描述" />
        </div>
        <div>
          <label class="text-label mb-1.5 block">提示词</label>
          <textarea v-model="form.prompt" rows="5" class="input-base resize-none font-mono text-xs" placeholder="技能提示词模板" />
        </div>
        <label class="flex items-center gap-2 text-sm text-zinc-300">
          <input v-model="form.is_enabled" type="checkbox" class="h-4 w-4 rounded border-base-600 bg-base-900 accent-amber" />
          启用此技能
        </label>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="showFormModal = false">取消</button>
        <button class="btn-primary" :disabled="submitting" @click="submitForm">
          {{ submitting ? '保存中...' : '保存' }}
        </button>
      </template>
    </BaseModal>

    <!-- 执行弹窗 -->
    <BaseModal :model-value="showExecuteModal" :title="`执行技能: ${executingSkill?.name ?? ''}`" width="max-w-xl" @update:model-value="showExecuteModal = $event">
      <div class="space-y-4">
        <div>
          <label class="text-label mb-1.5 block">输入</label>
          <textarea v-model="executeInput" rows="4" class="input-base resize-none" placeholder="输入要处理的内容" />
        </div>
        <div v-if="executeResult">
          <label class="text-label mb-1.5 block">结果</label>
          <div class="rounded-md border p-3 font-mono text-xs" :class="executeResult.success ? 'border-status-success/30 bg-status-success/5 text-zinc-200' : 'border-status-error/30 bg-status-error/5 text-status-error'">
            <pre class="whitespace-pre-wrap break-words">{{ executeResult.success ? executeResult.result : executeResult.error }}</pre>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="showExecuteModal = false">关闭</button>
        <button class="btn-primary" :disabled="executing || !executeInput.trim()" @click="runExecute">
          {{ executing ? '执行中...' : '执行' }}
        </button>
      </template>
    </BaseModal>

    <!-- 删除确认 -->
    <ConfirmDialog
      :model-value="showDeleteDialog"
      :text="`确定要删除技能「${deletingSkill?.name ?? ''}」吗？此操作不可撤销。`"
      @update:model-value="showDeleteDialog = $event"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { Plus, MessageSquare, Trash2, Loader2, Activity } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { sessionsApi } from '@/api/sessions'
import { agentApi } from '@/api/agent'
import type { Session } from '@/types'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import EmptyState from '@/components/shared/EmptyState.vue'
import LoadingState from '@/components/shared/LoadingState.vue'

const auth = useAuthStore()
const chat = useChatStore()

const messagesContainer = ref<HTMLElement | null>(null)
const agentStatus = ref<string>('idle')
const error = ref('')

async function loadSessions(): Promise<void> {
  chat.loadingSessions = true
  try {
    const res = await sessionsApi.list({ page: 1, limit: 50 })
    chat.setSessions(res.items)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载会话失败'
  } finally {
    chat.loadingSessions = false
  }
}

async function selectSession(session: Session): Promise<void> {
  chat.setCurrentSession(session.id)
  chat.loadingMessages = true
  try {
    const res = await sessionsApi.getMessages(session.id, { page: 1, limit: 100 })
    chat.setMessages(res.items)
    await scrollToBottom()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载消息失败'
  } finally {
    chat.loadingMessages = false
  }
}

async function createSession(): Promise<void> {
  try {
    const session = await sessionsApi.create({ title: `会话 ${new Date().toLocaleString('zh-CN')}` })
    chat.setSessions([session, ...chat.sessions])
    await selectSession(session)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建会话失败'
  }
}

async function deleteSession(id: number): Promise<void> {
  try {
    await sessionsApi.delete(id)
    chat.setSessions(chat.sessions.filter((s) => s.id !== id))
    if (chat.currentSessionId === id) {
      chat.setCurrentSession(null)
      chat.clearMessages()
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除会话失败'
  }
}

async function sendMessage(content: string): Promise<void> {
  if (!chat.currentSessionId) {
    error.value = '请先选择或创建会话'
    return
  }
  chat.sending = true
  error.value = ''
  chat.addUserMessage(content)
  await scrollToBottom()

  const pendingId = chat.addPendingAssistant()
  await scrollToBottom()

  try {
    const res = await agentApi.chat({
      message: content,
      session_id: chat.currentSessionId,
    })
    chat.resolveAssistant(pendingId, res)
    await scrollToBottom()
  } catch (e) {
    chat.resolveAssistant(pendingId, {
      response: '',
      session_id: chat.currentSessionId!,
      iterations: 0,
      tool_calls: [],
      error: e instanceof Error ? e.message : 'Agent 处理失败',
    })
    error.value = e instanceof Error ? e.message : '发送失败'
  } finally {
    chat.sending = false
  }
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function fetchAgentStatus(): Promise<void> {
  try {
    const res = await agentApi.status()
    agentStatus.value = res.status
  } catch {
    agentStatus.value = 'unknown'
  }
}

onMounted(async () => {
  await auth.fetchUser()
  await loadSessions()
  fetchAgentStatus()
})

watch(() => chat.messages.length, () => scrollToBottom())
</script>

<template>
  <div class="flex h-[calc(100vh-4rem)] overflow-hidden">
    <!-- 会话列表 -->
    <div class="flex w-64 flex-shrink-0 flex-col border-r border-base-700 bg-base-900">
      <div class="flex items-center justify-between border-b border-base-700 px-4 py-3">
        <span class="text-label">会话</span>
        <button class="btn-ghost p-1" title="新建会话" @click="createSession">
          <Plus class="h-4 w-4" />
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-2">
        <LoadingState v-if="chat.loadingSessions" text="加载会话..." />
        <EmptyState v-else-if="chat.sessions.length === 0" text="暂无会话" description="点击 + 创建新会话" />
        <div v-else class="space-y-1">
          <button
            v-for="session in chat.sessions"
            :key="session.id"
            class="group flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-all"
            :class="
              chat.currentSessionId === session.id
                ? 'bg-amber/10 text-amber'
                : 'text-zinc-400 hover:bg-base-800'
            "
            @click="selectSession(session)"
          >
            <MessageSquare class="h-3.5 w-3.5 flex-shrink-0" />
            <span class="flex-1 truncate">{{ session.title || `会话 #${session.id}` }}</span>
            <span
              class="hidden opacity-0 transition-opacity group-hover:opacity-100"
              @click.stop="deleteSession(session.id)"
            >
              <Trash2 class="h-3.5 w-3.5 text-status-error" />
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 消息区 -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- 状态条 -->
      <div class="flex items-center justify-between border-b border-base-700 px-4 py-2">
        <div class="flex items-center gap-2">
          <div
            class="h-2 w-2 rounded-full"
            :class="{
              'bg-status-success': agentStatus === 'idle',
              'bg-amber animate-pulse': agentStatus === 'running',
              'bg-status-error': agentStatus === 'error',
              'bg-base-500': agentStatus === 'unknown',
            }"
          />
          <span class="font-mono text-xs text-base-500">Agent: {{ agentStatus }}</span>
        </div>
        <div class="flex items-center gap-2 text-base-500">
          <Activity class="h-3.5 w-3.5" />
          <span class="font-mono text-xs">{{ chat.messages.length }} 条消息</span>
        </div>
      </div>

      <!-- 消息流 -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6">
        <div v-if="!chat.currentSessionId" class="flex h-full items-center justify-center">
          <div class="text-center">
            <div class="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full border border-base-700 bg-base-850">
              <MessageSquare class="h-7 w-7 text-base-500" />
            </div>
            <p class="text-sm text-zinc-400">选择一个会话或创建新会话开始对话</p>
          </div>
        </div>
        <LoadingState v-else-if="chat.loadingMessages" text="加载消息..." />
        <div v-else class="space-y-6">
          <MessageBubble v-for="msg in chat.messages" :key="msg.id" :message="msg" />
        </div>
      </div>

      <!-- 错误提示 -->
      <div
        v-if="error"
        class="border-t border-status-error/30 bg-status-error/10 px-4 py-2 text-xs text-status-error"
      >
        {{ error }}
      </div>

      <!-- 输入区 -->
      <ChatInput :disabled="!chat.currentSessionId || chat.sending" @send="sendMessage" />
    </div>
  </div>
</template>

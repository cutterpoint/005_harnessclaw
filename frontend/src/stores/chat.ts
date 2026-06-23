import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Session, Message, ChatResponse } from '@/types'

export interface ChatMessage {
  id: number | string
  role: string
  content: string
  tool_calls?: Array<{ tool_name: string; result: string }>
  created_at: string
  pending?: boolean
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<number | null>(null)
  const messages = ref<ChatMessage[]>([])
  const sending = ref(false)
  const loadingSessions = ref(false)
  const loadingMessages = ref(false)

  function setSessions(list: Session[]): void {
    sessions.value = list
  }

  function setCurrentSession(id: number | null): void {
    currentSessionId.value = id
  }

  function setMessages(list: Message[]): void {
    messages.value = list.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      created_at: m.created_at,
    }))
  }

  function addUserMessage(content: string): void {
    messages.value.push({
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    })
  }

  function addPendingAssistant(): string {
    const id = `pending-${Date.now()}`
    messages.value.push({
      id,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      pending: true,
    })
    return id
  }

  function resolveAssistant(id: string, res: ChatResponse): void {
    const msg = messages.value.find((m) => m.id === id)
    if (msg) {
      msg.content = res.response
      msg.tool_calls = res.tool_calls
      msg.pending = false
      msg.created_at = new Date().toISOString()
    }
  }

  function clearMessages(): void {
    messages.value = []
  }

  return {
    sessions,
    currentSessionId,
    messages,
    sending,
    loadingSessions,
    loadingMessages,
    setSessions,
    setCurrentSession,
    setMessages,
    addUserMessage,
    addPendingAssistant,
    resolveAssistant,
    clearMessages,
  }
})

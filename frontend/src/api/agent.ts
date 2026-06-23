import client from './client'
import type { ChatRequest, ChatResponse, AgentStatus } from '@/types'

export const agentApi = {
  chat(data: ChatRequest): Promise<ChatResponse> {
    return client.post('/agent/chat', data)
  },
  status(): Promise<AgentStatus> {
    return client.get('/agent/status')
  },
}

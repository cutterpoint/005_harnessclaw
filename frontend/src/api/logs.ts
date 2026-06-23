import client from './client'
import type {
  SystemLog,
  LlmLog,
  LlmStatistics,
  SystemLogParams,
  LlmLogParams,
  PaginatedData,
} from '@/types'

export const logsApi = {
  system(params?: SystemLogParams): Promise<PaginatedData<SystemLog>> {
    return client.get('/logs/system', { params })
  },
  llm(params?: LlmLogParams): Promise<PaginatedData<LlmLog>> {
    return client.get('/logs/llm', { params })
  },
  llmStatistics(): Promise<LlmStatistics> {
    return client.get('/logs/llm/statistics')
  },
}

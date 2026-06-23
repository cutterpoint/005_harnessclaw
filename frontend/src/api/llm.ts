import client from './client'
import type { LlmConfig, LlmConfigCreate, LlmConfigUpdate } from '@/types'

export const llmApi = {
  listConfigs(): Promise<LlmConfig[]> {
    return client.get('/llm/configs')
  },
  createConfig(data: LlmConfigCreate): Promise<LlmConfig> {
    return client.post('/llm/configs', data)
  },
  getConfig(id: number): Promise<LlmConfig> {
    return client.get(`/llm/configs/${id}`)
  },
  updateConfig(id: number, data: LlmConfigUpdate): Promise<LlmConfig> {
    return client.put(`/llm/configs/${id}`, data)
  },
  deleteConfig(id: number): Promise<void> {
    return client.delete(`/llm/configs/${id}`)
  },
  activateConfig(id: number): Promise<LlmConfig> {
    return client.post(`/llm/configs/${id}/activate`)
  },
  getModels(configId?: number): Promise<string[]> {
    return client.get('/llm/models', { params: { config_id: configId } })
  },
}

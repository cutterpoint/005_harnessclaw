import client from './client'
import type {
  Tool,
  ToolCreate,
  ToolUpdate,
  ToolExecuteRequest,
  ExecutionResult,
} from '@/types'

export const toolsApi = {
  list(params?: { enabled_only?: boolean }): Promise<Tool[]> {
    return client.get('/tools', { params })
  },
  create(data: ToolCreate): Promise<Tool> {
    return client.post('/tools', data)
  },
  get(id: number): Promise<Tool> {
    return client.get(`/tools/${id}`)
  },
  update(id: number, data: ToolUpdate): Promise<Tool> {
    return client.put(`/tools/${id}`, data)
  },
  delete(id: number): Promise<void> {
    return client.delete(`/tools/${id}`)
  },
  execute(id: number, data: ToolExecuteRequest): Promise<ExecutionResult> {
    return client.post(`/tools/${id}/execute`, data)
  },
}

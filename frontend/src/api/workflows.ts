import client from './client'
import type {
  Workflow,
  WorkflowCreate,
  WorkflowUpdate,
  WorkflowExecution,
  ExecutionResult,
  PaginationParams,
  PaginatedData,
} from '@/types'

export const workflowsApi = {
  list(params?: PaginationParams): Promise<PaginatedData<Workflow>> {
    return client.get('/workflows', { params })
  },
  create(data: WorkflowCreate): Promise<Workflow> {
    return client.post('/workflows', data)
  },
  get(id: number): Promise<Workflow> {
    return client.get(`/workflows/${id}`)
  },
  update(id: number, data: WorkflowUpdate): Promise<Workflow> {
    return client.put(`/workflows/${id}`, data)
  },
  delete(id: number): Promise<void> {
    return client.delete(`/workflows/${id}`)
  },
  execute(id: number): Promise<ExecutionResult> {
    return client.post(`/workflows/${id}/execute`)
  },
  executions(id: number): Promise<WorkflowExecution[]> {
    return client.get(`/workflows/${id}/executions`)
  },
}

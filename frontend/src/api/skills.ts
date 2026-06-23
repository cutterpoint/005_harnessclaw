import client from './client'
import type {
  Skill,
  SkillCreate,
  SkillUpdate,
  SkillExecuteRequest,
  ExecutionResult,
  TrainResult,
  PaginationParams,
  PaginatedData,
} from '@/types'

export const skillsApi = {
  list(params?: PaginationParams): Promise<PaginatedData<Skill>> {
    return client.get('/skills', { params })
  },
  create(data: SkillCreate): Promise<Skill> {
    return client.post('/skills', data)
  },
  get(id: number): Promise<Skill> {
    return client.get(`/skills/${id}`)
  },
  update(id: number, data: SkillUpdate): Promise<Skill> {
    return client.put(`/skills/${id}`, data)
  },
  delete(id: number): Promise<void> {
    return client.delete(`/skills/${id}`)
  },
  execute(id: number, data: SkillExecuteRequest): Promise<ExecutionResult> {
    return client.post(`/skills/${id}/execute`, data)
  },
  train(): Promise<TrainResult> {
    return client.post('/skills/train')
  },
}

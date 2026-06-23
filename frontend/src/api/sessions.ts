import client from './client'
import type {
  Session,
  SessionCreate,
  SessionUpdate,
  Message,
  MessageCreate,
  PaginationParams,
  PaginatedData,
} from '@/types'

export const sessionsApi = {
  list(params?: PaginationParams): Promise<PaginatedData<Session>> {
    return client.get('/sessions', { params })
  },
  create(data: SessionCreate): Promise<Session> {
    return client.post('/sessions', data)
  },
  get(id: number): Promise<Session> {
    return client.get(`/sessions/${id}`)
  },
  update(id: number, data: SessionUpdate): Promise<Session> {
    return client.put(`/sessions/${id}`, data)
  },
  delete(id: number): Promise<void> {
    return client.delete(`/sessions/${id}`)
  },
  getMessages(id: number, params?: PaginationParams): Promise<PaginatedData<Message>> {
    return client.get(`/sessions/${id}/messages`, { params })
  },
  addMessage(id: number, data: MessageCreate): Promise<Message> {
    return client.post(`/sessions/${id}/messages`, data)
  },
}

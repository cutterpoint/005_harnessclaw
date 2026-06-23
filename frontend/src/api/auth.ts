import client from './client'
import type {
  LoginRequest,
  RegisterRequest,
  AuthTokens,
  UserInfo,
} from '@/types'

export const authApi = {
  login(data: LoginRequest): Promise<AuthTokens> {
    return client.post('/auth/login', data)
  },
  register(data: RegisterRequest): Promise<UserInfo> {
    return client.post('/auth/register', data)
  },
  refresh(refreshToken: string): Promise<AuthTokens> {
    return client.post('/auth/refresh', { refresh_token: refreshToken })
  },
  me(): Promise<UserInfo> {
    return client.get('/auth/me')
  },
}

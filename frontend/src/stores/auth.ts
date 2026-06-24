import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { getToken, getRefreshToken, setTokens, clearTokens } from '@/api/client'
import type { LoginRequest, RegisterRequest, UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const refreshToken = ref<string | null>(getRefreshToken())
  const user = ref<UserInfo | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  async function login(data: LoginRequest): Promise<void> {
    loading.value = true
    try {
      const tokens = await authApi.login(data)
      token.value = tokens.access_token
      refreshToken.value = tokens.refresh_token
      setTokens(tokens.access_token, tokens.refresh_token)
      try {
        await fetchUser()
      } catch {
      }
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest): Promise<void> {
    loading.value = true
    try {
      await authApi.register(data)
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return
    try {
      user.value = await authApi.me()
    } catch {
      logout()
    }
  }

  function logout(): void {
    token.value = null
    refreshToken.value = null
    user.value = null
    clearTokens()
  }

  return {
    token,
    refreshToken,
    user,
    loading,
    isLoggedIn,
    login,
    register,
    fetchUser,
    logout,
  }
})

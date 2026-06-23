<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Terminal, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})
const error = ref('')

async function handleSubmit(): Promise<void> {
  error.value = ''
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }
  try {
    await auth.login(form)
    const redirect = (route.query.redirect as string) || '/chat'
    router.push(redirect)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-4">
    <!-- 背景装饰 -->
    <div class="pointer-events-none fixed inset-0 overflow-hidden">
      <div class="absolute -left-40 top-1/4 h-96 w-96 rounded-full bg-amber/5 blur-3xl" />
      <div class="absolute -right-40 bottom-1/4 h-96 w-96 rounded-full bg-cyan/5 blur-3xl" />
    </div>

    <div class="relative w-full max-w-sm animate-slide-up">
      <!-- Logo -->
      <div class="mb-8 text-center">
        <div class="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-xl border border-amber/20 bg-amber/10 shadow-glow">
          <Terminal class="h-7 w-7 text-amber" />
        </div>
        <h1 class="text-2xl font-bold text-zinc-100">HarnessClaw</h1>
        <p class="mt-1 font-mono text-xs uppercase tracking-widest text-base-500">Agent Console</p>
      </div>

      <!-- 登录卡片 -->
      <div class="card p-6 shadow-card">
        <div class="mb-5">
          <h2 class="text-lg font-semibold text-zinc-100">登录</h2>
          <p class="mt-0.5 text-xs text-base-500">输入凭证以访问控制台</p>
        </div>

        <form class="space-y-4" @submit.prevent="handleSubmit">
          <div>
            <label class="text-label mb-1.5 block">用户名</label>
            <input
              v-model="form.username"
              type="text"
              class="input-base"
              placeholder="输入用户名"
              autocomplete="username"
            />
          </div>
          <div>
            <label class="text-label mb-1.5 block">密码</label>
            <input
              v-model="form.password"
              type="password"
              class="input-base"
              placeholder="输入密码"
              autocomplete="current-password"
            />
          </div>

          <div
            v-if="error"
            class="rounded-md border border-status-error/30 bg-status-error/10 px-3 py-2 text-xs text-status-error"
          >
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="auth.loading">
            <Loader2 v-if="auth.loading" class="h-4 w-4 animate-spin" />
            <span v-else>登录</span>
          </button>
        </form>

        <div class="mt-5 border-t border-base-700 pt-4 text-center">
          <p class="text-xs text-base-500">
            还没有账号？
            <router-link to="/register" class="text-cyan hover:text-cyan/80">立即注册</router-link>
          </p>
        </div>
      </div>

      <p class="mt-6 text-center font-mono text-[10px] text-base-600">
        v1.0.0 · Powered by FastAPI + Vue 3
      </p>
    </div>
  </div>
</template>

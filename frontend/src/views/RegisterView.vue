<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Terminal, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
})
const error = ref('')

async function handleSubmit(): Promise<void> {
  error.value = ''
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (form.password.length < 6) {
    error.value = '密码长度至少 6 位'
    return
  }
  try {
    await auth.register({
      username: form.username,
      password: form.password,
      email: form.email || undefined,
    })
    router.push('/login')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '注册失败'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-4">
    <div class="pointer-events-none fixed inset-0 overflow-hidden">
      <div class="absolute -left-40 top-1/4 h-96 w-96 rounded-full bg-amber/5 blur-3xl" />
      <div class="absolute -right-40 bottom-1/4 h-96 w-96 rounded-full bg-cyan/5 blur-3xl" />
    </div>

    <div class="relative w-full max-w-sm animate-slide-up">
      <div class="mb-8 text-center">
        <div class="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-xl border border-amber/20 bg-amber/10 shadow-glow">
          <Terminal class="h-7 w-7 text-amber" />
        </div>
        <h1 class="text-2xl font-bold text-zinc-100">创建账号</h1>
        <p class="mt-1 font-mono text-xs uppercase tracking-widest text-base-500">Agent Console</p>
      </div>

      <div class="card p-6 shadow-card">
        <form class="space-y-4" @submit.prevent="handleSubmit">
          <div>
            <label class="text-label mb-1.5 block">用户名</label>
            <input v-model="form.username" type="text" class="input-base" placeholder="输入用户名" />
          </div>
          <div>
            <label class="text-label mb-1.5 block">邮箱（可选）</label>
            <input v-model="form.email" type="email" class="input-base" placeholder="your@email.com" />
          </div>
          <div>
            <label class="text-label mb-1.5 block">密码</label>
            <input v-model="form.password" type="password" class="input-base" placeholder="至少 6 位" />
          </div>
          <div>
            <label class="text-label mb-1.5 block">确认密码</label>
            <input v-model="form.confirmPassword" type="password" class="input-base" placeholder="再次输入密码" />
          </div>

          <div
            v-if="error"
            class="rounded-md border border-status-error/30 bg-status-error/10 px-3 py-2 text-xs text-status-error"
          >
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="auth.loading">
            <Loader2 v-if="auth.loading" class="h-4 w-4 animate-spin" />
            <span v-else>注册</span>
          </button>
        </form>

        <div class="mt-5 border-t border-base-700 pt-4 text-center">
          <p class="text-xs text-base-500">
            已有账号？
            <router-link to="/login" class="text-cyan hover:text-cyan/80">返回登录</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

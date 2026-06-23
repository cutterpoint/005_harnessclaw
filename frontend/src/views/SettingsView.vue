<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Mail, Calendar, LogOut, Shield } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(async () => {
  if (!auth.user) {
    await auth.fetchUser()
  }
})

function handleLogout(): void {
  auth.logout()
  router.push('/login')
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="mx-auto max-w-2xl p-6">
    <div class="card overflow-hidden">
      <!-- 头部 -->
      <div class="flex items-center gap-4 border-b border-base-700 bg-base-850 px-6 py-5">
        <div class="flex h-14 w-14 items-center justify-center rounded-full border border-amber/30 bg-amber/10">
          <User class="h-7 w-7 text-amber" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-zinc-100">{{ auth.user?.username || '用户' }}</h2>
          <p class="font-mono text-xs text-base-500">ID: {{ auth.user?.id ?? '—' }}</p>
        </div>
      </div>

      <!-- 信息列表 -->
      <div class="divide-y divide-base-700">
        <div class="flex items-center gap-3 px-6 py-4">
          <User class="h-4 w-4 text-base-500" />
          <span class="text-label w-24">用户名</span>
          <span class="text-data text-zinc-200">{{ auth.user?.username || '—' }}</span>
        </div>
        <div class="flex items-center gap-3 px-6 py-4">
          <Mail class="h-4 w-4 text-base-500" />
          <span class="text-label w-24">邮箱</span>
          <span class="text-data text-zinc-200">{{ auth.user?.email || '未设置' }}</span>
        </div>
        <div class="flex items-center gap-3 px-6 py-4">
          <Calendar class="h-4 w-4 text-base-500" />
          <span class="text-label w-24">注册时间</span>
          <span class="text-data text-zinc-200">
            {{ auth.user?.created_at ? formatDate(auth.user.created_at) : '—' }}
          </span>
        </div>
        <div class="flex items-center gap-3 px-6 py-4">
          <Shield class="h-4 w-4 text-base-500" />
          <span class="text-label w-24">角色</span>
          <span class="text-data text-zinc-200">普通用户</span>
        </div>
      </div>

      <!-- 操作 -->
      <div class="border-t border-base-700 px-6 py-4">
        <button class="btn-danger" @click="handleLogout">
          <LogOut class="h-4 w-4" />
          退出登录
        </button>
      </div>
    </div>
  </div>
</template>

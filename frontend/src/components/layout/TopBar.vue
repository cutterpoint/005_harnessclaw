<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LogOut, User } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const pageTitle = computed(() => (route.meta.title as string) || '控制台')

function handleLogout(): void {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="flex h-16 flex-shrink-0 items-center justify-between border-b border-base-700 bg-base-900/80 px-6 backdrop-blur">
    <div class="flex items-center gap-3">
      <h1 class="text-lg font-semibold text-zinc-100">{{ pageTitle }}</h1>
      <span class="font-mono text-xs text-base-500">/</span>
      <span class="font-mono text-xs text-base-500">{{ route.path }}</span>
    </div>

    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2 rounded-md border border-base-700 bg-base-850 px-3 py-1.5">
        <User class="h-4 w-4 text-base-500" />
        <span class="font-mono text-sm text-zinc-300">{{ auth.user?.username || '未登录' }}</span>
      </div>
      <button class="btn-ghost" title="登出" @click="handleLogout">
        <LogOut class="h-4 w-4" />
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  MessageSquare,
  Sparkles,
  Wrench,
  Workflow,
  Cpu,
  Activity,
  Settings,
  Terminal,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

interface NavItem {
  name: string
  label: string
  icon: typeof MessageSquare
  path: string
}

const navItems: NavItem[] = [
  { name: 'chat', label: '对话控制台', icon: MessageSquare, path: '/chat' },
  { name: 'skills', label: '技能管理', icon: Sparkles, path: '/skills' },
  { name: 'tools', label: '工具管理', icon: Wrench, path: '/tools' },
  { name: 'workflows', label: '工作流', icon: Workflow, path: '/workflows' },
  { name: 'llm', label: 'LLM 配置', icon: Cpu, path: '/llm' },
  { name: 'monitor', label: '监控仪表盘', icon: Activity, path: '/monitor' },
  { name: 'settings', label: '设置', icon: Settings, path: '/settings' },
]

const activeName = computed(() => route.name as string)

function navigate(path: string): void {
  router.push(path)
}
</script>

<template>
  <aside class="flex w-60 flex-shrink-0 flex-col border-r border-base-700 bg-base-900">
    <!-- Logo -->
    <div class="flex h-16 items-center gap-3 border-b border-base-700 px-5">
      <div class="flex h-8 w-8 items-center justify-center rounded-md bg-amber/10">
        <Terminal class="h-5 w-5 text-amber" />
      </div>
      <div>
        <div class="font-mono text-sm font-bold tracking-tight text-zinc-100">HarnessClaw</div>
        <div class="font-mono text-[10px] uppercase tracking-widest text-base-500">Agent Console</div>
      </div>
    </div>

    <!-- 导航 -->
    <nav class="flex-1 space-y-1 overflow-y-auto p-3">
      <div class="mb-2 px-3 text-label">导航</div>
      <button
        v-for="item in navItems"
        :key="item.name"
        class="group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all"
        :class="
          activeName === item.name
            ? 'bg-amber/10 text-amber'
            : 'text-zinc-400 hover:bg-base-800 hover:text-zinc-200'
        "
        @click="navigate(item.path)"
      >
        <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
        <span>{{ item.label }}</span>
        <div
          v-if="activeName === item.name"
          class="ml-auto h-1.5 w-1.5 rounded-full bg-amber shadow-glow-sm"
        />
      </button>
    </nav>

    <!-- 底部状态 -->
    <div class="border-t border-base-700 p-4">
      <div class="flex items-center gap-2 text-xs text-base-500">
        <div class="h-2 w-2 rounded-full bg-status-success animate-pulse-slow" />
        <span class="font-mono">系统在线</span>
      </div>
    </div>
  </aside>
</template>

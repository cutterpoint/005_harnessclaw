import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ChatView from '@/views/ChatView.vue'
import SkillsView from '@/views/SkillsView.vue'
import ToolsView from '@/views/ToolsView.vue'
import WorkflowsView from '@/views/WorkflowsView.vue'
import LlmView from '@/views/LlmView.vue'
import MonitorView from '@/views/MonitorView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true, title: '登录' },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { public: true, title: '注册' },
  },
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: { title: '对话控制台' },
  },
  {
    path: '/skills',
    name: 'skills',
    component: SkillsView,
    meta: { title: '技能管理' },
  },
  {
    path: '/tools',
    name: 'tools',
    component: ToolsView,
    meta: { title: '工具管理' },
  },
  {
    path: '/workflows',
    name: 'workflows',
    component: WorkflowsView,
    meta: { title: '工作流管理' },
  },
  {
    path: '/llm',
    name: 'llm',
    component: LlmView,
    meta: { title: 'LLM 配置' },
  },
  {
    path: '/monitor',
    name: 'monitor',
    component: MonitorView,
    meta: { title: '监控仪表盘' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { title: '设置' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.public && auth.isLoggedIn) {
    return { name: 'chat' }
  }
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || 'Agent 控制台'
  document.title = `${title} · HarnessClaw`
})

export default router

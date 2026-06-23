<script setup lang="ts">
import { ref } from 'vue'
import { User, Bot, Wrench, ChevronDown, Loader2 } from 'lucide-vue-next'
import type { ChatMessage } from '@/stores/chat'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const showTools = ref(false)

function isUser(): boolean {
  return props.message.role === 'user'
}
</script>

<template>
  <div class="flex gap-3 animate-fade-in" :class="isUser() ? 'flex-row-reverse' : 'flex-row'">
    <!-- 头像 -->
    <div
      class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md"
      :class="isUser() ? 'bg-cyan/10' : 'bg-amber/10'"
    >
      <User v-if="isUser()" class="h-4 w-4 text-cyan" />
      <Bot v-else class="h-4 w-4 text-amber" />
    </div>

    <!-- 消息内容 -->
    <div class="flex max-w-[75%] flex-col gap-2" :class="isUser() ? 'items-end' : 'items-start'">
      <div
        class="rounded-lg px-4 py-2.5 text-sm leading-relaxed"
        :class="
          isUser()
            ? 'bg-cyan/10 text-zinc-100'
            : 'bg-base-800 text-zinc-200 border border-base-700'
        "
      >
        <template v-if="message.pending">
          <div class="flex items-center gap-2 text-base-500">
            <Loader2 class="h-3.5 w-3.5 animate-spin" />
            <span class="font-mono text-xs">Agent 思考中...</span>
          </div>
        </template>
        <template v-else>
          <p class="whitespace-pre-wrap break-words">{{ message.content }}</p>
        </template>
      </div>

      <!-- 工具调用 -->
      <div
        v-if="message.tool_calls && message.tool_calls.length > 0"
        class="w-full overflow-hidden rounded-lg border border-base-700 bg-base-900"
      >
        <button
          class="flex w-full items-center gap-2 px-3 py-2 text-xs text-base-500 hover:bg-base-850"
          @click="showTools = !showTools"
        >
          <Wrench class="h-3.5 w-3.5 text-amber" />
          <span class="font-mono">{{ message.tool_calls.length }} 个工具调用</span>
          <ChevronDown class="ml-auto h-3.5 w-3.5 transition-transform" :class="{ 'rotate-180': showTools }" />
        </button>
        <div v-if="showTools" class="space-y-2 border-t border-base-700 p-3">
          <div
            v-for="(tc, i) in message.tool_calls"
            :key="i"
            class="rounded border border-base-700 bg-base-850 p-2"
          >
            <div class="mb-1 flex items-center gap-2">
              <span class="font-mono text-xs text-amber">{{ tc.tool_name }}</span>
            </div>
            <pre class="overflow-x-auto font-mono text-xs text-zinc-400">{{ tc.result }}</pre>
          </div>
        </div>
      </div>

      <!-- 时间戳 -->
      <span v-if="!message.pending" class="font-mono text-[10px] text-base-600">
        {{ new Date(message.created_at).toLocaleTimeString('zh-CN') }}
      </span>
    </div>
  </div>
</template>

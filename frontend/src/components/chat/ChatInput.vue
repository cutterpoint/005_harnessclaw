<script setup lang="ts">
import { ref } from 'vue'
import { Send } from 'lucide-vue-next'

interface Props {
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{ send: [message: string] }>()

const text = ref('')

function handleSend(): void {
  const trimmed = text.value.trim()
  if (!trimmed || props.disabled) return
  emit('send', trimmed)
  text.value = ''
}

function handleKeydown(e: KeyboardEvent): void {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="border-t border-base-700 bg-base-900 p-4">
    <div class="flex items-end gap-3">
      <textarea
        v-model="text"
        rows="1"
        class="input-base max-h-32 min-h-[42px] flex-1 resize-none"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行..."
        :disabled="disabled"
        @keydown="handleKeydown"
      />
      <button class="btn-primary h-[42px]" :disabled="disabled || !text.trim()" @click="handleSend">
        <Send class="h-4 w-4" />
      </button>
    </div>
    <div class="mt-2 flex items-center gap-4 px-1">
      <span class="font-mono text-[10px] text-base-600">Enter 发送 · Shift+Enter 换行</span>
    </div>
  </div>
</template>

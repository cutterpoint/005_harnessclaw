<script setup lang="ts">
import { AlertTriangle, RefreshCw } from 'lucide-vue-next'

interface Props {
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: '加载失败',
})

const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16 text-center">
    <div class="flex h-14 w-14 items-center justify-center rounded-full border border-status-error/30 bg-status-error/10">
      <AlertTriangle class="h-6 w-6 text-status-error" />
    </div>
    <p class="text-sm text-status-error">{{ text }}</p>
    <button class="btn-secondary" @click="emit('retry')">
      <RefreshCw class="h-4 w-4" />
      重试
    </button>
  </div>
</template>

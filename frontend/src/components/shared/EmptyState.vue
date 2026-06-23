<script setup lang="ts">
import { Inbox } from 'lucide-vue-next'

interface Props {
  text?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  text: '暂无数据',
  description: '',
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16 text-center">
    <div class="flex h-14 w-14 items-center justify-center rounded-full border border-base-700 bg-base-850">
      <Inbox class="h-6 w-6 text-base-500" />
    </div>
    <div>
      <p class="text-sm font-medium text-zinc-400">{{ text }}</p>
      <p v-if="description" class="mt-1 text-xs text-base-500">{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16">
    <div class="h-8 w-8 animate-spin rounded-full border-2 border-base-700 border-t-amber" />
    <p class="font-mono text-xs text-base-500">{{ text }}</p>
  </div>
</template>

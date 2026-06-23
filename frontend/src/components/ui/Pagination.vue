<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

interface Props {
  page: number
  limit: number
  total: number
}

const props = defineProps<Props>()
const emit = defineEmits<{ change: [page: number] }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)))
const hasNext = computed(() => props.page < totalPages.value)
const hasPrev = computed(() => props.page > 1)

const rangeStart = computed(() =>
  props.total === 0 ? 0 : (props.page - 1) * props.limit + 1,
)
const rangeEnd = computed(() => Math.min(props.page * props.limit, props.total))

function go(page: number): void {
  if (page >= 1 && page <= totalPages.value && page !== props.page) {
    emit('change', page)
  }
}
</script>

<template>
  <div class="flex items-center justify-between gap-4 px-1 py-3">
    <div class="font-mono text-xs text-base-500">
      <span v-if="total > 0">{{ rangeStart }}-{{ rangeEnd }} / 共 {{ total }} 条</span>
      <span v-else>无数据</span>
    </div>
    <div class="flex items-center gap-1">
      <button class="btn-ghost p-1.5" :disabled="!hasPrev" @click="go(page - 1)">
        <ChevronLeft class="h-4 w-4" />
      </button>
      <span class="font-mono text-xs text-zinc-400">
        {{ page }} / {{ totalPages }}
      </span>
      <button class="btn-ghost p-1.5" :disabled="!hasNext" @click="go(page + 1)">
        <ChevronRight class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next'
import BaseModal from '@/components/ui/BaseModal.vue'

interface Props {
  modelValue: boolean
  title?: string
  text?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认删除',
  text: '此操作不可撤销，确定要继续吗？',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
}>()

function close(): void {
  emit('update:modelValue', false)
}

function confirm(): void {
  emit('confirm')
  close()
}
</script>

<template>
  <BaseModal :model-value="modelValue" :title="title" width="max-w-md" @update:model-value="close">
    <div class="flex gap-4">
      <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-status-error/30 bg-status-error/10">
        <AlertTriangle class="h-5 w-5 text-status-error" />
      </div>
      <p class="pt-1.5 text-sm text-zinc-300">{{ text }}</p>
    </div>
    <template #footer>
      <button class="btn-secondary" @click="close">取消</button>
      <button class="btn-danger" @click="confirm">确认删除</button>
    </template>
  </BaseModal>
</template>

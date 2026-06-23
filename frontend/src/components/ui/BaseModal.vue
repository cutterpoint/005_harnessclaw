<script setup lang="ts">
import { X } from 'lucide-vue-next'

interface Props {
  modelValue: boolean
  title?: string
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  width: 'max-w-lg',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function close(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-base-950/80 backdrop-blur-sm" @click="close" />
        <div :class="['relative w-full card shadow-card animate-slide-up', width]">
          <div class="flex items-center justify-between border-b border-base-700 px-5 py-4">
            <h3 class="text-base font-semibold text-zinc-100">{{ title }}</h3>
            <button class="btn-ghost p-1" @click="close">
              <X class="h-4 w-4" />
            </button>
          </div>
          <div class="px-5 py-4">
            <slot />
          </div>
          <div v-if="$slots.footer" class="flex justify-end gap-3 border-t border-base-700 px-5 py-4">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>

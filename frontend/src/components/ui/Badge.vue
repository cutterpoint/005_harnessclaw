<script setup lang="ts">
import { computed } from 'vue'

type BadgeVariant = 'default' | 'amber' | 'cyan' | 'success' | 'warning' | 'error'

interface Props {
  variant?: BadgeVariant
  dot?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  dot: false,
})

const variantClasses: Record<BadgeVariant, string> = {
  default: 'border-base-600 bg-base-800 text-zinc-400',
  amber: 'border-amber/30 bg-amber/10 text-amber',
  cyan: 'border-cyan/30 bg-cyan/10 text-cyan',
  success: 'border-status-success/30 bg-status-success/10 text-status-success',
  warning: 'border-status-warning/30 bg-status-warning/10 text-status-warning',
  error: 'border-status-error/30 bg-status-error/10 text-status-error',
}

const dotClasses: Record<BadgeVariant, string> = {
  default: 'bg-zinc-500',
  amber: 'bg-amber',
  cyan: 'bg-cyan',
  success: 'bg-status-success',
  warning: 'bg-status-warning',
  error: 'bg-status-error',
}

const classes = computed(() => variantClasses[props.variant])
const dotClass = computed(() => dotClasses[props.variant])
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-xs font-medium',
      classes,
    ]"
  >
    <span v-if="dot" :class="['h-1.5 w-1.5 rounded-full', dotClass]" />
    <slot />
  </span>
</template>

<template>
  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium" :class="classes">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  type?: 'success' | 'warning' | 'danger' | 'info' | 'default'
}>()

const classes = computed(() => {
  switch (props.type) {
    case 'success': return 'bg-green-100 text-green-700'
    case 'warning': return 'bg-yellow-100 text-yellow-700'
    case 'danger': return 'bg-red-100 text-red-700'
    case 'info': return 'bg-blue-100 text-blue-700'
    default: return 'bg-slate-100 text-slate-600'
  }
})
</script>

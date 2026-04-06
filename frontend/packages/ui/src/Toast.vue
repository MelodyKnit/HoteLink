<template>
  <Teleport to="body">
    <Transition name="toast-slide">
      <div v-if="visible" :class="['fixed top-4 right-4 z-[9999] flex items-center gap-2 rounded-lg px-4 py-3 shadow-lg text-sm font-medium max-w-sm', colorClass]" role="alert">
        <span v-if="type === 'success'" class="text-lg">✓</span>
        <span v-else-if="type === 'error'" class="text-lg">✕</span>
        <span v-else-if="type === 'warning'" class="text-lg">⚠</span>
        <span v-else class="text-lg">ℹ</span>
        <span class="flex-1">{{ message }}</span>
        <button class="ml-2 opacity-60 hover:opacity-100" @click="close">×</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

const props = defineProps<{
  visible: boolean
  message: string
  type?: ToastType
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const colorClass = computed(() => {
  switch (props.type) {
    case 'success': return 'bg-green-50 text-green-800 ring-1 ring-green-200'
    case 'error': return 'bg-red-50 text-red-800 ring-1 ring-red-200'
    case 'warning': return 'bg-yellow-50 text-yellow-800 ring-1 ring-yellow-200'
    default: return 'bg-blue-50 text-blue-800 ring-1 ring-blue-200'
  }
})

function close() {
  emit('close')
}
</script>

<style scoped>
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.3s ease;
}
.toast-slide-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-slide-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>

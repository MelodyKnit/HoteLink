<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="$emit('close')">
        <div class="flex max-h-[calc(100vh-2rem)] w-full flex-col rounded-2xl bg-white shadow-xl" :class="sizeClass">
          <div class="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <h3 class="text-lg font-semibold text-slate-900">{{ title }}</h3>
            <button class="text-slate-400 hover:text-slate-600" @click="$emit('close')">✕</button>
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <slot />
          </div>
          <div v-if="$slots.footer" class="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue'
import { lockBodyScroll, unlockBodyScroll } from './bodyScrollLock'

const props = defineProps<{
  visible: boolean
  title: string
  size?: 'sm' | 'md' | 'lg'
}>()

defineEmits<{ close: [] }>()

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm': return 'max-w-md'
    case 'lg': return 'max-w-3xl'
    default: return 'max-w-xl'
  }
})

let bodyLocked = false

watch(
  () => props.visible,
  (visible) => {
    if (visible && !bodyLocked) {
      lockBodyScroll()
      bodyLocked = true
      return
    }
    if (!visible && bodyLocked) {
      unlockBodyScroll()
      bodyLocked = false
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (!bodyLocked) return
  unlockBodyScroll()
  bodyLocked = false
})
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>

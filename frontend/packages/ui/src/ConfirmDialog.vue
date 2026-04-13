<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div v-if="confirmVisible" class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/40 px-4" @click.self="onCancel">
        <div class="flex max-h-[calc(100vh-2rem)] w-full max-w-sm flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
          <div class="flex items-start gap-4 overflow-y-auto p-6">
            <span class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-xl"
              :class="iconBg">{{ icon }}</span>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ confirmTitle }}</h3>
              <p class="mt-1.5 text-sm leading-relaxed text-slate-500">{{ confirmMessage }}</p>
            </div>
          </div>
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <button
              class="rounded-lg border border-slate-200 px-5 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
              @click="onCancel"
            >取消</button>
            <button
              class="rounded-lg px-5 py-2 text-sm font-medium text-white transition"
              :class="okBtnClass"
              @click="onOk"
            >确认</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue'
import { useConfirm } from './useConfirm'
import { lockBodyScroll, unlockBodyScroll } from './bodyScrollLock'

const { confirmVisible, confirmTitle, confirmMessage, confirmType, onOk, onCancel } = useConfirm()

const icon = computed(() => {
  if (confirmType.value === 'danger') return '🗑️'
  if (confirmType.value === 'info') return 'ℹ️'
  return '⚠️'
})

const iconBg = computed(() => {
  if (confirmType.value === 'danger') return 'bg-red-50'
  if (confirmType.value === 'info') return 'bg-blue-50'
  return 'bg-amber-50'
})

const okBtnClass = computed(() => {
  if (confirmType.value === 'danger') return 'bg-red-600 hover:bg-red-700'
  if (confirmType.value === 'info') return 'bg-blue-600 hover:bg-blue-700'
  return 'bg-amber-500 hover:bg-amber-600'
})

let bodyLocked = false

watch(
  confirmVisible,
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
.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.2s ease;
}
.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}
.confirm-fade-enter-active .max-w-sm,
.confirm-fade-leave-active .max-w-sm {
  transition: transform 0.2s ease;
}
.confirm-fade-enter-from .max-w-sm {
  transform: scale(0.95) translateY(-8px);
}
.confirm-fade-leave-to .max-w-sm {
  transform: scale(0.95) translateY(-8px);
}
</style>

import { ref } from 'vue'
import type { ToastType } from './Toast.vue'

const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<ToastType>('info')
let toastTimer: ReturnType<typeof setTimeout> | null = null

export function useToast() {
  function showToast(message: string, type: ToastType = 'info', duration = 3000) {
    if (toastTimer) clearTimeout(toastTimer)
    toastMessage.value = message
    toastType.value = type
    toastVisible.value = true
    toastTimer = setTimeout(() => {
      toastVisible.value = false
    }, duration)
  }

  function closeToast() {
    toastVisible.value = false
    if (toastTimer) clearTimeout(toastTimer)
  }

  return {
    toastVisible,
    toastMessage,
    toastType,
    showToast,
    closeToast,
  }
}

import { ref } from 'vue'

const visible = ref(false)
const confirmTitle = ref('确认操作')
const confirmMessage = ref('')
const confirmType = ref<'danger' | 'warning' | 'info'>('warning')
let _resolve: ((val: boolean) => void) | null = null

export function useConfirm() {
  function confirm(message: string, options?: { title?: string; type?: 'danger' | 'warning' | 'info' }): Promise<boolean> {
    confirmMessage.value = message
    confirmTitle.value = options?.title ?? '确认操作'
    confirmType.value = options?.type ?? 'warning'
    visible.value = true
    return new Promise((resolve) => {
      _resolve = resolve
    })
  }

  function onOk() {
    visible.value = false
    _resolve?.(true)
    _resolve = null
  }

  function onCancel() {
    visible.value = false
    _resolve?.(false)
    _resolve = null
  }

  return { confirmVisible: visible, confirmTitle, confirmMessage, confirmType, confirm, onOk, onCancel }
}

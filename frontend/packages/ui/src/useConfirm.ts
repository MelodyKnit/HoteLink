import { ref } from 'vue'

const visible = ref(false)
const confirmTitle = ref('确认操作')
const confirmMessage = ref('')
const confirmType = ref<'danger' | 'warning' | 'info'>('warning')

type ConfirmOptions = { title?: string; type?: 'danger' | 'warning' | 'info' }
type ConfirmTask = {
  message: string
  options?: ConfirmOptions
  resolve: (val: boolean) => void
}

const queue: ConfirmTask[] = []
let currentTask: ConfirmTask | null = null

function flushNextTask() {
  if (currentTask || queue.length === 0) return
  currentTask = queue.shift() || null
  if (!currentTask) return
  confirmMessage.value = currentTask.message
  confirmTitle.value = currentTask.options?.title ?? '确认操作'
  confirmType.value = currentTask.options?.type ?? 'warning'
  visible.value = true
}

export function useConfirm() {
  function confirm(message: string, options?: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) => {
      queue.push({ message, options, resolve })
      flushNextTask()
    })
  }

  function settleCurrent(result: boolean) {
    visible.value = false
    if (!currentTask) return
    currentTask.resolve(result)
    currentTask = null
    flushNextTask()
  }

  function onOk() {
    settleCurrent(true)
  }

  function onCancel() {
    settleCurrent(false)
  }

  return { confirmVisible: visible, confirmTitle, confirmMessage, confirmType, confirm, onOk, onCancel }
}

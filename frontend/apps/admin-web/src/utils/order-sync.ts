export type OrderSyncAction = 'check-in' | 'check-out' | 'extend-stay' | 'switch-room' | 'change-status' | 'refresh'

export interface OrderSyncPayload {
  action: OrderSyncAction
  orderId?: number
  source?: string
  timestamp?: number
}

const EVENT_NAME = 'hotelink-admin-order-updated'
const CHANNEL_NAME = 'hotelink-admin-order-sync'

function isBroadcastChannelSupported(): boolean {
  return typeof window !== 'undefined' && typeof window.BroadcastChannel !== 'undefined'
}

export function emitOrderSync(payload: OrderSyncPayload) {
  if (typeof window === 'undefined') return
  const nextPayload: OrderSyncPayload = {
    ...payload,
    timestamp: Date.now(),
  }

  window.dispatchEvent(new CustomEvent<OrderSyncPayload>(EVENT_NAME, { detail: nextPayload }))

  if (isBroadcastChannelSupported()) {
    const channel = new BroadcastChannel(CHANNEL_NAME)
    channel.postMessage(nextPayload)
    channel.close()
  }
}

export function onOrderSync(handler: (payload: OrderSyncPayload) => void) {
  if (typeof window === 'undefined') {
    return () => {}
  }

  const onWindowEvent = (event: Event) => {
    const customEvent = event as CustomEvent<OrderSyncPayload>
    if (customEvent.detail) {
      handler(customEvent.detail)
    }
  }

  window.addEventListener(EVENT_NAME, onWindowEvent)

  let channel: BroadcastChannel | null = null
  if (isBroadcastChannelSupported()) {
    channel = new BroadcastChannel(CHANNEL_NAME)
    channel.onmessage = (event: MessageEvent<OrderSyncPayload>) => {
      if (event.data) {
        handler(event.data)
      }
    }
  }

  return () => {
    window.removeEventListener(EVENT_NAME, onWindowEvent)
    if (channel) {
      channel.close()
    }
  }
}
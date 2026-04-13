const LOCK_COUNT_KEY = 'data-hotelink-scroll-lock-count'
const PREV_OVERFLOW_KEY = 'data-hotelink-prev-overflow'
const PREV_PADDING_RIGHT_KEY = 'data-hotelink-prev-padding-right'

function readLockCount(body: HTMLElement): number {
  const raw = body.getAttribute(LOCK_COUNT_KEY) || '0'
  const parsed = Number.parseInt(raw, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
}

export function lockBodyScroll() {
  if (typeof document === 'undefined' || typeof window === 'undefined') return
  const body = document.body
  const current = readLockCount(body)

  if (current === 0) {
    body.setAttribute(PREV_OVERFLOW_KEY, body.style.overflow || '')
    body.setAttribute(PREV_PADDING_RIGHT_KEY, body.style.paddingRight || '')
    const scrollbarWidth = Math.max(window.innerWidth - document.documentElement.clientWidth, 0)
    body.style.overflow = 'hidden'
    if (scrollbarWidth > 0) {
      body.style.paddingRight = `${scrollbarWidth}px`
    }
  }

  body.setAttribute(LOCK_COUNT_KEY, String(current + 1))
}

export function unlockBodyScroll() {
  if (typeof document === 'undefined') return
  const body = document.body
  const current = readLockCount(body)
  if (current <= 1) {
    body.style.overflow = body.getAttribute(PREV_OVERFLOW_KEY) || ''
    body.style.paddingRight = body.getAttribute(PREV_PADDING_RIGHT_KEY) || ''
    body.removeAttribute(LOCK_COUNT_KEY)
    body.removeAttribute(PREV_OVERFLOW_KEY)
    body.removeAttribute(PREV_PADDING_RIGHT_KEY)
    return
  }
  body.setAttribute(LOCK_COUNT_KEY, String(current - 1))
}

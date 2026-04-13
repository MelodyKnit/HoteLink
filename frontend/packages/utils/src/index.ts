// 处理 formatDate 业务流程。
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// 处理 formatDateTime 业务流程。
export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return `${formatDate(d)} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

// 处理 formatMoney 业务流程。
export function formatMoney(amount: number | string): string {
  const n = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(n)) return '0.00'
  return n.toFixed(2)
}

export function buildImageThumbUrl(url: string | null | undefined, width = 56, height = 40): string {
  const raw = String(url || '').trim()
  if (!raw) return ''
  if (raw.startsWith('/api/v1/common/image-thumb')) return raw

  const safeWidth = Math.min(2048, Math.max(16, Math.round(Number(width) || 56)))
  const safeHeight = Math.min(2048, Math.max(16, Math.round(Number(height) || 40)))

  const baseOrigin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost'

  try {
    const parsed = new URL(raw, baseOrigin)
    if (!parsed.pathname.startsWith('/media/')) {
      return raw
    }
    return `/api/v1/common/image-thumb?url=${encodeURIComponent(parsed.pathname)}&w=${safeWidth}&h=${safeHeight}`
  } catch {
    if (!raw.startsWith('/media/')) {
      return raw
    }
    return `/api/v1/common/image-thumb?url=${encodeURIComponent(raw)}&w=${safeWidth}&h=${safeHeight}`
  }
}

export function debounce<T extends (...args: unknown[]) => void>(fn: T, delay = 300): T {
  let timer: ReturnType<typeof setTimeout> | null = null
  return ((...args: unknown[]) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }) as unknown as T
}

export const ORDER_STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending_payment: { label: '待支付', color: 'text-yellow-600' },
  paid: { label: '已支付', color: 'text-blue-600' },
  confirmed: { label: '已确认', color: 'text-indigo-600' },
  checked_in: { label: '已入住', color: 'text-green-600' },
  completed: { label: '已完成', color: 'text-gray-600' },
  cancelled: { label: '已取消', color: 'text-red-600' },
  refunding: { label: '退款中', color: 'text-orange-600' },
  refunded: { label: '已退款', color: 'text-gray-500' },
}

export const ROOM_STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  available: { label: '空闲', color: 'text-green-700', bg: 'bg-green-100' },
  reserved: { label: '已预订', color: 'text-blue-700', bg: 'bg-blue-100' },
  occupied: { label: '在住', color: 'text-orange-700', bg: 'bg-orange-100' },
  cleaning: { label: '清扫中', color: 'text-yellow-700', bg: 'bg-yellow-100' },
  maintenance: { label: '维修中', color: 'text-red-700', bg: 'bg-red-100' },
  offline: { label: '已下线', color: 'text-gray-700', bg: 'bg-gray-200' },
}

export const HOTEL_STATUS_MAP: Record<string, string> = {
  draft: '草稿',
  online: '已上架',
  offline: '已下架',
}

export const BED_TYPE_MAP: Record<string, string> = {
  single: '单人床',
  double: '双人床',
  queen: '大床',
  twin: '双床',
  family: '家庭床',
}

export const PAYMENT_METHOD_MAP: Record<string, string> = {
  mock: '模拟支付',
  wechat: '微信支付',
  alipay: '支付宝',
  cash: '现金',
  card: '银行卡',
}

export const PAYMENT_STATUS_MAP: Record<string, string> = {
  unpaid: '未支付',
  paid: '已支付',
  failed: '支付失败',
  refunded: '已退款',
}

export type FieldErrors = Record<string, string>

const DEFAULT_API_FIELD_LABELS: Record<string, string> = {
  amount: '金额',
  birthday: '生日',
  check_in_date: '入住日期',
  check_out_date: '离店日期',
  confirm_password: '确认密码',
  consume_amount: '消费金额',
  content: '内容',
  email: '邮箱',
  end_date: '结束日期',
  guest_count: '入住人数',
  guest_mobile: '手机号',
  guest_name: '入住人姓名',
  hotel_id: '酒店',
  invoice_title_id: '发票抬头',
  invoice_type: '发票类型',
  mobile: '手机号',
  name: '名称',
  new_password: '新密码',
  old_password: '当前密码',
  order_id: '订单',
  password: '密码',
  payment_method: '支付方式',
  reason: '原因',
  role: '角色',
  room_no: '房间号',
  room_type_id: '房型',
  score: '评分',
  start_date: '开始日期',
  target_status: '目标状态',
  tax_no: '税号',
  title: '抬头名称',
  username: '用户名',
}

const GENERIC_API_MESSAGES = [
  /^This field may not be blank\.$/,
  /^This field is required\.$/,
  /^This field may not be null\.$/,
  /^Not a valid string\.$/,
  /^Not a valid integer\.$/,
  /^Enter a valid email address\.$/,
  /^Enter a valid URL\.$/,
  /^Ensure this field has no more than \d+ characters\.$/,
  /^Ensure this field has at least \d+ characters\.$/,
  /^Ensure this value is greater than or equal to \d+\.$/,
  /^Ensure this value is less than or equal to \d+\.$/,
]

function translateApiMessage(message: string): string {
  return message
    .replace('This field may not be blank.', '不能为空')
    .replace('This field is required.', '为必填项')
    .replace('This field may not be null.', '不能为空')
    .replace('Not a valid string.', '格式不正确')
    .replace('Not a valid integer.', '格式不正确')
    .replace('Enter a valid email address.', '格式不正确，请填写有效邮箱')
    .replace('Enter a valid URL.', '格式不正确，请填写有效链接')
    .replace(/Ensure this field has no more than (\d+) characters\./, '不能超过 $1 个字符')
    .replace(/Ensure this field has at least (\d+) characters\./, '至少需要 $1 个字符')
    .replace(/Ensure this value is greater than or equal to (\d+)\./, '不能小于 $1')
    .replace(/Ensure this value is less than or equal to (\d+)\./, '不能大于 $1')
}

function isGenericApiMessage(message: string): boolean {
  return GENERIC_API_MESSAGES.some((pattern) => pattern.test(message))
}

function buildFieldPrefix(field: string, fieldMap?: Record<string, string>): string {
  return fieldMap?.[field] || DEFAULT_API_FIELD_LABELS[field] || field
}

function toSingleMessage(value: unknown): string {
  if (Array.isArray(value)) {
    return String(value[0] ?? '')
  }
  return String(value ?? '')
}

export function extractApiFieldErrors(
  res: { data?: unknown },
  fieldMap?: Record<string, string>,
): FieldErrors {
  const errors = (res.data as Record<string, unknown>)?.errors
  if (!errors || typeof errors !== 'object') {
    return {}
  }

  return Object.entries(errors as Record<string, unknown>).reduce<FieldErrors>((acc, [field, value]) => {
    const rawMessage = toSingleMessage(value).trim()
    if (!rawMessage) {
      return acc
    }

    const translated = translateApiMessage(rawMessage)
    const prefix = buildFieldPrefix(field, fieldMap)
    acc[field] = isGenericApiMessage(rawMessage) ? `${prefix}${translated}` : translated
    return acc
  }, {})
}

export function isValidChineseMobile(value: string): boolean {
  return /^1\d{10}$/.test(value.trim())
}

export function isValidEmailAddress(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
}

export function isValidContactInfo(value: string): boolean {
  const normalized = value.trim()
  if (!normalized) return true
  return isValidChineseMobile(normalized) || isValidEmailAddress(normalized)
}

export function isValidTaxNumber(value: string): boolean {
  return /^[0-9A-Z]{15,20}$/i.test(value.trim())
}

export function validateUsername(value: string, options?: { label?: string; minLength?: number; maxLength?: number }): string {
  const normalized = value.trim()
  const label = options?.label || '用户名'
  const minLength = options?.minLength ?? 4
  const maxLength = options?.maxLength ?? 30

  if (!normalized) return `请输入${label}`
  if (normalized.length < minLength) return `${label}至少 ${minLength} 个字符`
  if (normalized.length > maxLength) return `${label}不能超过 ${maxLength} 个字符`
  if (!/^[\w\-\u4e00-\u9fa5]+$/u.test(normalized)) {
    return `${label}仅支持中文、英文、数字、下划线和短横线`
  }
  return ''
}

export function validatePassword(value: string, options?: { label?: string; minLength?: number; requireCurrentPassword?: boolean }): string {
  const label = options?.label || '密码'
  const minLength = options?.minLength ?? 8
  if (!value) return `请输入${label}`
  if (value.length < minLength) return `${label}至少 ${minLength} 位`
  if (/\s/.test(value)) return `${label}不能包含空格`
  return ''
}

export function getPasswordStrength(password: string, minLength = 8): {
  level: 'empty' | 'weak' | 'fair' | 'good' | 'strong'
  label: string
  hint: string
  percentage: number
} {
  if (!password) {
    return {
      level: 'empty',
      label: '未设置',
      hint: `建议至少 ${minLength} 位，并组合字母、数字或符号`,
      percentage: 0,
    }
  }

  const hasLower = /[a-z]/.test(password)
  const hasUpper = /[A-Z]/.test(password)
  const hasNumber = /\d/.test(password)
  const hasSymbol = /[^A-Za-z0-9]/.test(password)
  const categoryCount = [hasLower, hasUpper, hasNumber, hasSymbol].filter(Boolean).length
  let score = 0

  if (password.length >= minLength) score += 1
  if (password.length >= Math.max(12, minLength + 2)) score += 1
  if (categoryCount >= 2) score += 1
  if (categoryCount >= 3) score += 1

  if (password.length < minLength) {
    return {
      level: 'weak',
      label: '偏弱',
      hint: `至少需要 ${minLength} 位`,
      percentage: 25,
    }
  }

  if (score <= 2) {
    return {
      level: 'fair',
      label: '一般',
      hint: '建议混合字母、数字或符号，安全性会更高',
      percentage: 50,
    }
  }

  if (score === 3) {
    return {
      level: 'good',
      label: '良好',
      hint: '已经比较稳妥，再加入大小写或符号会更安全',
      percentage: 75,
    }
  }

  return {
    level: 'strong',
    label: '很强',
    hint: '当前密码强度不错，可以放心使用',
    percentage: 100,
  }
}

/**
 * 从后端 API 响应中提取用户友好的错误消息。
 * 当 res.data.errors 存在时，将字段校验错误拼成中文提示。
 */
export function extractApiError(
  res: { message?: string; data?: unknown },
  fallback = '操作失败，请重试',
  fieldMap?: Record<string, string>,
): string {
  const fieldErrors = extractApiFieldErrors(res, fieldMap)
  const parts = Object.values(fieldErrors)
  if (parts.length) return parts.join('；')
  return translateApiMessage(res.message || fallback)
}

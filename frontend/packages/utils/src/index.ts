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

/**
 * 从后端 API 响应中提取用户友好的错误消息。
 * 当 res.data.errors 存在时，将字段校验错误拼成中文提示。
 */
export function extractApiError(res: { message?: string; data?: unknown }, fallback = '操作失败，请重试'): string {
  const errors = (res.data as Record<string, unknown>)?.errors
  if (errors && typeof errors === 'object') {
    const fieldMap: Record<string, string> = {
      room_no: '房间号',
      order_id: '订单',
      guest_name: '入住人姓名',
      guest_mobile: '手机号',
      check_in_date: '入住日期',
      check_out_date: '离店日期',
      guest_count: '入住人数',
      payment_method: '支付方式',
      score: '评分',
      content: '内容',
      name: '名称',
      price: '价格',
      amount: '金额',
      username: '用户名',
      password: '密码',
      consume_amount: '消费金额',
      target_status: '目标状态',
    }
    const parts: string[] = []
    for (const [field, msgs] of Object.entries(errors as Record<string, string[]>)) {
      const label = fieldMap[field] || field
      const msg = Array.isArray(msgs) ? msgs[0] : String(msgs)
      // 常见 DRF 英文错误翻译
      const translated = msg
        .replace('This field may not be blank.', '不能为空')
        .replace('This field is required.', '为必填项')
        .replace('This field may not be null.', '不能为空')
        .replace(/Ensure this field has no more than (\d+) characters./, '不能超过 $1 个字符')
        .replace(/Ensure this value is greater than or equal to (\d+)./, '不能小于 $1')
      parts.push(`${label}${translated}`)
    }
    if (parts.length) return parts.join('；')
  }
  return res.message || fallback
}

export interface InventoryBulkDraft {
  roomTypeIds: number[]
  startDate: string
  endDate: string
  price?: string | number | null
  weekendPrice?: string | number | null
  stock?: string | number | null
  status?: string
  weekdays?: number[]
}

export interface InventoryBulkValidationResult {
  valid: boolean
  message: string
  dateCount: number
}

function parseIsoDateToUtc(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const date = new Date(Date.UTC(year, month - 1, day))
  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null
  }
  return date
}

/**
 * Builds an inclusive date list from ISO date strings.
 *
 * @param startDate - Start date in YYYY-MM-DD format.
 * @param endDate - End date in YYYY-MM-DD format.
 * @returns Inclusive date strings, or an empty list when input is invalid.
 */
export function buildInclusiveDateList(startDate: string, endDate: string): string[] {
  if (!startDate || !endDate || startDate > endDate) return []
  const start = parseIsoDateToUtc(startDate)
  const end = parseIsoDateToUtc(endDate)
  if (!start || !end) return []

  const dates: string[] = []
  for (const cursor = new Date(start); cursor <= end; cursor.setUTCDate(cursor.getUTCDate() + 1)) {
    dates.push(cursor.toISOString().slice(0, 10))
  }
  return dates
}

/**
 * Normalizes selected weekdays to the backend contract where Monday is 0.
 *
 * @param weekdays - Raw selected weekday values.
 * @returns Deduplicated weekday values sorted ascending.
 */
export function normalizeInventoryBulkWeekdays(weekdays?: number[]): number[] {
  const values = Array.isArray(weekdays) && weekdays.length ? weekdays : [0, 1, 2, 3, 4, 5, 6]
  return Array.from(new Set(values.filter(item => Number.isInteger(item) && item >= 0 && item <= 6))).sort((a, b) => a - b)
}

/**
 * Validates the admin inventory bulk-edit draft before submitting to the API.
 *
 * @param draft - Current bulk-edit form state.
 * @returns Validation status and the selected date count.
 */
export function validateInventoryBulkDraft(draft: InventoryBulkDraft): InventoryBulkValidationResult {
  if (!draft.roomTypeIds.length) return { valid: false, message: '请选择至少一个房型', dateCount: 0 }
  if (!draft.startDate || !draft.endDate) return { valid: false, message: '请选择批量设置日期范围', dateCount: 0 }
  if (draft.startDate > draft.endDate) return { valid: false, message: '开始日期不能晚于结束日期', dateCount: 0 }

  const dateCount = buildInclusiveDateList(draft.startDate, draft.endDate).length
  if (dateCount > 366) return { valid: false, message: '批量设置日期范围不能超过 366 天', dateCount }

  const hasPrice = draft.price !== '' && draft.price !== null && draft.price !== undefined
  const hasWeekendPrice = draft.weekendPrice !== '' && draft.weekendPrice !== null && draft.weekendPrice !== undefined
  const hasStock = draft.stock !== '' && draft.stock !== null && draft.stock !== undefined
  const hasStatus = Boolean(draft.status)
  if (!hasPrice && !hasWeekendPrice && !hasStock && !hasStatus) {
    return { valid: false, message: '至少需要设置价格、周末价、库存或状态中的一项', dateCount }
  }

  if ((hasPrice && Number(draft.price) < 0) || (hasWeekendPrice && Number(draft.weekendPrice) < 0)) {
    return { valid: false, message: '价格不能小于 0', dateCount }
  }
  if (hasStock && (!Number.isInteger(Number(draft.stock)) || Number(draft.stock) < 0)) {
    return { valid: false, message: '库存必须是大于等于 0 的整数', dateCount }
  }

  const weekdays = normalizeInventoryBulkWeekdays(draft.weekdays)
  if (!weekdays.length) return { valid: false, message: '请选择至少一个适用星期', dateCount }

  return { valid: true, message: '', dateCount }
}

import { describe, expect, it } from 'vitest'

import {
  buildInclusiveDateList,
  normalizeInventoryBulkWeekdays,
  validateInventoryBulkDraft,
} from './inventory-bulk'

describe('inventory bulk helpers', () => {
  it('builds inclusive ISO date ranges', () => {
    expect(buildInclusiveDateList('2026-05-10', '2026-05-12')).toEqual([
      '2026-05-10',
      '2026-05-11',
      '2026-05-12',
    ])
    expect(buildInclusiveDateList('2026-05-12', '2026-05-10')).toEqual([])
  })

  it('normalizes weekday selections for the backend contract', () => {
    expect(normalizeInventoryBulkWeekdays([6, 1, 6, 0, 9])).toEqual([0, 1, 6])
    expect(normalizeInventoryBulkWeekdays([])).toEqual([0, 1, 2, 3, 4, 5, 6])
  })

  it('requires at least one changed inventory field', () => {
    const result = validateInventoryBulkDraft({
      roomTypeIds: [1],
      startDate: '2026-05-10',
      endDate: '2026-05-12',
      price: '',
      weekendPrice: '',
      stock: '',
      status: '',
      weekdays: [0, 1],
    })

    expect(result.valid).toBe(false)
    expect(result.message).toContain('至少需要设置')
  })

  it('accepts a valid bulk stock and status draft', () => {
    const result = validateInventoryBulkDraft({
      roomTypeIds: [1, 2],
      startDate: '2026-05-10',
      endDate: '2026-05-12',
      stock: 5,
      status: 'available',
      weekdays: [0, 1, 2, 3, 4, 5, 6],
    })

    expect(result).toEqual({ valid: true, message: '', dateCount: 3 })
  })
})

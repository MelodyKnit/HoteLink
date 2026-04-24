import { describe, expect, it } from 'vitest'

import {
  buildImageThumbUrl,
  extractApiFieldErrors,
  formatDate,
  formatMoney,
  isValidChineseMobile,
} from './index'

describe('utils helpers', () => {
  it('formats valid dates and rejects invalid input', () => {
    expect(formatDate(new Date('2026-04-24T00:00:00Z'))).toBe('2026-04-24')
    expect(formatDate('invalid-date')).toBe('')
  })

  it('formats money with two decimals', () => {
    expect(formatMoney(12)).toBe('12.00')
    expect(formatMoney('19.9')).toBe('19.90')
    expect(formatMoney('NaN')).toBe('0.00')
  })

  it('builds thumb proxy urls only for site media assets', () => {
    expect(buildImageThumbUrl('/media/hotels/demo.jpg', 80, 60)).toBe(
      '/api/v1/common/image-thumb?url=%2Fmedia%2Fhotels%2Fdemo.jpg&w=80&h=60',
    )
    expect(buildImageThumbUrl('https://cdn.example.com/demo.jpg')).toBe(
      'https://cdn.example.com/demo.jpg',
    )
  })

  it('extracts translated field errors from api payloads', () => {
    const fieldErrors = extractApiFieldErrors({
      data: {
        errors: {
          email: ['Enter a valid email address.'],
          stock: ['Ensure this value is greater than or equal to 0.'],
          username: ['用户名已存在'],
        },
      },
    })

    expect(fieldErrors.email).toBe('邮箱格式不正确，请填写有效邮箱')
    expect(fieldErrors.stock).toBe('库存不能小于 0')
    expect(fieldErrors.username).toBe('用户名已存在')
  })

  it('validates chinese mobile numbers', () => {
    expect(isValidChineseMobile('13800138000')).toBe(true)
    expect(isValidChineseMobile('23800138000')).toBe(false)
  })
})

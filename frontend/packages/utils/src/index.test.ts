import { describe, expect, it } from 'vitest'

import {
  ORDER_STATUS_MAP,
  PAYMENT_GATEWAY_SWITCH_META,
  POINT_TYPE_MAP,
  buildImageThumbList,
  buildImageThumbUrl,
  extractApiFieldErrors,
  formatDate,
  formatDateTime,
  formatMoney,
  INVOICE_STATUS_MAP,
  isBusinessDateBeforeToday,
  isBusinessDateOnOrBeforeToday,
  isValidChineseMobile,
  normalizeImageList,
  resolveAdminUserId,
  suggestUniquePaymentGatewayName,
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

  it('resolves admin account operations with User.id before profile id', () => {
    expect(resolveAdminUserId({ id: 3, user_id: 99 })).toBe(99)
    expect(resolveAdminUserId({ id: 3 })).toBe(3)
    expect(resolveAdminUserId({})).toBe(0)
  })

  it('formats date time into a compact local timestamp', () => {
    expect(formatDateTime('2026-05-10T15:41:34.672170+08:00')).toBe('2026-05-10 15:41:34')
    expect(formatDateTime('invalid-date')).toBe('')
  })

  it('compares business dates without UTC timezone drift', () => {
    expect(isBusinessDateOnOrBeforeToday('2026-05-10', '2026-05-10')).toBe(true)
    expect(isBusinessDateOnOrBeforeToday('2026-05-11', '2026-05-10')).toBe(false)
    expect(isBusinessDateBeforeToday('2026-05-09', '2026-05-10')).toBe(true)
    expect(isBusinessDateBeforeToday('invalid', '2026-05-10')).toBe(false)
  })

  it('builds thumb proxy urls only for site media assets', () => {
    expect(buildImageThumbUrl('/media/hotels/demo.jpg', 80, 60)).toBe(
      '/api/v1/common/image-thumb?url=%2Fmedia%2Fhotels%2Fdemo.jpg&w=80&h=60',
    )
    expect(buildImageThumbUrl('https://cdn.example.com/demo.jpg')).toBe(
      'https://cdn.example.com/demo.jpg',
    )
  })

  it('normalizes raw image payloads and builds thumbs for review images', () => {
    expect(normalizeImageList(['/media/reviews/a.jpg', '  ', null])).toEqual([
      '/media/reviews/a.jpg',
    ])
    expect(normalizeImageList('["/media/reviews/a.jpg","/media/reviews/b.jpg"]')).toEqual([
      '/media/reviews/a.jpg',
      '/media/reviews/b.jpg',
    ])
    expect(buildImageThumbList('["/media/reviews/a.jpg"]', 160, 160)).toEqual([
      '/api/v1/common/image-thumb?url=%2Fmedia%2Freviews%2Fa.jpg&w=160&h=160',
    ])
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

  it('exposes unified payment gateway switch metadata', () => {
    expect(PAYMENT_GATEWAY_SWITCH_META).toEqual([
      {
        key: 'enabled',
        label: '启用网关',
        description: '保存后参与用户端支付方式展示与真实下单路由。',
        tone: 'teal',
      },
      {
        key: 'sandbox',
        label: '沙箱 / 联调',
        description: '标记当前商户用于测试、联调或沙箱环境。',
        tone: 'amber',
      },
    ])
  })

  it('suggests unique payment gateway names from existing identifiers', () => {
    expect(suggestUniquePaymentGatewayName('Wechat Main', [])).toBe('wechat_main')
    expect(suggestUniquePaymentGatewayName('Wechat Main', ['wechat_main'])).toBe('wechat_main_2')
    expect(suggestUniquePaymentGatewayName('***', [])).toBe('gateway')
  })

  it('maps split point types to user-facing labels', () => {
    expect(POINT_TYPE_MAP.consume).toBe('消费积分')
    expect(POINT_TYPE_MAP.member).toBe('会员积分')
  })

  it('maps invoice processing statuses to unified badges', () => {
    expect(INVOICE_STATUS_MAP.pending.label).toBe('待处理')
    expect(INVOICE_STATUS_MAP.issued.bg).toBe('bg-emerald-100')
  })

  it('maps no-show orders to a dedicated lifecycle label', () => {
    expect(ORDER_STATUS_MAP.no_show.label).toBe('未入住')
  })
})

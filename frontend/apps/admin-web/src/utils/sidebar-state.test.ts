import { describe, expect, it, vi } from 'vitest'

import {
  ADMIN_SIDEBAR_COLLAPSED_GROUPS_STORAGE_KEY,
  readAdminSidebarCollapsedGroups,
  writeAdminSidebarCollapsedGroups,
} from './sidebar-state'

describe('admin sidebar state helpers', () => {
  it('defaults to no collapsed groups when no persisted value exists', () => {
    expect(readAdminSidebarCollapsedGroups(null)).toEqual([])
    expect(readAdminSidebarCollapsedGroups({ getItem: () => null })).toEqual([])
  })

  it('restores collapsed group labels from a persisted json array', () => {
    expect(readAdminSidebarCollapsedGroups({ getItem: () => '["房态与资源","订单与前台"]' })).toEqual(['房态与资源', '订单与前台'])
    expect(readAdminSidebarCollapsedGroups({ getItem: () => '"unexpected"' })).toEqual([])
    expect(readAdminSidebarCollapsedGroups({ getItem: () => '{bad json' })).toEqual([])
  })

  it('writes collapsed groups using a stable storage key', () => {
    const setItem = vi.fn()

    writeAdminSidebarCollapsedGroups(['房态与资源', '订单与前台', '房态与资源'], { setItem })

    expect(setItem).toHaveBeenCalledTimes(1)
    expect(setItem).toHaveBeenNthCalledWith(
      1,
      ADMIN_SIDEBAR_COLLAPSED_GROUPS_STORAGE_KEY,
      '["房态与资源","订单与前台"]',
    )
  })
})

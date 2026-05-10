const ADMIN_SIDEBAR_COLLAPSED_GROUPS_STORAGE_KEY = 'hotelink_admin_sidebar_collapsed_groups'

type StorageReader = Pick<Storage, 'getItem'>
type StorageWriter = Pick<Storage, 'setItem'>

/**
 * Reads the persisted admin sidebar collapsed group labels from local storage.
 *
 * @param storage - Optional storage-like object used by tests.
 * @returns Sidebar group labels that should start in collapsed mode.
 */
export function readAdminSidebarCollapsedGroups(storage?: StorageReader | null): string[] {
  const target = storage ?? (typeof window !== 'undefined' ? window.localStorage : null)
  if (!target) return []

  try {
    const raw = target.getItem(ADMIN_SIDEBAR_COLLAPSED_GROUPS_STORAGE_KEY)
    if (!raw) return []

    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []

    return parsed.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
  } catch {
    return []
  }
}

/**
 * Persists the admin sidebar collapsed groups for the next page load.
 *
 * @param labels - Group labels that should remain collapsed after refresh.
 * @param storage - Optional storage-like object used by tests.
 */
export function writeAdminSidebarCollapsedGroups(labels: string[], storage?: StorageWriter | null): void {
  const target = storage ?? (typeof window !== 'undefined' ? window.localStorage : null)
  if (!target) return

  try {
    const normalized = Array.from(new Set(labels.filter(item => item.trim().length > 0)))
    target.setItem(ADMIN_SIDEBAR_COLLAPSED_GROUPS_STORAGE_KEY, JSON.stringify(normalized))
  } catch {
    // Ignore storage write failures so the layout still works in restricted environments.
  }
}

export { ADMIN_SIDEBAR_COLLAPSED_GROUPS_STORAGE_KEY }

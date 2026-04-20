<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-white shadow-sm">
      <div class="flex items-center justify-between px-4 py-3">
        <button @click="selectMode ? exitSelect() : $router.back()"
          class="flex h-8 w-8 items-center justify-center rounded-full hover:bg-gray-100">
          <svg class="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 class="text-base font-semibold text-gray-900">
          {{ selectMode ? `已选 ${selected.size} 条` : '消息通知' }}
          <span v-if="!selectMode && unreadCount > 0"
            class="ml-1.5 rounded-full bg-red-500 px-1.5 py-0.5 text-[11px] font-bold text-white">
            {{ unreadCount }}
          </span>
        </h1>
        <button @click="toggleSelectMode"
          class="rounded-full px-2.5 py-1 text-xs font-medium transition"
          :class="selectMode ? 'bg-brand/10 text-brand' : 'text-gray-500 hover:bg-gray-100'">
          {{ selectMode ? '取消' : '管理' }}
        </button>
      </div>

      <!-- Select-mode floating toolbar -->
      <Transition
        enter-active-class="transition duration-200"
        enter-from-class="opacity-0 -translate-y-1"
        leave-active-class="transition duration-150"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <div v-if="selectMode" class="flex items-center gap-0 border-t border-gray-100 bg-white px-3 py-2">
          <!-- Select all -->
          <button @click="toggleSelectAll"
            class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100">
            <span class="flex h-4 w-4 items-center justify-center rounded border-2 transition"
              :class="allSelected ? 'border-brand bg-brand' : 'border-gray-300'">
              <svg v-if="allSelected" class="h-3 w-3 text-white" viewBox="0 0 12 12" fill="currentColor">
                <path d="M2 6l3 3 5-5" stroke="white" stroke-width="1.8" fill="none" stroke-linecap="round"/>
              </svg>
            </span>
            全选
          </button>
          <div class="mx-1 h-5 w-px bg-gray-200"></div>
          <!-- Mark read -->
          <button @click="batchMarkRead" :disabled="selected.size === 0"
            class="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition disabled:opacity-30"
            :class="selected.size > 0 ? 'text-brand hover:bg-brand/10' : 'text-gray-300'">
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            已读
          </button>
          <!-- Mark unread -->
          <button @click="batchMarkUnread" :disabled="selected.size === 0"
            class="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition disabled:opacity-30"
            :class="selected.size > 0 ? 'text-blue-500 hover:bg-blue-50' : 'text-gray-300'">
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            未读
          </button>
          <!-- Delete selected -->
          <button @click="batchDelete" :disabled="selected.size === 0"
            class="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition disabled:opacity-30"
            :class="selected.size > 0 ? 'text-red-400 hover:bg-red-50' : 'text-gray-300'">
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            删除
          </button>
          <div class="ml-auto">
            <!-- Delete all (non-selective) -->
            <button @click="deleteAll"
              class="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-400 hover:bg-red-50 hover:text-red-400 transition">
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
              清空
            </button>
          </div>
        </div>
      </Transition>

      <!-- Non-select mode: mark all read -->
      <div v-if="!selectMode" class="flex items-center justify-between border-t border-gray-50 px-4 py-1.5">
        <div class="flex gap-0 overflow-x-auto">
          <button
            v-for="tab in typeTabs" :key="tab.value"
            @click="activeType = tab.value; expandedId = null"
            class="flex-shrink-0 px-3 py-1.5 text-xs font-medium transition-colors"
            :class="activeType === tab.value ? 'border-b-2 border-brand text-brand' : 'text-gray-500 hover:text-gray-700'"
          >{{ tab.label }}</button>
        </div>
        <button v-if="unreadCount > 0" @click="markAllRead"
          class="flex-shrink-0 text-xs text-brand">全部已读</button>
      </div>
    </div>

    <!-- Notice List -->
    <div class="mx-auto max-w-2xl px-4 py-4">
      <!-- Skeleton -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-20 animate-pulse rounded-xl bg-white"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredNotices.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-400">
        <svg class="mb-3 h-16 w-16 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <p class="text-sm">暂无通知</p>
      </div>

      <!-- List -->
      <div v-else class="space-y-2.5">
        <div
          v-for="notice in filteredNotices" :key="notice.id"
          class="group relative overflow-hidden rounded-xl bg-white shadow-sm transition-all"
          :class="[
            notice.is_read ? '' : 'ring-1 ring-brand/20',
            selectMode ? 'cursor-pointer' : 'cursor-pointer hover:shadow-md',
            selected.has(notice.id) ? 'ring-2 ring-brand shadow-md' : '',
          ]"
          @click="selectMode ? toggleSelect(notice.id) : handleNoticeClick(notice)"
        >
          <!-- Unread accent bar -->
          <div class="absolute left-0 top-0 h-full w-1 rounded-l-xl transition-colors duration-300"
            :class="notice.is_read ? 'bg-transparent' : 'bg-brand'"></div>

          <div class="flex items-start gap-3 px-4 py-3.5 pl-5">
            <!-- Checkbox (select mode) or Type icon -->
            <div class="flex-shrink-0">
              <Transition name="swap" mode="out-in">
                <div v-if="selectMode" :key="'cb'"
                  class="flex h-10 w-10 items-center justify-center">
                  <span class="flex h-5 w-5 items-center justify-center rounded-full border-2 transition-all"
                    :class="selected.has(notice.id) ? 'border-brand bg-brand' : 'border-gray-300'">
                    <svg v-if="selected.has(notice.id)" class="h-3 w-3 text-white" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6l3 3 5-5" stroke="white" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </span>
                </div>
                <div v-else :key="'ic'"
                  class="flex h-10 w-10 items-center justify-center rounded-full"
                  :class="typeStyle(notice.notice_type).bg">
                  <span class="text-lg">{{ typeStyle(notice.notice_type).icon }}</span>
                </div>
              </Transition>
            </div>

            <!-- Content -->
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <p class="text-sm font-semibold leading-snug"
                  :class="notice.is_read ? 'text-gray-500' : 'text-gray-900'">
                  {{ notice.title }}
                </p>
                <span class="flex-shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                  :class="notice.is_read ? 'bg-gray-100 text-gray-400' : 'bg-brand/10 text-brand'">
                  {{ notice.is_read ? '已读' : '未读' }}
                </span>
              </div>
              <p class="mt-0.5 line-clamp-2 text-xs leading-relaxed"
                :class="notice.is_read ? 'text-gray-400' : 'text-gray-500'">
                {{ notice.content }}
              </p>
              <p class="mt-1.5 flex items-center gap-1.5 text-xs text-gray-400">
                <span>{{ formatTime(notice.created_at) }}</span>
                <span v-if="!selectMode && isNavigable(notice.notice_type)" class="text-sm font-medium text-brand/60">›</span>
                <span v-else-if="!selectMode" class="text-[10px] text-brand/50">{{ expandedId === notice.id ? '△ 收起' : '▽ 展开' }}</span>
              </p>
            </div>

            <!-- Single delete (non-select mode) -->
            <button v-if="!selectMode"
              @click.stop="deleteNotice(notice)"
              class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-gray-300 hover:bg-red-50 hover:text-red-400"
              title="删除">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>

          <!-- Book-expand detail (non-navigable notices only) -->
          <div v-if="!selectMode && !isNavigable(notice.notice_type)" class="book-wrap" :class="{ open: expandedId === notice.id }">
            <div class="book-inner">
              <div class="book-content border-t border-gray-50 px-5 pb-4 pt-3">
                <p class="text-sm leading-relaxed text-gray-700">{{ notice.content }}</p>
                <div class="mt-3 flex items-center justify-between">
                  <span class="text-xs text-gray-400">{{ formatExactTime(notice.created_at) }}</span>
                  <router-link v-if="getNoticeLink(notice.notice_type)" :to="getNoticeLink(notice.notice_type)!"
                    class="rounded-lg bg-brand/10 px-3 py-1.5 text-xs font-semibold text-brand hover:bg-brand/20"
                    @click.stop>
                    {{ getNoticeLinkLabel(notice.notice_type) }} →
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Load more -->
        <div v-if="hasMore" class="py-3 text-center">
          <button @click="loadMore" :disabled="loadingMore" class="text-sm text-brand disabled:opacity-50">
            {{ loadingMore ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, inject } from 'vue'
import { useRouter } from 'vue-router'
import { userNoticeApi } from '@hotelink/api'
import { useConfirm, useToast } from '@hotelink/ui'

const { confirm: confirmDialog } = useConfirm()
const { showToast } = useToast()

interface Notice {
  id: number
  notice_type: string
  title: string
  content: string
  related_order_id?: number | null
  related_order_no?: string | null
  is_read: boolean
  created_at: string
}

const setParentUnreadCount = inject<(n: number) => void>('setUnreadCount')

const notices = ref<Notice[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const unreadCount = ref(0)
const activeType = ref('all')
const expandedId = ref<number | null>(null)
const router = useRouter()
let refreshTimer: number | null = null

// ── Select-mode state ──
const selectMode = ref(false)
const selected = ref<Set<number>>(new Set())

const allSelected = computed(
  () => filteredNotices.value.length > 0 && filteredNotices.value.every(n => selected.value.has(n.id))
)

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  selected.value = new Set()
  expandedId.value = null
}

function exitSelect() {
  selectMode.value = false
  selected.value = new Set()
}

function toggleSelect(id: number) {
  const s = new Set(selected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selected.value = s
}

function toggleSelectAll() {
  if (allSelected.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(filteredNotices.value.map(n => n.id))
  }
}

// ─────────────────────────

function syncParent(n: number) {
  unreadCount.value = n
  setParentUnreadCount?.(n)
}

const typeTabs = [
  { value: 'all', label: '全部' },
  { value: 'order', label: '订单' },
  { value: 'member', label: '会员' },
  { value: 'coupon', label: '优惠券' },
  { value: 'system', label: '系统' },
  { value: 'activity', label: '活动' },
]

function typeStyle(type: string) {
  const map: Record<string, { icon: string; bg: string }> = {
    order: { icon: '📋', bg: 'bg-blue-50' },
    payment: { icon: '💳', bg: 'bg-green-50' },
    member: { icon: '⭐', bg: 'bg-yellow-50' },
    coupon: { icon: '🎫', bg: 'bg-pink-50' },
    activity: { icon: '🎉', bg: 'bg-orange-50' },
    review: { icon: '✍️', bg: 'bg-purple-50' },
    system: { icon: '🔔', bg: 'bg-gray-100' },
  }
  return map[type] ?? { icon: '📢', bg: 'bg-gray-100' }
}

/** 订单/支付/优惠券 → 直接跳转；其余 → 书本展开 */
function isNavigable(type: string): boolean {
  return ['order', 'payment', 'coupon'].includes(type)
}

function getNoticeLink(type: string): string | null {
  const map: Record<string, string> = {
    review: '/my/reviews',
    member: '/my/membership',
  }
  return map[type] ?? null
}

function getNoticeLinkLabel(type: string): string {
  const map: Record<string, string> = {
    review: '查看评价',
    member: '查看会员',
  }
  return map[type] ?? ''
}

function extractOrderNo(text: string): string | null {
  const normalized = String(text || '')
  const patterns = [
    /订单(?:号)?[\s:：#]*([A-Za-z0-9_-]{6,64})/i,
    /\b(HT[A-Za-z0-9_-]{4,})\b/i,
  ]
  for (const pattern of patterns) {
    const matched = normalized.match(pattern)
    const value = matched?.[1]?.trim()
    if (value) return value
  }
  return null
}

function formatExactTime(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function handleNoticeClick(notice: Notice) {
  markRead(notice)
  if (isNavigable(notice.notice_type)) {
    if (notice.notice_type === 'coupon') {
      router.push('/my/coupons')
      return
    }
    if (Number.isFinite(Number(notice.related_order_id)) && Number(notice.related_order_id) > 0) {
      router.push(`/my/orders/${notice.related_order_id}`)
      return
    }
    const keyword = notice.related_order_no || extractOrderNo(`${notice.title} ${notice.content}`)
    if (keyword) {
      router.push({ path: '/my/orders', query: { keyword } })
      return
    }
    router.push('/my/orders')
    return
  }
  expandedId.value = expandedId.value === notice.id ? null : notice.id
}

const filteredNotices = computed(() => {
  if (activeType.value === 'all') return notices.value
  return notices.value.filter(n => n.notice_type === activeType.value)
})

const hasMore = computed(() => page.value * pageSize < total.value)

function formatTime(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}小时前`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD}天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function fetchNotices(reset = false) {
  if (reset) {
    page.value = 1
    notices.value = []
  }
  try {
    const res = await userNoticeApi.list({ page: page.value, page_size: pageSize })
    if (res.code === 0 && res.data) {
      notices.value = reset
        ? (res.data as any).items
        : [...notices.value, ...(res.data as any).items]
      total.value = (res.data as any).total
      const serverCount = (res.data as any).unread_count ?? 0
      syncParent(serverCount)
    } else {
      showToast(res.message || '通知加载失败', 'error')
    }
  } catch {
    showToast('通知加载失败，请检查网络', 'error')
  }
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value) return
  loadingMore.value = true
  page.value++
  await fetchNotices()
  loadingMore.value = false
}

async function markRead(notice: Notice) {
  if (notice.is_read) return
  notice.is_read = true
  try {
    const res = await userNoticeApi.markRead([notice.id])
    if (res.data) syncParent(res.data.unread_count)
  } catch {
    notice.is_read = false
  }
}

async function markAllRead() {
  const prev = notices.value.map(n => n.is_read)
  notices.value.forEach(n => (n.is_read = true))
  try {
    const res = await userNoticeApi.markRead()
    if (res.data) syncParent(res.data.unread_count)
  } catch {
    notices.value.forEach((n, i) => (n.is_read = prev[i]))
    showToast('操作失败，请重试', 'error')
  }
}

async function deleteNotice(notice: Notice) {
  if (!await confirmDialog('确定删除这条通知？')) return
  const backup = [...notices.value]
  const prevTotal = total.value
  notices.value = notices.value.filter(n => n.id !== notice.id)
  total.value = Math.max(0, total.value - 1)
  try {
    const res = await userNoticeApi.deleteNotices([notice.id])
    if (res.data) syncParent(res.data.unread_count)
  } catch {
    notices.value = backup
    total.value = prevTotal
    showToast('删除失败，请重试', 'error')
  }
}

// ── Batch operations ──
async function batchMarkRead() {
  const ids = [...selected.value]
  if (!ids.length) return
  ids.forEach(id => {
    const n = notices.value.find(x => x.id === id)
    if (n) n.is_read = true
  })
  try {
    const res = await userNoticeApi.markRead(ids)
    if (res.data) syncParent(res.data.unread_count)
    selected.value = new Set()
  } catch {
    ids.forEach(id => {
      const n = notices.value.find(x => x.id === id)
      if (n) n.is_read = false
    })
    showToast('操作失败，请重试', 'error')
  }
}

async function batchMarkUnread() {
  const ids = [...selected.value]
  if (!ids.length) return
  ids.forEach(id => {
    const n = notices.value.find(x => x.id === id)
    if (n) n.is_read = false
  })
  try {
    const res = await userNoticeApi.markUnread(ids)
    if (res.data) syncParent(res.data.unread_count)
    selected.value = new Set()
  } catch {
    ids.forEach(id => {
      const n = notices.value.find(x => x.id === id)
      if (n) n.is_read = true
    })
    showToast('操作失败，请重试', 'error')
  }
}

async function batchDelete() {
  const ids = [...selected.value]
  if (!ids.length) return
  if (!await confirmDialog(`确定删除选中的 ${ids.length} 条通知？`, { type: 'danger' })) return
  const backup = [...notices.value]
  const prevTotal = total.value
  notices.value = notices.value.filter(n => !ids.includes(n.id))
  total.value = Math.max(0, total.value - ids.length)
  try {
    const res = await userNoticeApi.deleteNotices(ids)
    if (res.data) syncParent(res.data.unread_count)
    selected.value = new Set()
  } catch {
    notices.value = backup
    total.value = prevTotal
    showToast('删除失败，请重试', 'error')
  }
}

async function deleteAll() {
  if (!await confirmDialog('确定删除所有通知？该操作不可恢复。', { type: 'danger' })) return
  const backup = [...notices.value]
  const prevTotal = total.value
  notices.value = []
  total.value = 0
  selected.value = new Set()
  try {
    const res = await userNoticeApi.deleteNotices()
    if (res.data) syncParent(0)
    selectMode.value = false
  } catch {
    notices.value = backup
    total.value = prevTotal
    showToast('清空失败，请重试', 'error')
  }
}

function refreshNoticeFeedIfVisible() {
  if (!document.hidden) {
    fetchNotices(true)
  }
}

onMounted(async () => {
  await fetchNotices(true)
  loading.value = false
  document.addEventListener('visibilitychange', refreshNoticeFeedIfVisible)
  refreshTimer = window.setInterval(refreshNoticeFeedIfVisible, 60000)
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', refreshNoticeFeedIfVisible)
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.book-wrap {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.book-wrap.open {
  grid-template-rows: 1fr;
}
.book-inner {
  overflow: hidden;
}
.book-content {
  transform: scaleY(0);
  transform-origin: center;
  opacity: 0;
  transition:
    transform 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.3s ease;
}
.book-wrap.open .book-content {
  transform: scaleY(1);
  opacity: 1;
}
.swap-enter-active, .swap-leave-active { transition: opacity 0.15s, transform 0.15s; }
.swap-enter-from { opacity: 0; transform: scale(0.7); }
.swap-leave-to  { opacity: 0; transform: scale(0.7); }
</style>


<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="sticky top-0 z-10 flex items-center justify-between bg-white px-4 py-3 shadow-sm">
      <button @click="$router.back()" class="flex h-8 w-8 items-center justify-center rounded-full hover:bg-gray-100">
        <svg class="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-base font-semibold text-gray-900">
        消息通知
        <span v-if="unreadCount > 0" class="ml-1.5 rounded-full bg-red-500 px-1.5 py-0.5 text-[11px] font-bold text-white">
          {{ unreadCount }}
        </span>
      </h1>
      <div class="flex items-center gap-2">
        <button v-if="unreadCount > 0" @click="markAllRead" class="text-sm text-brand">全部已读</button>
        <span v-else class="w-14"></span>
      </div>
    </div>

    <!-- Type Tabs -->
    <div class="flex gap-0 overflow-x-auto bg-white shadow-sm">
      <button
        v-for="tab in typeTabs"
        :key="tab.value"
        @click="activeType = tab.value"
        class="flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors"
        :class="activeType === tab.value
          ? 'border-b-2 border-brand text-brand'
          : 'text-gray-500 hover:text-gray-700'"
      >
        {{ tab.label }}
      </button>
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
          v-for="notice in filteredNotices"
          :key="notice.id"
          class="group relative overflow-hidden rounded-xl bg-white shadow-sm transition-shadow hover:shadow-md"
          :class="notice.is_read ? '' : 'ring-1 ring-brand/20'"
        >
          <!-- Unread left accent bar -->
          <div
            class="absolute left-0 top-0 h-full w-1 rounded-l-xl transition-colors duration-300"
            :class="notice.is_read ? 'bg-transparent' : 'bg-brand'"
          ></div>

          <div class="flex items-start gap-3 px-4 py-3.5 pl-5">
            <!-- Type icon -->
            <div
              class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full"
              :class="typeStyle(notice.notice_type).bg"
            >
              <span class="text-lg">{{ typeStyle(notice.notice_type).icon }}</span>
            </div>

            <!-- Content (click to mark read) -->
            <div class="min-w-0 flex-1 cursor-pointer" @click="markRead(notice)">
              <div class="flex items-center gap-2">
                <p
                  class="text-sm font-semibold leading-snug"
                  :class="notice.is_read ? 'text-gray-500' : 'text-gray-900'"
                >
                  {{ notice.title }}
                </p>
                <!-- Read / Unread tag -->
                <span
                  class="flex-shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                  :class="notice.is_read
                    ? 'bg-gray-100 text-gray-400'
                    : 'bg-brand/10 text-brand'"
                >
                  {{ notice.is_read ? '已读' : '未读' }}
                </span>
              </div>
              <p
                class="mt-0.5 text-xs leading-relaxed"
                :class="notice.is_read ? 'text-gray-400' : 'text-gray-500'"
              >
                {{ notice.content }}
              </p>
              <p class="mt-1.5 text-xs text-gray-400">{{ formatTime(notice.created_at) }}</p>
            </div>

            <!-- Delete button (visible on hover) -->
            <button
              @click="deleteNotice(notice)"
              class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-gray-300 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-50 hover:text-red-400"
              title="删除通知"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
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
import { ref, computed, onMounted, inject } from 'vue'
import { userNoticeApi } from '@hotelink/api'

interface Notice {
  id: number
  notice_type: string
  title: string
  content: string
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
  const res = await userNoticeApi.list({ page: page.value, page_size: pageSize })
  if (res.data) {
    notices.value = reset
      ? (res.data as any).items
      : [...notices.value, ...(res.data as any).items]
    total.value = (res.data as any).total
    // 从列表接口获取 unread_count 并同步到父级铃铛
    const serverCount = (res.data as any).unread_count ?? 0
    syncParent(serverCount)
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
  const res = await userNoticeApi.markRead([notice.id])
  if (res.data) syncParent(res.data.unread_count)
}

async function markAllRead() {
  notices.value.forEach(n => (n.is_read = true))
  const res = await userNoticeApi.markRead()
  if (res.data) syncParent(res.data.unread_count)
}

async function deleteNotice(notice: Notice) {
  notices.value = notices.value.filter(n => n.id !== notice.id)
  total.value = Math.max(0, total.value - 1)
  const res = await userNoticeApi.deleteNotices([notice.id])
  if (res.data) syncParent(res.data.unread_count)
}

onMounted(async () => {
  await fetchNotices(true)
  loading.value = false
})
</script>


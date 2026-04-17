<template>
  <div class="mx-auto max-w-2xl px-4 py-5">
    <div class="mb-3 rounded-2xl bg-white p-3 shadow-sm ring-1 ring-gray-100">
      <div class="mb-2 flex items-center justify-between">
        <h2 class="text-lg font-bold text-gray-900">我的订单</h2>
        <span class="text-xs text-gray-400">共 {{ total }} 条</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="flex min-w-0 flex-1 items-center rounded-xl border border-gray-200 bg-slate-50 px-3">
          <svg class="mr-2 h-4 w-4 shrink-0 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35m1.85-5.15a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="keyword"
            @keydown.enter="applyFilters"
            placeholder="搜索订单号 / 酒店 / 房型 / 入住人 / 手机号"
            class="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none"
          />
        </div>
        <button
          @click="applyFilters"
          class="shrink-0 rounded-xl bg-brand px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-dark"
        >
          搜索
        </button>
      </div>
    </div>

    <div class="mb-3 rounded-2xl bg-white px-3 py-1.5 shadow-sm ring-1 ring-gray-100">
      <div class="flex items-center gap-2">
        <div class="min-w-0 flex-1">
          <div class="relative grid h-9 grid-cols-4 rounded-xl bg-slate-50 p-1 ring-1 ring-inset ring-gray-200">
            <span
              class="pointer-events-none absolute bottom-1 left-1 top-1 rounded-lg bg-white shadow-sm transition-transform duration-300 ease-out"
              :style="tabSliderStyle"
            />
            <button
              v-for="tab in tabs"
              :key="tab.value"
              @click="switchTab(tab.value)"
              class="relative z-10 h-full rounded-lg px-2 text-[13px] font-medium transition-colors"
              :class="currentTab === tab.value ? 'text-slate-900' : 'text-gray-500'"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div class="relative shrink-0">
          <button
            @click="showAdvanced = !showAdvanced"
            class="relative inline-flex h-9 w-9 items-center justify-center text-brand transition hover:text-brand-dark"
            :class="showAdvanced ? 'text-brand-dark' : ''"
            :title="showAdvanced ? '收起筛选' : '展开筛选'"
            :aria-expanded="showAdvanced"
            aria-label="筛选"
          >
            <svg class="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h18l-7 8v6l-4 2v-8L3 4z" />
            </svg>
            <span v-if="activeAdvancedCount" class="absolute -right-1 -top-1 rounded-full bg-brand px-1 text-[10px] font-medium text-white">
              {{ activeAdvancedCount }}
            </span>
          </button>

          <Transition
            enter-active-class="transform transition duration-180 ease-out"
            enter-from-class="-translate-y-1.5 scale-95 opacity-0"
            enter-to-class="translate-y-0 scale-100 opacity-100"
            leave-active-class="transform transition duration-120 ease-in"
            leave-from-class="translate-y-0 scale-100 opacity-100"
            leave-to-class="-translate-y-1.5 scale-95 opacity-0"
          >
            <div
              v-if="showAdvanced"
              class="absolute right-0 top-[calc(100%+0.45rem)] z-30 w-72 max-h-[65vh] max-w-[calc(100vw-2rem)] overflow-y-auto rounded-2xl border border-gray-200 bg-white p-3 shadow-xl ring-1 ring-slate-100"
            >
              <span class="pointer-events-none absolute -top-1.5 right-3 h-3 w-3 rotate-45 border-l border-t border-gray-200 bg-white" />

              <div class="grid grid-cols-1 gap-2.5">
                <label class="text-xs text-gray-500">
                  支付状态
                  <select
                    v-model="paymentStatus"
                    class="mt-1 w-full rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-brand"
                  >
                    <option v-for="item in paymentStatusOptions" :key="item.value || 'all-payment'" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                </label>

                <div class="grid grid-cols-2 gap-2">
                  <label class="text-xs text-gray-500">
                    入住开始
                    <input
                      v-model="checkInStart"
                      type="date"
                      class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-brand"
                    />
                  </label>
                  <label class="text-xs text-gray-500">
                    入住结束
                    <input
                      v-model="checkInEnd"
                      type="date"
                      class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-brand"
                    />
                  </label>
                </div>

                <div class="grid grid-cols-2 gap-2">
                  <label class="text-xs text-gray-500">
                    下单开始
                    <input
                      v-model="createdStart"
                      type="date"
                      class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-brand"
                    />
                  </label>
                  <label class="text-xs text-gray-500">
                    下单结束
                    <input
                      v-model="createdEnd"
                      type="date"
                      class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-brand"
                    />
                  </label>
                </div>

                <div class="grid grid-cols-2 gap-2">
                  <label class="text-xs text-gray-500">
                    最低金额
                    <input
                      v-model="amountMin"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0"
                      class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-brand"
                    />
                  </label>
                  <label class="text-xs text-gray-500">
                    最高金额
                    <input
                      v-model="amountMax"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="不限"
                      class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-brand"
                    />
                  </label>
                </div>
              </div>

              <div class="mt-3 flex justify-end gap-2">
                <button
                  @click="resetFilters"
                  class="rounded-lg border border-gray-200 px-3 py-1 text-xs text-gray-600 transition hover:bg-gray-50"
                >
                  清空
                </button>
                <button
                  @click="applyFilters"
                  class="rounded-lg border border-brand/30 bg-brand/5 px-3 py-1 text-xs font-medium text-brand transition hover:bg-brand/10"
                >
                  应用
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <div class="relative" @touchstart.passive="onContentTouchStart" @touchend.passive="onContentTouchEnd">
      <Transition :name="contentTransitionName" mode="out-in">
        <div :key="contentTransitionKey">
          <div v-if="loading" class="space-y-3">
            <div v-for="i in 3" :key="i" class="h-32 animate-pulse rounded-2xl bg-gray-200" />
          </div>

          <div v-else-if="orders.length === 0" class="rounded-2xl bg-white px-4 py-10 text-center shadow-sm ring-1 ring-gray-100">
            <p class="text-sm text-gray-400">暂无符合条件的订单</p>
            <button
              v-if="hasAnyFilters"
              @click="resetFilters"
              class="mt-4 rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-500 transition hover:bg-gray-50"
            >
              清空筛选条件
            </button>
          </div>

          <div v-else class="space-y-3">
            <article
              v-for="order in orders"
              :key="order.id"
              class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100"
            >
              <div class="mb-3 flex items-start justify-between gap-3">
                <router-link :to="`/my/orders/${order.id}`" class="min-w-0 flex-1">
                  <h4 class="truncate text-base font-semibold text-gray-800">{{ order.hotel_name || '酒店' }}</h4>
                  <p class="mt-0.5 truncate text-xs text-gray-400">{{ order.room_type_name || '房型' }}</p>
                </router-link>
                <div class="flex flex-col items-end gap-1">
                  <span class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium" :class="statusBadge(order.status)">
                    {{ statusLabel(order.status) }}
                  </span>
                  <span
                    v-if="order.status === 'completed' && !order.has_review"
                    class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700"
                  >
                    待评价
                  </span>
                </div>
              </div>

              <div class="mb-3 rounded-xl bg-slate-50 px-3 py-2">
                <p class="text-sm font-medium text-slate-700">{{ orderProgressText(order) }}</p>
                <p class="mt-1 text-xs text-slate-400">更新时间：{{ formatDateTime(order.updated_at || order.created_at) }}</p>
              </div>

              <div v-if="getRecentChangeText(order)" class="mb-3 rounded-xl border px-3 py-2"
                :class="getRecentChangeTag(order) === '回滚/纠正' ? 'border-amber-200 bg-amber-50/70' : getRecentChangeTag(order) === '异常' ? 'border-rose-200 bg-rose-50/70' : 'border-cyan-200 bg-cyan-50/70'">
                <div class="flex items-center justify-between gap-2">
                  <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                    :class="getRecentChangeTag(order) === '回滚/纠正' ? 'bg-amber-100 text-amber-700' : getRecentChangeTag(order) === '异常' ? 'bg-rose-100 text-rose-700' : 'bg-cyan-100 text-cyan-700'">
                    {{ getRecentChangeTag(order) }}
                  </span>
                  <span class="text-[11px] text-gray-400">近期变更</span>
                </div>
                <p class="mt-1 text-xs leading-5 text-slate-700">{{ getRecentChangeText(order) }}</p>
              </div>

              <router-link :to="`/my/orders/${order.id}`" class="mb-3 flex items-center gap-3">
                <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-xl">🏨</div>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-gray-800">{{ order.room_type_name || '房型' }}</p>
                  <p class="mt-0.5 text-xs text-gray-500">{{ order.check_in_date }} — {{ order.check_out_date }}</p>
                  <p class="mt-1 text-xs text-gray-400">入住人：{{ order.guest_name || '-' }} · {{ maskMobile(order.guest_mobile) }}</p>
                </div>
                <div class="text-right">
                  <p class="text-lg font-bold text-orange-600">¥{{ formatMoney(order.pay_amount || order.total_amount || order.original_amount || 0) }}</p>
                  <p class="text-xs text-gray-400">{{ paymentStatusLabel(order.payment_status) }}</p>
                </div>
              </router-link>

              <div class="flex items-center justify-between border-t border-gray-100 pt-3">
                <p class="truncate pr-2 text-xs text-gray-400">订单号：{{ order.order_no }}</p>
                <div class="flex shrink-0 gap-2">
                  <router-link
                    :to="`/my/orders/${order.id}`"
                    class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-600 transition hover:bg-gray-50"
                  >
                    详情
                  </router-link>
                  <router-link
                    v-if="order.status === 'pending_payment'"
                    :to="`/payment/${order.id}`"
                    class="rounded-lg bg-brand px-3 py-1.5 text-xs font-medium text-white transition hover:bg-brand-dark"
                  >
                    去支付
                  </router-link>
                  <router-link
                    v-else-if="order.status === 'completed' && !order.has_review"
                    :to="`/my/orders/${order.id}`"
                    class="rounded-lg border border-brand/30 bg-brand/5 px-3 py-1.5 text-xs font-medium text-brand transition hover:bg-brand/10"
                  >
                    去评价
                  </router-link>
                  <router-link
                    v-else-if="getHotelPath(order)"
                    :to="getHotelPath(order)"
                    class="rounded-lg border border-brand/30 bg-brand/5 px-3 py-1.5 text-xs font-medium text-brand transition hover:bg-brand/10"
                  >
                    再次预订
                  </router-link>
                </div>
              </div>
            </article>
          </div>

          <!-- Pagination -->
          <div v-if="!loading && total > pageSize" class="mt-6 flex justify-center gap-2">
            <button :disabled="page <= 1" @click="page--; fetchOrders(true)" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">上一页</button>
            <span class="flex items-center px-3 text-sm text-gray-500">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
            <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchOrders(true)" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">下一页</button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi } from '@hotelink/api'
import { ORDER_STATUS_MAP, PAYMENT_STATUS_MAP, formatMoney } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const orders = ref<any[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const currentTab = ref('')
const keyword = ref('')
const paymentStatus = ref('')
const checkInStart = ref('')
const checkInEnd = ref('')
const createdStart = ref('')
const createdEnd = ref('')
const amountMin = ref('')
const amountMax = ref('')
const showAdvanced = ref(false)
type SlideDirection = 'left' | 'right'
const contentSlideDirection = ref<SlideDirection>('left')
const contentSlideTick = ref(0)
const touchStartX = ref<number | null>(null)
const touchStartY = ref<number | null>(null)
const touchStartAt = ref(0)
let refreshTimer: number | null = null

const tabs = [
  { value: '', label: '全部' },
  { value: 'pending_payment', label: '待支付' },
  { value: 'confirmed', label: '待入住' },
  { value: 'completed', label: '已完成' },
]

const paymentStatusOptions = [
  { value: '', label: '全部支付' },
  { value: 'unpaid', label: '未支付' },
  { value: 'paid', label: '已支付' },
  { value: 'failed', label: '支付失败' },
  { value: 'refunded', label: '已退款' },
]

const currentTabIndex = computed(() => {
  const index = tabs.findIndex(item => item.value === currentTab.value)
  return index >= 0 ? index : 0
})

const tabSliderStyle = computed(() => ({
  width: `calc((100% - 0.5rem) / ${tabs.length})`,
  transform: `translateX(${currentTabIndex.value * 100}%)`,
}))

const contentTransitionName = computed(() => (
  contentSlideDirection.value === 'left' ? 'orders-slide-left' : 'orders-slide-right'
))

const contentTransitionKey = computed(() => `${currentTab.value || 'all'}-${contentSlideTick.value}`)

// 根据状态值返回对应展示信息。
function statusLabel(s: string): string { return ORDER_STATUS_MAP[s]?.label || s }
function statusBadge(s: string): string {
  if (s === 'completed') return 'bg-emerald-50 text-emerald-700'
  if (s === 'checked_in') return 'bg-cyan-50 text-cyan-700'
  if (s === 'pending_payment') return 'bg-amber-50 text-amber-700'
  if (s === 'cancelled') return 'bg-gray-100 text-gray-500'
  if (s === 'confirmed') return 'bg-indigo-50 text-indigo-700'
  return 'bg-slate-100 text-slate-600'
}

function paymentStatusLabel(status: string): string {
  return PAYMENT_STATUS_MAP[status] || '支付状态未知'
}

function maskMobile(mobile?: string): string {
  const value = String(mobile || '')
  if (!value) return '-'
  if (value.length < 7) return value
  return `${value.slice(0, 3)}****${value.slice(-4)}`
}

function formatDateTime(value?: string): string {
  if (!value) return '-'
  const dt = new Date(value)
  if (Number.isNaN(dt.getTime())) {
    return String(value).replace('T', ' ').slice(0, 16)
  }
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const dd = String(dt.getDate()).padStart(2, '0')
  const hh = String(dt.getHours()).padStart(2, '0')
  const mi = String(dt.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

function orderProgressText(order: any): string {
  switch (order?.status) {
    case 'pending_payment':
      return '订单待支付，请尽快完成支付以保留房间'
    case 'confirmed':
      return '酒店已确认，等待办理入住'
    case 'checked_in':
      return '您已入住，祝您旅途愉快'
    case 'completed':
      return order?.has_review ? '订单已完成，感谢您的入住' : '订单已完成，欢迎评价本次入住'
    case 'cancelled':
      return '订单已取消'
    default:
      return '订单处理中'
  }
}

function splitRemarkSegments(raw: string): string[] {
  return String(raw || '')
    .split(/[；;\n]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function classifyChangeTag(text: string): string {
  const normalized = String(text || '').toLowerCase()
  if (normalized.includes('回滚') || normalized.includes('撤销') || normalized.includes('纠正') || normalized.includes('回退')) {
    return '回滚/纠正'
  }
  if (normalized.includes('异常')) {
    return '异常'
  }
  if (normalized.includes('续住')) {
    return '续住'
  }
  if (normalized.includes('换房')) {
    return '换房'
  }
  if (normalized.includes('入住')) {
    return '入住'
  }
  if (normalized.includes('退房')) {
    return '退房'
  }
  return '变更'
}

function getRecentChangeText(order: any): string {
  const warning = String(order?.lifecycle_warning || '').trim()
  if (warning) return warning

  const segments = splitRemarkSegments(String(order?.operator_remark || ''))
  if (!segments.length) return ''
  return segments[segments.length - 1]
}

function getRecentChangeTag(order: any): string {
  const text = getRecentChangeText(order)
  if (!text) return ''
  return classifyChangeTag(text)
}

function getHotelPath(order: any): string {
  const hotelId = Number(order?.hotel_id || order?.hotel || 0)
  if (!Number.isFinite(hotelId) || hotelId <= 0) return ''
  return `/hotels/${hotelId}`
}

const activeAdvancedCount = computed(() => {
  const extraCount = [checkInStart.value, checkInEnd.value, createdStart.value, createdEnd.value, amountMin.value, amountMax.value]
    .filter(v => String(v || '').trim()).length
  return extraCount + (paymentStatus.value ? 1 : 0)
})

const hasAdvancedFilters = computed(() => Boolean(activeAdvancedCount.value))

const hasAnyFilters = computed(() => Boolean(
  currentTab.value ||
  keyword.value.trim() ||
  paymentStatus.value ||
  hasAdvancedFilters.value
))

function readQueryValue(key: string): string {
  const value = route.query[key]
  return typeof value === 'string' ? value : ''
}

function hydrateFromQuery() {
  const queryStatus = readQueryValue('status')
  currentTab.value = tabs.some(item => item.value === queryStatus) ? queryStatus : ''
  keyword.value = readQueryValue('keyword')
  paymentStatus.value = readQueryValue('payment_status')
  checkInStart.value = readQueryValue('check_in_start')
  checkInEnd.value = readQueryValue('check_in_end')
  createdStart.value = readQueryValue('created_start')
  createdEnd.value = readQueryValue('created_end')
  amountMin.value = readQueryValue('amount_min')
  amountMax.value = readQueryValue('amount_max')

  const parsedPage = Number(readQueryValue('page') || '1')
  page.value = Number.isFinite(parsedPage) && parsedPage > 0 ? Math.floor(parsedPage) : 1

  showAdvanced.value = false
}

function buildOrderQueryParams(includePage = true): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (includePage) params.page = page.value
  if (currentTab.value) params.status = currentTab.value
  if (keyword.value.trim()) params.keyword = keyword.value.trim()
  if (paymentStatus.value) params.payment_status = paymentStatus.value
  if (checkInStart.value) params.check_in_start = checkInStart.value
  if (checkInEnd.value) params.check_in_end = checkInEnd.value
  if (createdStart.value) params.created_start = createdStart.value
  if (createdEnd.value) params.created_end = createdEnd.value
  if (amountMin.value) params.amount_min = amountMin.value
  if (amountMax.value) params.amount_max = amountMax.value
  return params
}

async function syncRouteQuery() {
  const query = buildOrderQueryParams(true)
  await router.replace({ path: '/my/orders', query })
}

// 加载 fetchOrders 相关数据。
async function fetchOrders(syncQuery = false) {
  loading.value = true
  try {
    if (syncQuery) {
      await syncRouteQuery()
    }
    const params: Record<string, unknown> = { ...buildOrderQueryParams(true), page_size: pageSize }
    const res = await userOrderApi.list(params)
    if (res.code === 0 && res.data) {
      orders.value = (res.data as any).items || []
      total.value = (res.data as any).total || 0
    }
  } catch {
    orders.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function refreshOrdersIfVisible() {
  if (!document.hidden) {
    fetchOrders(false)
  }
}

function switchTab(status: string, direction?: SlideDirection) {
  const nextIndex = tabs.findIndex(item => item.value === status)
  if (nextIndex < 0) return
  const fromIndex = currentTabIndex.value
  if (nextIndex === fromIndex) return

  contentSlideDirection.value = direction || (nextIndex > fromIndex ? 'left' : 'right')
  contentSlideTick.value += 1
  currentTab.value = status
  page.value = 1
  fetchOrders(true)
}

function switchTabByOffset(offset: number) {
  const currentIndex = currentTabIndex.value
  const nextIndex = currentIndex + offset
  if (nextIndex < 0 || nextIndex >= tabs.length) return
  switchTab(tabs[nextIndex].value, offset > 0 ? 'left' : 'right')
}

function resetTouchTracking() {
  touchStartX.value = null
  touchStartY.value = null
  touchStartAt.value = 0
}

function onContentTouchStart(event: TouchEvent) {
  if (event.touches.length !== 1) {
    resetTouchTracking()
    return
  }
  const target = event.target as HTMLElement | null
  if (target?.closest('input,select,textarea')) {
    resetTouchTracking()
    return
  }
  const touch = event.touches[0]
  touchStartX.value = touch.clientX
  touchStartY.value = touch.clientY
  touchStartAt.value = Date.now()
}

function onContentTouchEnd(event: TouchEvent) {
  if (touchStartX.value === null || touchStartY.value === null || touchStartAt.value <= 0) return
  if (event.changedTouches.length !== 1) {
    resetTouchTracking()
    return
  }

  const touch = event.changedTouches[0]
  const deltaX = touch.clientX - touchStartX.value
  const deltaY = touch.clientY - touchStartY.value
  const elapsed = Date.now() - touchStartAt.value
  resetTouchTracking()

  if (elapsed > 900) return
  if (Math.abs(deltaX) < 45) return
  if (Math.abs(deltaX) < Math.abs(deltaY) * 1.2) return

  if (deltaX < 0) {
    switchTabByOffset(1)
    return
  }
  switchTabByOffset(-1)
}

function applyFilters() {
  showAdvanced.value = false
  page.value = 1
  fetchOrders(true)
}

function resetFilters() {
  currentTab.value = ''
  keyword.value = ''
  paymentStatus.value = ''
  checkInStart.value = ''
  checkInEnd.value = ''
  createdStart.value = ''
  createdEnd.value = ''
  amountMin.value = ''
  amountMax.value = ''
  showAdvanced.value = false
  page.value = 1
  fetchOrders(true)
}

onMounted(async () => {
  hydrateFromQuery()
  await fetchOrders(false)
  window.addEventListener('focus', refreshOrdersIfVisible)
  document.addEventListener('visibilitychange', refreshOrdersIfVisible)
  refreshTimer = window.setInterval(refreshOrdersIfVisible, 60000)
})

onBeforeUnmount(() => {
  window.removeEventListener('focus', refreshOrdersIfVisible)
  document.removeEventListener('visibilitychange', refreshOrdersIfVisible)
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.orders-slide-left-enter-active,
.orders-slide-left-leave-active,
.orders-slide-right-enter-active,
.orders-slide-right-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.orders-slide-left-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.orders-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.orders-slide-right-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.orders-slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>

<template>
  <div class="mx-auto max-w-5xl px-4 py-6">
    <p v-if="error" class="mb-4 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

    <!-- Search & Filter bar -->
    <div class="mb-6 rounded-3xl bg-white p-4 shadow-sm ring-1 ring-gray-100 md:p-5">
      <div class="mb-3 grid grid-cols-4 gap-1 rounded-2xl bg-slate-100 p-1 text-sm font-semibold text-gray-500">
        <button
          v-for="item in stayTypes"
          :key="item.value"
          type="button"
          @click="switchStayType(item.value)"
          class="rounded-xl px-2 py-1.5 transition"
          :class="activeStayType === item.value ? 'bg-brand/10 text-brand ring-1 ring-brand/20' : 'text-gray-500 hover:bg-white/70'"
        >
          {{ item.label }}
        </button>
        <button
          type="button"
          @click="toggleViewMode"
          class="inline-flex items-center justify-center gap-1 rounded-xl bg-white px-2 py-1.5 text-xs font-semibold text-gray-600 ring-1 ring-gray-200 transition hover:bg-gray-50"
          :title="viewMode === 'single' ? '当前单列，点击切换双列' : '当前双列，点击切换单列'"
        >
          <svg v-if="viewMode === 'single'" class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          <svg v-else class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z" />
          </svg>
          <span>{{ viewMode === 'single' ? '单列' : '双列' }}</span>
        </button>
      </div>

      <div class="divide-y divide-gray-100">
        <div class="flex items-center gap-2 px-1 py-3">
          <svg class="h-4 w-4 shrink-0 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 12.414m0 0A5 5 0 1116 9a5 5 0 01-2.586 3.414z" />
          </svg>
          <input
            v-model="filters.keyword"
            type="text"
            placeholder="位置/品牌/酒店名"
            class="min-w-0 flex-1 bg-transparent text-sm outline-none"
            @keyup.enter="onSearch"
          />
        </div>

        <div class="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] items-center gap-2 px-1 py-3">
          <label class="text-xs text-gray-500">
            入住
            <input v-model="filters.check_in_date" type="date" :min="today" class="mt-1 w-full bg-transparent text-sm text-gray-800 outline-none" />
          </label>
          <label class="text-xs text-gray-500">
            离店
            <input v-model="filters.check_out_date" type="date" :min="filters.check_in_date || today" class="mt-1 w-full bg-transparent text-sm text-gray-800 outline-none" />
          </label>
          <span class="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-gray-600">共 {{ stayNights }} 晚</span>
        </div>

        <div class="relative grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] items-center gap-2 px-1 py-3">
          <SelectField v-model="filters.star" size="sm" class="w-full">
            <option value="">全部星级</option>
            <option v-for="s in [5,4,3,2]" :key="s" :value="s">{{ s }}星</option>
          </SelectField>
          <SelectField v-model="filters.sort" size="sm" class="w-full">
            <option value="default">默认排序</option>
            <option value="price_asc">价格低→高</option>
            <option value="price_desc">价格高→低</option>
            <option value="rating_desc">评分优先</option>
            <option value="popular_desc">人气优先</option>
          </SelectField>

          <button
            type="button"
            @click="showMoreFilters = !showMoreFilters"
            class="relative inline-flex h-[34px] w-[34px] shrink-0 items-center justify-center text-brand transition hover:text-brand-dark"
            :class="showMoreFilters ? 'text-brand-dark' : ''"
            :title="showMoreFilters ? '收起更多筛选' : '展开更多筛选'"
            :aria-expanded="showMoreFilters"
            aria-label="更多筛选"
          >
            <svg class="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h18l-7 8v6l-4 2v-8L3 4z" />
            </svg>
            <span v-if="hasMoreFilters" class="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-brand" />
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
              v-if="showMoreFilters"
              class="absolute right-0 top-[calc(100%+0.45rem)] z-20 w-64 rounded-2xl border border-gray-200 bg-white p-3 shadow-xl ring-1 ring-slate-100"
            >
              <span class="pointer-events-none absolute -top-1.5 right-3 h-3 w-3 rotate-45 border-l border-t border-gray-200 bg-white" />

              <p class="mb-2 text-xs font-medium text-gray-500">更多筛选</p>
              <div class="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
                <input
                  v-model.number="filters.min_price"
                  type="number"
                  placeholder="最低价"
                  class="w-full rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs outline-none focus:border-brand"
                />
                <span class="text-center text-gray-300">—</span>
                <input
                  v-model.number="filters.max_price"
                  type="number"
                  placeholder="最高价"
                  class="w-full rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs outline-none focus:border-brand"
                />
              </div>

              <div class="mt-3 flex justify-end gap-2">
                <button
                  type="button"
                  @click="clearPriceRange"
                  class="rounded-lg border border-gray-200 px-3 py-1 text-xs text-gray-600 transition hover:bg-gray-50"
                >
                  清空
                </button>
                <button
                  type="button"
                  @click="showMoreFilters = false"
                  class="rounded-lg border border-brand/30 bg-brand/5 px-3 py-1 text-xs font-medium text-brand transition hover:bg-brand/10"
                >
                  完成
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <button
        type="button"
        @click="onSearch"
        class="mt-4 w-full rounded-2xl bg-gradient-to-r from-brand to-brand-dark px-6 py-3 text-base font-semibold text-white transition hover:brightness-105"
      >
        找酒店
      </button>
    </div>

    <!-- Results -->
    <div class="relative">
      <Transition :name="resultTransitionName" mode="out-in">
        <div :key="resultTransitionKey">
          <div v-if="loading" class="space-y-4">
            <div v-for="i in 4" :key="i" class="h-36 animate-pulse rounded-2xl bg-gray-200" />
          </div>

          <div v-else-if="hotels.length === 0" class="py-20 text-center text-gray-400">
            <p class="text-4xl">🔍</p>
            <p class="mt-3 text-sm">暂未找到符合条件的酒店</p>
          </div>

          <div v-else :class="viewMode === 'single' ? 'space-y-4' : 'grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4'">
            <article
              v-for="hotel in hotels"
              :key="`${viewMode}-${hotel.id}`"
              :class="viewMode === 'single'
                ? 'group flex cursor-pointer overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 transition hover:shadow-md'
                : 'group cursor-pointer overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 transition hover:shadow-md'"
              tabindex="0"
              @click="goHotelDetail(hotel.id)"
              @keydown.enter.prevent="goHotelDetail(hotel.id)"
            >
              <template v-if="viewMode === 'single'">
                <div class="aspect-[4/3] w-28 shrink-0 overflow-hidden bg-gray-200 sm:w-36 md:w-40">
                  <img v-if="hotel.image_url" :src="hotel.image_thumb || hotel.image_url" :alt="hotel.name" class="h-full w-full object-cover transition group-hover:scale-105" loading="lazy" decoding="async" />
                  <div v-else class="flex h-full items-center justify-center text-3xl text-gray-300">🏨</div>
                </div>
                <div class="flex flex-1 flex-col justify-between p-4">
                  <div>
                    <div class="flex items-start justify-between">
                      <h3 class="font-semibold text-gray-900 line-clamp-1">{{ hotel.name }}</h3>
                      <span class="ml-2 shrink-0 text-xs text-yellow-500">{{ '★'.repeat(hotel.star || 0) }}</span>
                    </div>
                    <p class="mt-1 text-xs text-gray-400">📍 {{ hotel.city }} · {{ hotel.address }}</p>
                    <div v-if="hotel.tags?.length" class="mt-2 flex flex-wrap gap-1">
                      <span v-for="tag in hotel.tags.slice(0, 4)" :key="tag" class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">{{ tag }}</span>
                    </div>
                  </div>
                  <div class="mt-2 flex items-center justify-between gap-2">
                    <div class="flex min-w-0 items-center gap-2">
                      <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
                      <span class="whitespace-nowrap text-xs text-gray-400">{{ hotel.review_count || 0 }}条评价</span>
                    </div>
                    <button
                      @click.stop.prevent="goHotelCompare(hotel.id)"
                      class="shrink-0 rounded-md border border-brand/25 bg-brand/5 px-2 py-0.5 text-xs font-medium text-brand transition hover:bg-brand/10"
                    >AI对比</button>
                  </div>
                  <div class="mt-2 text-right">
                    <span class="text-lg font-bold text-orange-600">¥{{ hotel.min_price }}</span>
                    <span class="ml-0.5 text-xs text-gray-400">/晚起</span>
                  </div>
                </div>
              </template>

              <template v-else>
                <div class="relative h-28 w-full overflow-hidden bg-gray-200">
                  <img v-if="hotel.image_url" :src="hotel.image_thumb || hotel.image_url" :alt="hotel.name" class="h-full w-full object-cover transition group-hover:scale-105" loading="lazy" decoding="async" />
                  <div v-else class="flex h-full items-center justify-center text-3xl text-gray-300">🏨</div>
                  <div class="absolute right-2 top-2 inline-flex items-center gap-1 rounded-full bg-white/90 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600 shadow-sm">
                    <svg class="h-3 w-3 text-amber-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.08 3.324a1 1 0 00.95.69h3.496c.969 0 1.371 1.24.588 1.81l-2.829 2.055a1 1 0 00-.364 1.118l1.08 3.323c.3.922-.755 1.688-1.54 1.118l-2.83-2.055a1 1 0 00-1.175 0l-2.83 2.055c-.783.57-1.838-.196-1.539-1.118l1.08-3.323a1 1 0 00-.364-1.118L2.935 8.75c-.783-.57-.38-1.81.588-1.81H7.02a1 1 0 00.95-.69l1.08-3.324z" />
                    </svg>
                    <span>{{ hotel.star || 0 }}</span>
                  </div>
                </div>
                <div class="p-3">
                  <h3 class="line-clamp-1 text-sm font-semibold text-gray-900">{{ hotel.name }}</h3>
                  <p class="mt-1 line-clamp-1 text-[11px] text-gray-400">{{ hotel.city }} · {{ hotel.address }}</p>
                  <div class="mt-2 flex items-center gap-1.5 text-[11px] text-gray-500">
                    <span class="rounded bg-brand/10 px-1.5 py-0.5 font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
                    <span>{{ hotel.review_count || 0 }}条评价</span>
                  </div>
                  <div class="mt-2 flex items-center justify-between">
                    <span class="text-base font-bold text-orange-600">¥{{ hotel.min_price }}</span>
                    <button
                      @click.stop.prevent="goHotelCompare(hotel.id)"
                      class="rounded-md border border-brand/25 bg-brand/5 px-2 py-0.5 text-[11px] font-medium text-brand transition hover:bg-brand/10"
                    >
                      AI对比
                    </button>
                  </div>
                </div>
              </template>
            </article>
          </div>
        </div>
      </Transition>
    </div>

    <div v-if="!loading && hotels.length > 0" class="mt-4">
      <div v-if="loadFailed" class="py-4 text-center">
        <button @click="loadFailed = false; loadMore()" class="text-sm text-brand hover:underline">加载失败，点击重试</button>
      </div>
      <div v-else-if="hasMore" class="flex justify-center py-2 text-xs text-gray-400">
        {{ loadingMore ? '正在加载更多酒店...' : '向下滑动加载更多' }}
      </div>
      <div v-else class="flex justify-center py-2 text-xs text-gray-300">已经到底了</div>
      <div ref="loadMoreAnchor" class="h-1 w-full" />
    </div>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="translate-y-2 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-2 opacity-0"
    >
      <button
        v-if="showBackTop"
        type="button"
        @click="scrollToTop"
        class="fixed bottom-20 right-4 z-40 inline-flex h-10 w-10 items-center justify-center rounded-full bg-white text-brand shadow-lg ring-1 ring-brand/20 transition hover:bg-brand/5"
        title="返回顶部"
        aria-label="返回顶部"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
        </svg>
      </button>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicApi } from '@hotelink/api'
import { SelectField } from '@hotelink/ui'
import { buildImageThumbUrl } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const loadingMore = ref(false)
const loadFailed = ref(false)
const hotels = ref<any[]>([])
const error = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const showBackTop = ref(false)
const loadMoreAnchor = ref<HTMLElement | null>(null)
let loadMoreObserver: IntersectionObserver | null = null
type StayType = 'hotel' | 'homestay' | 'short_rent'
type ViewMode = 'single' | 'double'
type SlideDirection = 'left' | 'right'
const activeStayType = ref<StayType>('hotel')
const viewMode = ref<ViewMode>('single')
const showMoreFilters = ref(false)
const resultSlideDirection = ref<SlideDirection>('left')

const stayTypes: Array<{ value: StayType; label: string }> = [
  { value: 'hotel', label: '酒店' },
  { value: 'homestay', label: '民宿' },
  { value: 'short_rent', label: '短租' },
]

function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function addDays(base: string, days: number): string {
  const date = new Date(base)
  date.setDate(date.getDate() + days)
  return formatDate(date)
}

const today = formatDate(new Date())
const tomorrow = addDays(today, 1)

function resolveDateRangeFromRoute() {
  const incomingCheckIn = (route.query.check_in_date as string) || ''
  const incomingCheckOut = (route.query.check_out_date as string) || ''

  const normalizedCheckIn = incomingCheckIn || today
  let normalizedCheckOut = incomingCheckOut || addDays(normalizedCheckIn, 1)
  if (normalizedCheckOut <= normalizedCheckIn) {
    normalizedCheckOut = addDays(normalizedCheckIn, 1)
  }

  return {
    check_in_date: normalizedCheckIn,
    check_out_date: normalizedCheckOut,
  }
}

const initialDates = resolveDateRangeFromRoute()

const filters = reactive({
  keyword: (route.query.keyword as string) || '',
  check_in_date: initialDates.check_in_date,
  check_out_date: initialDates.check_out_date,
  star: (route.query.star as string) || '',
  sort: (route.query.sort as string) || 'default',
  min_price: route.query.min_price ? Number(route.query.min_price) : undefined as number | undefined,
  max_price: route.query.max_price ? Number(route.query.max_price) : undefined as number | undefined,
})

const stayNights = computed(() => {
  const start = new Date(filters.check_in_date)
  const end = new Date(filters.check_out_date)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 1
  const diff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 1
})

const hasMoreFilters = computed(() => (
  filters.min_price !== undefined || filters.max_price !== undefined
))

const hasMore = computed(() => hotels.value.length < total.value)

const resultTransitionName = computed(() => (
  resultSlideDirection.value === 'left' ? 'hotel-result-left' : 'hotel-result-right'
))

const resultTransitionKey = computed(() => `${viewMode.value}-${activeStayType.value}`)

// 加载 fetchList 相关数据。
function formatRating(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(1) : '暂无'
}

function mapHotel(item: any) {
  const image = item?.image_url || item?.cover_image || ''
  return {
    ...item,
    image_url: image,
    image_thumb: buildImageThumbUrl(image, 352, 288) || item?.cover_thumb || image,
  }
}

async function fetchList(options: { append?: boolean } = {}) {
  const append = Boolean(options.append)
  if (append) {
    if (loading.value || loadingMore.value || !hasMore.value) return
    loadingMore.value = true
  } else {
    loading.value = true
    error.value = ''
  }
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (activeStayType.value !== 'hotel') params.type = activeStayType.value
    if (filters.check_in_date) params.check_in_date = filters.check_in_date
    if (filters.check_out_date) params.check_out_date = filters.check_out_date
    if (filters.star) params.star = filters.star
    if (filters.sort !== 'default') params.sort = filters.sort
    if (filters.min_price) params.min_price = filters.min_price
    if (filters.max_price) params.max_price = filters.max_price
    const res = await publicApi.hotels(params)
    if (res.code === 0 && res.data) {
      const items = ((res.data as any).items || []).map(mapHotel)
      hotels.value = append ? [...hotels.value, ...items] : items
      total.value = (res.data as any).total || 0
    } else {
      if (!append) {
        hotels.value = []
        total.value = 0
      } else {
        page.value = Math.max(1, page.value - 1)
      }
      error.value = res.message || '酒店列表加载失败'
    }
  } catch {
    if (!append) {
      hotels.value = []
      total.value = 0
    } else {
      page.value = Math.max(1, page.value - 1)
      loadFailed.value = true
    }
    error.value = '酒店列表加载失败，请稍后重试'
  } finally {
    if (append) {
      loadingMore.value = false
    } else {
      loading.value = false
    }
  }
}

async function loadMore() {
  if (!hasMore.value || loading.value || loadingMore.value) return
  loadFailed.value = false
  page.value += 1
  await fetchList({ append: true })
}

function setupLoadMoreObserver() {
  if (typeof window === 'undefined' || !('IntersectionObserver' in window) || !loadMoreAnchor.value) return
  if (loadMoreObserver) {
    loadMoreObserver.disconnect()
  }
  loadMoreObserver = new IntersectionObserver(
    (entries) => {
      if (entries.some(entry => entry.isIntersecting)) {
        void loadMore()
      }
    },
    { root: null, rootMargin: '260px 0px', threshold: 0 }
  )
  loadMoreObserver.observe(loadMoreAnchor.value)
}

function handleWindowScroll() {
  if (typeof window === 'undefined') return
  showBackTop.value = window.scrollY > 480
}

function scrollToTop() {
  if (typeof window === 'undefined') return
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function syncFiltersFromRoute() {
  const normalizedDates = resolveDateRangeFromRoute()
  filters.keyword = (route.query.keyword as string) || ''
  filters.check_in_date = normalizedDates.check_in_date
  filters.check_out_date = normalizedDates.check_out_date
  filters.star = (route.query.star as string) || ''
  filters.sort = (route.query.sort as string) || 'default'
  filters.min_price = route.query.min_price ? Number(route.query.min_price) : undefined
  filters.max_price = route.query.max_price ? Number(route.query.max_price) : undefined
}

function onSearch() {
  showMoreFilters.value = false
  page.value = 1
  const nextQuery: Record<string, string> = {
    ...(filters.keyword ? { keyword: filters.keyword } : {}),
    ...(filters.check_in_date ? { check_in_date: filters.check_in_date } : {}),
    ...(filters.check_out_date ? { check_out_date: filters.check_out_date } : {}),
    ...(filters.star ? { star: String(filters.star) } : {}),
    ...(filters.sort !== 'default' ? { sort: filters.sort } : {}),
    ...(filters.min_price ? { min_price: String(filters.min_price) } : {}),
    ...(filters.max_price ? { max_price: String(filters.max_price) } : {}),
  }

  const currentEntries = Object.entries(route.query)
    .filter(([, value]) => typeof value === 'string')
    .map(([key, value]) => [key, String(value)] as const)
    .sort(([a], [b]) => a.localeCompare(b))
  const currentQuery = Object.fromEntries(currentEntries) as Record<string, string>
  const normalizedNextQuery = Object.fromEntries(Object.entries(nextQuery).sort(([a], [b]) => a.localeCompare(b))) as Record<string, string>
  const sameQuery = JSON.stringify(currentQuery) === JSON.stringify(normalizedNextQuery)

  if (sameQuery) {
    fetchList()
    return
  }

  router.push({ path: '/hotels', query: normalizedNextQuery })
}

function switchStayType(nextType: StayType) {
  if (activeStayType.value === nextType) return
  const fromIndex = stayTypes.findIndex(item => item.value === activeStayType.value)
  const toIndex = stayTypes.findIndex(item => item.value === nextType)
  resultSlideDirection.value = toIndex > fromIndex ? 'left' : 'right'
  activeStayType.value = nextType
  onSearch()
}

function toggleViewMode() {
  const nextMode: ViewMode = viewMode.value === 'single' ? 'double' : 'single'
  resultSlideDirection.value = nextMode === 'double' ? 'left' : 'right'
  viewMode.value = nextMode
}

function clearPriceRange() {
  filters.min_price = undefined
  filters.max_price = undefined
}

function goHotelDetail(id: number) {
  router.push(`/hotels/${id}`)
}

function goHotelCompare(id: number) {
  router.push({ path: '/hotel-compare', query: { id: String(id) } })
}

watch(
  () => route.query,
  () => {
    page.value = 1
    syncFiltersFromRoute()
    fetchList()
  }
)

watch(
  loadMoreAnchor,
  () => {
    nextTick(() => {
      setupLoadMoreObserver()
    })
  }
)

watch(
  () => filters.check_in_date,
  (nextDate) => {
    if (!nextDate) return
    if (!filters.check_out_date || filters.check_out_date <= nextDate) {
      filters.check_out_date = addDays(nextDate, 1)
    }
  }
)

onMounted(async () => {
  syncFiltersFromRoute()
  await fetchList()
  await nextTick()
  setupLoadMoreObserver()
  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', handleWindowScroll, { passive: true })
    handleWindowScroll()
  }
})

onUnmounted(() => {
  loadMoreObserver?.disconnect()
  if (typeof window !== 'undefined') {
    window.removeEventListener('scroll', handleWindowScroll)
  }
})
</script>

<style scoped>
.hotel-result-left-enter-active,
.hotel-result-left-leave-active,
.hotel-result-right-enter-active,
.hotel-result-right-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.hotel-result-left-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.hotel-result-left-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.hotel-result-right-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.hotel-result-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>

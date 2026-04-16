<template>
  <div class="mx-auto max-w-5xl px-4 py-6">
    <p v-if="error" class="mb-4 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

    <!-- Search & Filter bar -->
    <div class="mb-6 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100">
      <div class="flex flex-col gap-3 md:flex-row md:items-end">
        <div class="flex-1">
          <input v-model="filters.keyword" type="text" placeholder="搜索酒店名、城市、商圈..." class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-brand" @keyup.enter="fetchList" />
        </div>
        <div class="grid grid-cols-2 gap-3 md:flex md:gap-3">
          <input v-model="filters.check_in_date" type="date" :min="today" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-brand" />
          <input v-model="filters.check_out_date" type="date" :min="filters.check_in_date || today" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-brand" />
        </div>
        <button type="button" @click="onSearch" class="w-full rounded-xl bg-brand px-6 py-2.5 text-sm font-medium text-white transition hover:bg-brand-dark md:w-auto">搜索</button>
      </div>

      <!-- Filters row -->
      <div class="mt-4 space-y-2">
        <div class="grid grid-cols-2 gap-2 lg:grid-cols-[150px_180px]">
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
        </div>
        <div class="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2 lg:max-w-[260px]">
          <input v-model.number="filters.min_price" type="number" placeholder="最低价" class="w-full rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs outline-none focus:border-brand" />
          <span class="text-center text-gray-300">—</span>
          <input v-model.number="filters.max_price" type="number" placeholder="最高价" class="w-full rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs outline-none focus:border-brand" />
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 4" :key="i" class="h-36 animate-pulse rounded-2xl bg-gray-200" />
    </div>

    <div v-else-if="hotels.length === 0" class="py-20 text-center text-gray-400">
      <p class="text-4xl">🔍</p>
      <p class="mt-3 text-sm">暂未找到符合条件的酒店</p>
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="hotel in hotels"
        :key="hotel.id"
        class="group flex cursor-pointer overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 transition hover:shadow-md"
        tabindex="0"
        @click="goHotelDetail(hotel.id)"
        @keydown.enter.prevent="goHotelDetail(hotel.id)"
      >
        <div class="hidden h-36 w-44 shrink-0 overflow-hidden bg-gray-200 sm:block">
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
          <div class="mt-2 flex items-end justify-between">
            <div class="flex items-center gap-2">
              <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
              <span class="text-xs text-gray-400">{{ hotel.review_count || 0 }}条评价</span>
            </div>
            <div class="flex items-end gap-3">
              <button
                @click.stop.prevent="goHotelCompare(hotel.id)"
                class="text-xs text-gray-400 hover:text-brand transition cursor-pointer"
              >AI 对比</button>
              <div class="text-right">
                <span class="text-lg font-bold text-orange-600">¥{{ hotel.min_price }}</span>
                <span class="text-xs text-gray-400">/晚起</span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="mt-6 flex justify-center gap-2">
      <button :disabled="page <= 1" @click="changePage(page - 1)" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">上一页</button>
      <span class="flex items-center px-3 text-sm text-gray-500">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button :disabled="page >= Math.ceil(total / pageSize)" @click="changePage(page + 1)" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicApi } from '@hotelink/api'
import { SelectField } from '@hotelink/ui'
import { buildImageThumbUrl } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const hotels = ref<any[]>([])
const error = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)

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

async function fetchList() {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.check_in_date) params.check_in_date = filters.check_in_date
    if (filters.check_out_date) params.check_out_date = filters.check_out_date
    if (filters.star) params.star = filters.star
    if (filters.sort !== 'default') params.sort = filters.sort
    if (filters.min_price) params.min_price = filters.min_price
    if (filters.max_price) params.max_price = filters.max_price
    const res = await publicApi.hotels(params)
    if (res.code === 0 && res.data) {
      hotels.value = ((res.data as any).items || []).map(mapHotel)
      total.value = (res.data as any).total || 0
    } else {
      hotels.value = []
      total.value = 0
      error.value = res.message || '酒店列表加载失败'
    }
  } catch {
    hotels.value = []
    total.value = 0
    error.value = '酒店列表加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
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
  page.value = 1
  router.push({
    path: '/hotels',
    query: {
      ...(filters.keyword ? { keyword: filters.keyword } : {}),
      ...(filters.check_in_date ? { check_in_date: filters.check_in_date } : {}),
      ...(filters.check_out_date ? { check_out_date: filters.check_out_date } : {}),
      ...(filters.star ? { star: String(filters.star) } : {}),
      ...(filters.sort !== 'default' ? { sort: filters.sort } : {}),
      ...(filters.min_price ? { min_price: String(filters.min_price) } : {}),
      ...(filters.max_price ? { max_price: String(filters.max_price) } : {}),
    },
  })
}

function changePage(nextPage: number) {
  page.value = nextPage
  fetchList()
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
    syncFiltersFromRoute()
    fetchList()
  }
)

onMounted(() => {
  syncFiltersFromRoute()
  fetchList()
})
</script>

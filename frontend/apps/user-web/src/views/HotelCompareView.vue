<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { publicApi, userAiApi } from '@hotelink/api'
import { extractApiError, formatDate } from '@hotelink/utils'

const route = useRoute()

const now = new Date()
const tomorrowDate = new Date(now)
tomorrowDate.setDate(tomorrowDate.getDate() + 1)

const today = formatDate(now)
const checkIn = ref(today)
const checkOut = ref(formatDate(tomorrowDate))

const searchKeyword = ref('')
const searchResults = ref<any[]>([])
const searching = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)
const showSearchModal = ref(false)

const selectedHotels = ref<any[]>([])
const comparing = ref(false)
const compareResult = ref<any>(null)
const compareError = ref('')

const selectedCount = computed(() => selectedHotels.value.length)
const canAddMore = computed(() => selectedCount.value < 3)

const hasValidDateRange = computed(() => {
  if (!checkIn.value || !checkOut.value) return false
  return new Date(checkOut.value).getTime() > new Date(checkIn.value).getTime()
})

const nights = computed(() => {
  if (!hasValidDateRange.value) return 0
  const ms = new Date(checkOut.value).getTime() - new Date(checkIn.value).getTime()
  return Math.round(ms / (1000 * 60 * 60 * 24))
})

const canCompare = computed(() => selectedCount.value >= 2 && hasValidDateRange.value)

function toFiniteNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function toPositivePrice(value: unknown): number {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return Number.POSITIVE_INFINITY
  return parsed >= 0 ? parsed : Number.POSITIVE_INFINITY
}

const fallbackWinnerHotel = computed(() => {
  if (!selectedHotels.value.length) return null
  const sorted = [...selectedHotels.value].sort((a, b) => {
    const ratingGap = toFiniteNumber(b.rating) - toFiniteNumber(a.rating)
    if (ratingGap !== 0) return ratingGap
    const starGap = toFiniteNumber(b.star) - toFiniteNumber(a.star)
    if (starGap !== 0) return starGap
    return toPositivePrice(a.min_price) - toPositivePrice(b.min_price)
  })
  return sorted[0] || null
})

const winnerHotel = computed(() => {
  const winnerId = Number(compareResult.value?.winner_id)
  if (winnerId) {
    const exact = selectedHotels.value.find((h) => Number(h.id) === winnerId)
    if (exact) return exact
  }
  return fallbackWinnerHotel.value
})

const winnerReason = computed(() => {
  const rawReason = String(compareResult.value?.winner_reason || '').trim()
  if (rawReason) return rawReason
  const hotel = winnerHotel.value
  if (!hotel) return ''
  const rating = formatRating(toFiniteNumber(hotel.rating))
  const price = hotel.min_price ?? '—'
  return `综合评分与价格表现更平衡（评分 ${rating}，参考价 ¥${price}/晚）`
})

const recommendationText = computed(() => {
  const backendText = String(compareResult.value?.recommendation || '').trim()
  if (backendText && !backendText.includes('暂无对比结果')) return backendText
  if (winnerHotel.value) {
    return `推荐优先考虑 ${winnerHotel.value.name}。${winnerReason.value}`
  }
  return '综合分析已完成，请查看下方详情。'
})

function normalizeHotel(hotel: any) {
  return {
    ...hotel,
    id: Number(hotel?.id),
    star: Number(hotel?.star_rating ?? hotel?.star ?? 0),
    rating: Number(hotel?.rating ?? 0),
    min_price: hotel?.min_price ?? hotel?.base_price ?? '—',
    city: hotel?.city || '未知城市',
    address: hotel?.address || '地址待补充',
  }
}

function formatRating(v: number) {
  if (!Number.isFinite(v) || v <= 0) return '暂无'
  return v.toFixed(1)
}

function readDimensionValue(dim: any, hotelId: number) {
  const values = dim?.values || {}
  return values?.[hotelId] ?? values?.[String(hotelId)] ?? '—'
}

function isWinner(hotelId: number): boolean {
  return Number(winnerHotel.value?.id) === Number(hotelId)
}

function resetCompareResult() {
  compareResult.value = null
  compareError.value = ''
}

function focusSearchInput() {
  showSearchModal.value = true
  nextTick(() => {
    if (!searchInputRef.value) return
    searchInputRef.value.focus()
  })
}

function closeSearchModal() {
  showSearchModal.value = false
  searching.value = false
}

function addHotel(hotel: any) {
  const normalized = normalizeHotel(hotel)
  if (!normalized.id) return
  if (selectedHotels.value.some((h) => Number(h.id) === normalized.id)) return
  if (selectedHotels.value.length >= 3) {
    compareError.value = '最多只能选择 3 家酒店进行对比'
    return
  }
  selectedHotels.value.push(normalized)
  if (selectedHotels.value.length >= 3) {
    showSearchModal.value = false
  }
  resetCompareResult()
}

function removeHotel(id: number) {
  selectedHotels.value = selectedHotels.value.filter((h) => Number(h.id) !== Number(id))
  resetCompareResult()
}

async function addHotelById(idLike: unknown) {
  const id = Number(idLike)
  if (!Number.isFinite(id) || id <= 0) return
  if (selectedHotels.value.some((h) => Number(h.id) === id)) return
  try {
    const res = await publicApi.hotelDetail(id)
    if (res.code === 0 && res.data) {
      addHotel(res.data)
    }
  } catch {
    compareError.value = '加载酒店信息失败，请重试'
  }
}

async function searchHotels() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    const res = await publicApi.hotels({ keyword, page: 1, page_size: 12 })
    if (res.code === 0 && res.data) {
      const rawList = (res.data as any).items || (res.data as any).results || []
      searchResults.value = rawList.map(normalizeHotel)
    } else {
      searchResults.value = []
    }
  } catch {
    searchResults.value = []
    compareError.value = '搜索失败，请检查网络'
  } finally {
    searching.value = false
  }
}

function onSearchKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') searchHotels()
}

async function runCompare() {
  if (selectedHotels.value.length < 2) {
    compareError.value = '请至少选择 2 家酒店再开始对比'
    return
  }
  if (!hasValidDateRange.value) {
    compareError.value = '退房日期需晚于入住日期'
    return
  }
  comparing.value = true
  compareError.value = ''
  compareResult.value = null
  try {
    const res = await userAiApi.hotelCompare({
      hotel_ids: selectedHotels.value.map((h) => Number(h.id)),
      check_in_date: checkIn.value,
      check_out_date: checkOut.value,
    })
    if (res.code === 0 && res.data) {
      compareResult.value = res.data
    } else {
      compareError.value = extractApiError(res, '对比失败，请稍后重试')
    }
  } catch {
    compareError.value = '网络错误，请检查连接后重试'
  } finally {
    comparing.value = false
  }
}

watch([checkIn, checkOut], () => {
  resetCompareResult()
})

watch(canAddMore, (canAdd) => {
  if (!canAdd) {
    closeSearchModal()
  }
})

watch(
  () => route.query.id,
  (id) => {
    if (Array.isArray(id)) {
      if (id.length) addHotelById(id[0])
      return
    }
    if (id) addHotelById(id)
  }
)

onMounted(() => {
  const id = route.query.id
  if (Array.isArray(id)) {
    if (id.length) addHotelById(id[0])
    return
  }
  if (id) addHotelById(id)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-5">
    <div class="mx-auto max-w-5xl px-4">
      <div class="mb-4">
        <router-link to="/hotels" class="text-sm text-gray-400 transition hover:text-brand">← 返回列表</router-link>
        <h1 class="mt-2 text-2xl font-bold text-gray-900">AI 智能酒店对比</h1>
        <p class="mt-1 text-sm text-gray-500">按“选酒店 → 选日期 → 开始对比”的顺序操作，结果会更清晰。</p>
      </div>

      <p v-if="compareError" class="mb-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 ring-1 ring-red-100">
        {{ compareError }}
      </p>

      <section class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100 sm:p-5">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-900">1. 选择酒店</h2>
          <span class="rounded-full bg-brand/10 px-2.5 py-1 text-xs font-semibold text-brand">{{ selectedCount }}/3</span>
        </div>

        <div v-if="selectedHotels.length" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="hotel in selectedHotels"
            :key="hotel.id"
            class="rounded-xl border border-gray-100 p-3 transition hover:border-brand/30 hover:bg-brand/[0.03]"
          >
            <div class="mb-1 flex items-start justify-between gap-2">
              <h3 class="line-clamp-2 text-sm font-semibold text-gray-900">{{ hotel.name }}</h3>
              <button
                type="button"
                class="shrink-0 rounded-full px-1.5 text-gray-300 transition hover:bg-red-50 hover:text-red-500"
                @click="removeHotel(hotel.id)"
              >
                ×
              </button>
            </div>
            <p class="text-xs text-gray-400">{{ hotel.city }} · {{ hotel.address }}</p>
            <div class="mt-2 flex items-center justify-between">
              <span class="text-xs text-yellow-500">{{ '★'.repeat(hotel.star || 0) }}</span>
              <div class="text-right">
                <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
                <p class="mt-1 text-xs text-orange-500">¥{{ hotel.min_price }}/晚起</p>
              </div>
            </div>
          </article>
        </div>
        <div v-else class="rounded-xl border border-dashed border-gray-200 py-8 text-center text-sm text-gray-400">
          还没选酒店，请点击“+ 添加酒店”开始选择（至少 2 家）
        </div>

        <button
          v-if="canAddMore"
          type="button"
          class="mt-3 rounded-xl border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 transition hover:border-brand/50 hover:text-brand"
          @click="focusSearchInput"
        >
          + 添加酒店
        </button>
      </section>

      <section class="mt-4 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100 sm:p-5">
        <h2 class="mb-3 text-base font-semibold text-gray-900">2. 选择日期</h2>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs text-gray-500">入住日期</label>
            <input
              v-model="checkIn"
              type="date"
              :min="today"
              class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs text-gray-500">退房日期</label>
            <input
              v-model="checkOut"
              type="date"
              :min="checkIn"
              class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            />
          </div>
        </div>
        <p v-if="hasValidDateRange" class="mt-2 text-xs text-gray-500">共 {{ nights }} 晚</p>
        <p v-else class="mt-2 text-xs text-red-500">退房日期需要晚于入住日期</p>
      </section>

      <section class="mt-4 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100 sm:p-5">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-sm text-gray-500">至少 2 家酒店且日期有效时可开始 AI 对比</p>
          <button
            type="button"
            :disabled="!canCompare || comparing"
            class="w-full rounded-xl bg-brand px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            @click="runCompare"
          >
            {{ comparing ? 'AI 分析中…' : '开始对比' }}
          </button>
        </div>
      </section>

      <section v-if="compareResult" class="mt-4 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100 sm:p-5">
        <div class="rounded-xl bg-gradient-to-r from-brand/5 to-cyan-50 p-4 ring-1 ring-brand/10">
          <p class="mb-1 text-sm font-semibold text-brand">AI 综合建议</p>
          <p class="text-sm leading-relaxed text-gray-700">
            {{ recommendationText }}
          </p>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-3 md:hidden">
          <article
            v-for="hotel in selectedHotels"
            :key="`mobile-${hotel.id}`"
            class="rounded-xl border p-3"
            :class="isWinner(hotel.id) ? 'border-green-200 bg-green-50/40' : 'border-gray-100'"
          >
            <div class="mb-2 flex items-start justify-between gap-2">
              <h3 class="line-clamp-2 text-sm font-semibold text-gray-900">{{ hotel.name }}</h3>
              <span v-if="isWinner(hotel.id)" class="rounded-full bg-green-100 px-2 py-0.5 text-[11px] font-semibold text-green-700">
                推荐
              </span>
            </div>
            <div class="space-y-1.5 text-xs text-gray-600">
              <p>星级：<span class="text-yellow-500">{{ '★'.repeat(hotel.star || 0) }}</span></p>
              <p>评分：<span class="rounded bg-brand/10 px-1.5 py-0.5 font-semibold text-brand">{{ formatRating(hotel.rating) }}</span></p>
              <p>价格：<span class="font-semibold text-orange-500">¥{{ hotel.min_price }}</span>/晚</p>
              <p>城市：{{ hotel.city }}</p>
              <template v-if="compareResult.dimensions">
                <p v-for="(dim, idx) in compareResult.dimensions" :key="`mobile-dim-${idx}-${hotel.id}`">
                  {{ dim.name }}：{{ readDimensionValue(dim, hotel.id) }}
                </p>
              </template>
            </div>
          </article>
        </div>

        <div class="mt-4 hidden overflow-x-auto rounded-xl border border-gray-100 md:block">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="w-28 px-4 py-3 text-left text-xs font-semibold text-gray-400">对比项</th>
                <th
                  v-for="hotel in selectedHotels"
                  :key="`head-${hotel.id}`"
                  class="px-4 py-3 text-center font-semibold text-gray-700"
                >
                  <div class="line-clamp-1">{{ hotel.name }}</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b border-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">星级</td>
                <td v-for="hotel in selectedHotels" :key="`star-${hotel.id}`" class="px-4 py-3 text-center text-yellow-500">
                  {{ '★'.repeat(hotel.star || 0) || '—' }}
                </td>
              </tr>
              <tr class="border-b border-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">评分</td>
                <td v-for="hotel in selectedHotels" :key="`rating-${hotel.id}`" class="px-4 py-3 text-center">
                  <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">最低价</td>
                <td v-for="hotel in selectedHotels" :key="`price-${hotel.id}`" class="px-4 py-3 text-center">
                  <span class="font-semibold text-orange-500">¥{{ hotel.min_price }}</span><span class="text-xs text-gray-400">/晚</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">城市</td>
                <td v-for="hotel in selectedHotels" :key="`city-${hotel.id}`" class="px-4 py-3 text-center text-gray-600">{{ hotel.city }}</td>
              </tr>
              <template v-if="compareResult.dimensions">
                <tr
                  v-for="(dim, idx) in compareResult.dimensions"
                  :key="`dim-${idx}`"
                  class="border-b border-gray-50"
                >
                  <td class="px-4 py-3 text-xs text-gray-400">{{ dim.name }}</td>
                  <td
                    v-for="hotel in selectedHotels"
                    :key="`dim-${idx}-${hotel.id}`"
                    class="px-4 py-3 text-center text-xs text-gray-600"
                  >
                    {{ readDimensionValue(dim, hotel.id) }}
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <div v-if="winnerHotel" class="mt-4 rounded-xl bg-green-50 px-4 py-3 text-sm text-green-700 ring-1 ring-green-100">
          综合推荐：<strong>{{ winnerHotel.name }}</strong>
          <span v-if="winnerReason">，{{ winnerReason }}</span>
        </div>
      </section>
    </div>

    <Teleport to="body">
      <div
        v-if="showSearchModal"
        class="fixed inset-0 z-[90] flex items-end justify-center bg-black/40 p-3 sm:items-center sm:p-4"
        @click.self="closeSearchModal"
      >
        <div class="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-gray-100">
          <div class="bg-gradient-to-r from-brand/[0.06] via-cyan-50/70 to-white px-4 py-3 sm:px-5 sm:py-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-base font-semibold text-gray-900">搜索并添加酒店</h2>
                <p class="mt-0.5 text-xs text-gray-500">最多添加 3 家酒店参与对比</p>
              </div>
              <span class="rounded-full bg-brand/10 px-2.5 py-1 text-xs font-semibold text-brand">
                {{ selectedCount }}/3
              </span>
            </div>
          </div>

          <div class="px-4 pb-4 pt-3 sm:px-5 sm:pb-5">
            <div class="flex items-center justify-between">
              <p class="text-xs text-gray-400">输入酒店名或城市后点击搜索</p>
              <button
                type="button"
                class="rounded-full px-2 py-1 text-xl leading-none text-gray-300 transition hover:bg-gray-100 hover:text-gray-500"
                @click="closeSearchModal"
              >
                ×
              </button>
            </div>

            <div class="mt-3 flex flex-col gap-2 sm:flex-row">
              <div class="relative flex-1">
                <svg viewBox="0 0 20 20" aria-hidden="true" class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-300">
                  <circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" stroke-width="1.8" />
                  <path d="M13.8 13.8 L17 17" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.8" />
                </svg>
                <input
                  ref="searchInputRef"
                  v-model="searchKeyword"
                  type="text"
                  placeholder="输入酒店名称或城市…"
                  class="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                  @keydown="onSearchKeydown"
                />
              </div>
              <button
                type="button"
                :disabled="searching"
                class="inline-flex items-center justify-center rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:opacity-50"
                @click="searchHotels"
              >
                {{ searching ? '搜索中…' : '搜索' }}
              </button>
            </div>

            <div class="mt-4 max-h-[56vh] overflow-y-auto pr-1">
              <div v-if="searching" class="space-y-2">
                <div v-for="i in 3" :key="`search-loading-${i}`" class="animate-pulse rounded-xl border border-gray-100 bg-gray-50 px-3 py-3">
                  <div class="h-4 w-40 rounded bg-gray-200" />
                  <div class="mt-2 h-3 w-56 rounded bg-gray-200" />
                  <div class="mt-3 h-3 w-24 rounded bg-gray-200" />
                </div>
              </div>

              <div v-else-if="searchResults.length" class="space-y-2">
                <article
                  v-for="hotel in searchResults"
                  :key="hotel.id"
                  class="group flex items-center gap-3 rounded-xl border border-gray-100 bg-white px-3 py-3 transition hover:border-brand/30 hover:bg-brand/[0.02]"
                >
                  <div class="min-w-0 flex-1">
                    <div class="flex items-start justify-between gap-2">
                      <h3 class="line-clamp-1 text-sm font-semibold text-gray-900">{{ hotel.name }}</h3>
                      <span class="shrink-0 rounded-md bg-amber-50 px-1.5 py-0.5 text-[11px] text-amber-500">
                        {{ '★'.repeat(hotel.star || 0) || '暂无星级' }}
                      </span>
                    </div>
                    <p class="mt-1 line-clamp-1 text-xs text-gray-400">📍 {{ hotel.city }} · {{ hotel.address }}</p>
                    <div class="mt-2 flex items-center gap-2 text-xs">
                      <span class="rounded bg-brand/10 px-1.5 py-0.5 font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
                      <span class="font-semibold text-orange-500">¥{{ hotel.min_price }}/晚起</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    :disabled="!canAddMore || selectedHotels.some((h) => h.id === hotel.id)"
                    class="inline-flex h-8 min-w-[86px] items-center justify-center rounded-lg bg-brand/10 px-3 text-xs font-semibold text-brand transition hover:bg-brand/20 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-300"
                    @click="addHotel(hotel)"
                  >
                    {{ selectedHotels.some((h) => h.id === hotel.id) ? '已添加' : '加入对比' }}
                  </button>
                </article>
              </div>

              <div v-else class="rounded-xl border border-dashed border-gray-200 bg-gray-50/50 py-10 text-center">
                <p class="text-2xl leading-none text-gray-300">🔎</p>
                <p class="mt-2 text-sm text-gray-500">未找到匹配酒店</p>
                <p class="mt-1 text-xs text-gray-400">可尝试输入城市名、品牌名或酒店关键字</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

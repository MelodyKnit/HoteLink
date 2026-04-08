<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { publicApi, userAiApi } from '@hotelink/api'
import { formatDate } from '@hotelink/utils'

const route = useRoute()
const today = formatDate(new Date())
const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1)

const checkIn = ref(today)
const checkOut = ref(formatDate(tomorrow))

// 搜索酒店
const searchKeyword = ref('')
const searchResults = ref<any[]>([])
const searching = ref(false)

async function searchHotels() {
  if (!searchKeyword.value.trim()) return
  searching.value = true
  try {
    const res = await publicApi.hotels({ keyword: searchKeyword.value, page: 1, page_size: 12 })
    if (res.code === 0 && res.data) {
      searchResults.value = (res.data as any).items || (res.data as any).results || []
    }
  } catch { /* ignore */ } finally {
    searching.value = false
  }
}

function onSearchKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') searchHotels()
}

// 已选中的对比酒店（最多 3 家）
const selectedHotels = ref<any[]>([])

function addHotel(hotel: any) {
  if (selectedHotels.value.length >= 3) return
  if (selectedHotels.value.find(h => h.id === hotel.id)) return
  selectedHotels.value.push(hotel)
}

function removeHotel(id: number) {
  selectedHotels.value = selectedHotels.value.filter(h => h.id !== id)
  compareResult.value = null
}

const canCompare = computed(() => selectedHotels.value.length >= 2 && checkIn.value && checkOut.value)

// AI 对比
const comparing = ref(false)
const compareResult = ref<any>(null)
const compareError = ref('')

async function runCompare() {
  if (!canCompare.value) return
  comparing.value = true
  compareError.value = ''
  compareResult.value = null
  try {
    const res = await userAiApi.hotelCompare({
      hotel_ids: selectedHotels.value.map(h => h.id),
      check_in_date: checkIn.value,
      check_out_date: checkOut.value,
    })
    if (res.code === 0 && res.data) {
      compareResult.value = res.data
    } else {
      compareError.value = '对比失败，请稍后重试'
    }
  } catch {
    compareError.value = '网络错误，请检查连接后重试'
  } finally {
    comparing.value = false
  }
}

function formatRating(v: number) {
  if (!v) return '暂无'
  return v.toFixed(1)
}

onMounted(async () => {
  const id = route.query.id
  if (id) {
    try {
      const res = await publicApi.hotelDetail(Number(id))
      if (res.code === 0 && res.data) addHotel(res.data)
    } catch { /* ignore */ }
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="mx-auto max-w-5xl px-4">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center gap-3">
          <router-link to="/hotels" class="text-gray-400 hover:text-brand transition text-sm">← 返回列表</router-link>
        </div>
        <h1 class="mt-2 text-xl font-bold text-gray-900">🔍 AI 智能对比</h1>
        <p class="text-sm text-gray-500 mt-0.5">最多选择 3 家酒店，AI 为您综合分析并推荐最佳选择</p>
      </div>

      <!-- Selected Hotels Bar -->
      <div class="mb-6 flex flex-wrap gap-3">
        <div
          v-for="hotel in selectedHotels"
          :key="hotel.id"
          class="flex items-center gap-2 rounded-xl bg-white px-3 py-2 shadow-sm ring-1 ring-gray-100"
        >
          <span class="text-sm font-medium text-gray-800">{{ hotel.name }}</span>
          <button @click="removeHotel(hotel.id)" class="text-gray-300 hover:text-red-400 transition text-lg leading-none">×</button>
        </div>
        <div
          v-for="i in (3 - selectedHotels.length)"
          :key="`empty-${i}`"
          class="flex items-center gap-2 rounded-xl border-2 border-dashed border-gray-200 px-4 py-2"
        >
          <span class="text-sm text-gray-400">+ 添加酒店</span>
        </div>
      </div>

      <!-- Date Range + Compare Button -->
      <div class="mb-6 flex flex-col sm:flex-row gap-3 items-end">
        <div class="flex-1">
          <label class="block text-xs text-gray-500 mb-1">入住日期</label>
          <input v-model="checkIn" type="date" :min="today"
            class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30" />
        </div>
        <div class="flex-1">
          <label class="block text-xs text-gray-500 mb-1">退房日期</label>
          <input v-model="checkOut" type="date" :min="checkIn"
            class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30" />
        </div>
        <button
          @click="runCompare"
          :disabled="!canCompare || comparing"
          class="rounded-xl bg-brand px-6 py-2 text-sm font-semibold text-white shadow transition hover:bg-brand/90 disabled:opacity-50"
        >
          {{ comparing ? 'AI 分析中…' : '开始对比' }}
        </button>
      </div>

      <!-- Error -->
      <p v-if="compareError" class="mb-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{{ compareError }}</p>

      <!-- Compare Result -->
      <div v-if="compareResult" class="mb-8">
        <!-- AI Recommendation Text -->
        <div class="mb-4 rounded-2xl bg-gradient-to-r from-brand/5 to-teal-50 p-4 ring-1 ring-brand/10">
          <div class="mb-1 flex items-center gap-2">
            <span class="text-base">✨</span>
            <span class="text-sm font-semibold text-brand">AI 综合推荐</span>
          </div>
          <p class="text-sm text-gray-700 leading-relaxed">{{ compareResult.recommendation || '综合分析完成，请参阅下方详细对比。' }}</p>
        </div>

        <!-- Comparison Table -->
        <div class="overflow-x-auto rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-400 w-28">对比项</th>
                <th
                  v-for="hotel in selectedHotels"
                  :key="hotel.id"
                  class="px-4 py-3 text-center font-semibold text-gray-700"
                >
                  <div class="line-clamp-1">{{ hotel.name }}</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">星级</td>
                <td v-for="hotel in selectedHotels" :key="`star-${hotel.id}`" class="px-4 py-3 text-center">
                  <span class="text-yellow-400">{{ '★'.repeat(hotel.star_rating || hotel.star || 0) }}</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">评分</td>
                <td v-for="hotel in selectedHotels" :key="`rating-${hotel.id}`" class="px-4 py-3 text-center">
                  <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">最低价</td>
                <td v-for="hotel in selectedHotels" :key="`price-${hotel.id}`" class="px-4 py-3 text-center">
                  <span class="font-semibold text-orange-500">¥{{ hotel.min_price || '—' }}</span><span class="text-xs text-gray-400">/晚</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3 text-xs text-gray-400">城市</td>
                <td v-for="hotel in selectedHotels" :key="`city-${hotel.id}`" class="px-4 py-3 text-center text-gray-600">{{ hotel.city || '—' }}</td>
              </tr>
              <!-- AI dimension rows -->
              <template v-if="compareResult.dimensions">
                <tr
                  v-for="(dim, idx) in compareResult.dimensions"
                  :key="`dim-${idx}`"
                  class="border-b border-gray-50 hover:bg-gray-50"
                >
                  <td class="px-4 py-3 text-xs text-gray-400">{{ dim.name }}</td>
                  <td
                    v-for="hotel in selectedHotels"
                    :key="`dim-${idx}-${hotel.id}`"
                    class="px-4 py-3 text-center text-gray-600 text-xs"
                  >{{ (dim.values || {})[hotel.id] || '—' }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Verdict -->
        <div v-if="compareResult.winner_id" class="mt-4 rounded-xl bg-green-50 px-4 py-3 text-sm text-green-700 ring-1 ring-green-100">
          🏆 综合推荐：<strong>{{ selectedHotels.find(h => h.id === compareResult.winner_id)?.name || 'N/A' }}</strong>
          <span v-if="compareResult.winner_reason"> — {{ compareResult.winner_reason }}</span>
        </div>
      </div>

      <!-- Search Panel -->
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
        <h2 class="mb-3 text-sm font-semibold text-gray-700">搜索并添加酒店</h2>
        <div class="flex gap-2 mb-4">
          <input
            v-model="searchKeyword"
            @keydown="onSearchKeydown"
            placeholder="输入酒店名称或城市…"
            class="flex-1 rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
          />
          <button
            @click="searchHotels"
            :disabled="searching"
            class="rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:opacity-50"
          >
            {{ searching ? '搜索中…' : '搜索' }}
          </button>
        </div>

        <div v-if="searchResults.length" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="hotel in searchResults"
            :key="hotel.id"
            class="flex items-center gap-3 rounded-xl border border-gray-100 px-3 py-2.5 hover:bg-gray-50 transition"
          >
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800 line-clamp-1">{{ hotel.name }}</p>
              <p class="text-xs text-gray-400">{{ hotel.city }} · {{ '★'.repeat(hotel.star_rating || 0) }}</p>
            </div>
            <button
              @click="addHotel(hotel)"
              :disabled="selectedHotels.length >= 3 || selectedHotels.some(h => h.id === hotel.id)"
              class="shrink-0 rounded-lg bg-brand/10 px-2.5 py-1 text-xs font-semibold text-brand transition hover:bg-brand/20 disabled:text-gray-300 disabled:bg-gray-100"
            >
              {{ selectedHotels.some(h => h.id === hotel.id) ? '已添加' : '+ 对比' }}
            </button>
          </div>
        </div>
        <div v-else-if="!searching" class="py-6 text-center text-sm text-gray-400">
          搜索酒店，然后添加到对比列表
        </div>
      </div>
    </div>
  </div>
</template>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Back nav -->
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="truncate text-sm font-semibold text-gray-800">{{ hotel.name || '酒店详情' }}</h1>
      <div class="flex-1" />
      <button @click="toggleFav" class="text-xl" :class="isFav ? 'text-red-500' : 'text-gray-300'">{{ isFav ? '❤️' : '🤍' }}</button>
    </header>

    <div v-if="loading" class="flex items-center justify-center py-40">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
    </div>

    <div v-else-if="error" class="mx-auto max-w-5xl px-4 py-16 text-center">
      <p class="text-sm text-red-500">{{ error }}</p>
      <router-link to="/hotels" class="mt-3 inline-block rounded-xl bg-brand px-4 py-2 text-sm text-white">返回酒店列表</router-link>
    </div>

    <template v-else>
      <!-- Image gallery -->
      <div class="relative h-56 overflow-hidden bg-gray-200 md:h-80">
        <img v-if="hotel.images?.[currentImg]" :src="hotel.images[currentImg]" :alt="hotel.name" class="h-full w-full object-cover" />
        <div v-else class="flex h-full items-center justify-center text-5xl text-gray-300">🏨</div>
        <div v-if="hotel.images?.length > 1" class="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5">
          <button v-for="(_, i) in hotel.images" :key="i" @click="currentImg = i"
            class="h-1.5 w-6 rounded-full transition" :class="i === currentImg ? 'bg-white' : 'bg-white/40'" />
        </div>
      </div>

      <div class="mx-auto max-w-5xl px-4 py-6">
        <!-- Hotel Info -->
        <div class="rounded-2xl bg-white p-5 shadow-sm">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">{{ hotel.name }}</h2>
              <span class="text-xs text-yellow-500">{{ '★'.repeat(hotel.star || 0) }}</span>
            </div>
            <div class="text-right">
              <span class="rounded bg-brand/10 px-2 py-1 text-sm font-bold text-brand">{{ formatRating(hotel.rating) }}</span>
              <p class="mt-1 text-xs text-gray-400">{{ hotel.review_count || 0 }}条评价</p>
            </div>
          </div>
          <p class="mt-3 text-sm text-gray-500">📍 {{ hotel.city }} {{ hotel.address }}</p>
          <p v-if="hotel.phone" class="mt-1 text-sm text-gray-500">📞 {{ hotel.phone }}</p>
          <p v-if="hotel.description" class="mt-3 text-sm leading-relaxed text-gray-600">{{ hotel.description }}</p>
        </div>

        <!-- Facilities -->
        <div v-if="hotel.facilities?.length" class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-800">设施与服务</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="f in hotel.facilities" :key="f" class="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">{{ f }}</span>
          </div>
        </div>

        <!-- Policies -->
        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-800">入住政策</h3>
          <div class="grid grid-cols-2 gap-3 text-sm text-gray-600">
            <p>🕐 入住时间：{{ hotel.check_in_time || '14:00 后' }}</p>
            <p>🕐 退房时间：{{ hotel.check_out_time || '12:00 前' }}</p>
          </div>
        </div>

        <!-- Room Types -->
        <div class="mt-6">
          <h3 class="mb-4 text-lg font-bold text-gray-900">可选房型</h3>
          <div class="space-y-3">
            <div v-for="room in hotel.room_types || []" :key="room.id"
              class="flex overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100"
            >
              <div class="hidden h-32 w-32 shrink-0 overflow-hidden bg-gray-200 sm:block">
                <img v-if="room.image_url" :src="room.image_url" :alt="room.name" class="h-full w-full object-cover" />
                <div v-else class="flex h-full items-center justify-center text-2xl text-gray-300">🛏️</div>
              </div>
              <div class="flex flex-1 flex-col justify-between p-4">
                <div>
                  <h4 class="font-semibold text-gray-800">{{ room.name }}</h4>
                  <div class="mt-1 flex flex-wrap gap-2 text-xs text-gray-400">
                    <span>{{ bedTypeMap[room.bed_type] || room.bed_type }}</span>
                    <span v-if="room.area">{{ room.area }}㎡</span>
                    <span>可住{{ room.max_guest_count || 2 }}人</span>
                    <span v-if="room.breakfast_count">含{{ room.breakfast_count }}早</span>
                  </div>
                </div>
                <div class="mt-2 flex items-end justify-between">
                  <div>
                    <span class="text-lg font-bold text-orange-600">¥{{ room.base_price }}</span>
                    <span class="text-xs text-gray-400">/晚</span>
                  </div>
                  <button @click="handleBook(room)" class="rounded-full bg-brand px-5 py-1.5 text-sm font-medium text-white transition hover:bg-brand-dark">预订</button>
                </div>
              </div>
            </div>
            <div v-if="!hotel.room_types?.length" class="py-10 text-center text-sm text-gray-400">暂无可预订房型</div>
          </div>
        </div>

        <!-- Reviews -->
        <div class="mt-6">
          <h3 class="mb-4 text-lg font-bold text-gray-900">住客评价</h3>
          <div v-if="reviews.length" class="space-y-3">
            <div v-for="r in reviews" :key="r.id" class="rounded-2xl bg-white p-4 shadow-sm">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="flex h-8 w-8 items-center justify-center rounded-full bg-brand/10 text-xs font-bold text-brand">{{ (r.username || '用户').charAt(0) }}</div>
                  <span class="text-sm font-medium text-gray-800">{{ r.username || '匿名用户' }}</span>
                </div>
                <span class="text-xs text-yellow-500">{{ '★'.repeat(r.score) }}</span>
              </div>
              <p class="mt-2 text-sm text-gray-600">{{ r.content }}</p>
              <p class="mt-2 text-xs text-gray-400">{{ r.created_at }}</p>
              <div v-if="r.reply" class="mt-2 rounded-lg bg-gray-50 p-3 text-xs text-gray-500">
                <span class="font-medium text-brand">酒店回复：</span>{{ r.reply }}
              </div>
            </div>
          </div>
          <div v-else class="py-8 text-center text-sm text-gray-400">暂无评价</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicApi, userFavoriteApi, getToken } from '@hotelink/api'
import { BED_TYPE_MAP } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const hotel = ref<any>({})
const reviews = ref<any[]>([])
const currentImg = ref(0)
const isFav = ref(false)
const error = ref('')
const bedTypeMap = BED_TYPE_MAP

function formatRating(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(1) : '暂无'
}

function withTimeout<T>(promise: Promise<T>, timeoutMs = 12000): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('timeout')), timeoutMs)
    promise
      .then((result) => {
        clearTimeout(timer)
        resolve(result)
      })
      .catch((err) => {
        clearTimeout(timer)
        reject(err)
      })
  })
}

function normalizeHotelData(data: any) {
  const cover = data?.cover_image || ''
  const images = Array.isArray(data?.images) && data.images.length ? data.images : (cover ? [cover] : [])
  const roomTypes = Array.isArray(data?.room_types) ? data.room_types : []
  return {
    ...data,
    images,
    room_types: roomTypes.map((room: any) => ({
      ...room,
      image_url: room?.image_url || room?.image || cover || '',
    })),
  }
}

// 切换Fav显示状态。
async function toggleFav() {
  const hotelId = Number(route.params.id)
  if (!getToken()) { router.push({ name: 'login', query: { redirect: route.fullPath } }); return }
  if (!Number.isFinite(hotelId) || hotelId <= 0) return
  try {
    if (isFav.value) {
      await userFavoriteApi.remove(hotelId)
      isFav.value = false
    } else {
      await userFavoriteApi.add(hotelId)
      isFav.value = true
    }
  } catch { /* ignore */ }
}

// 处理 Book 交互逻辑。
function handleBook(room: any) {
  const hotelId = Number(route.params.id)
  if (!getToken()) { router.push({ name: 'login', query: { redirect: route.fullPath } }); return }
  if (!Number.isFinite(hotelId) || hotelId <= 0) return
  router.push({ path: '/booking', query: { hotel_id: String(hotelId), room_type_id: String(room.id), room_name: room.name, price: String(room.base_price), hotel_name: hotel.value.name } })
}

async function loadHotelDetail() {
  const hotelId = Number(route.params.id)
  if (!Number.isFinite(hotelId) || hotelId <= 0) {
    error.value = '酒店参数无效，请返回列表重新选择'
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    const [hotelResult, reviewResult] = await Promise.allSettled([
      withTimeout(publicApi.hotelDetail(hotelId)),
      withTimeout(publicApi.hotelReviews({ hotel_id: hotelId, page: 1, page_size: 5 })),
    ])

    if (hotelResult.status === 'fulfilled') {
      const hotelRes = hotelResult.value
      if (hotelRes.code === 0 && hotelRes.data) {
        hotel.value = normalizeHotelData(hotelRes.data)
      } else {
        hotel.value = {}
        error.value = hotelRes.message || '酒店详情加载失败'
      }
    } else {
      hotel.value = {}
      error.value = '酒店详情加载超时，请稍后重试'
    }

    if (reviewResult.status === 'fulfilled') {
      const reviewRes = reviewResult.value
      reviews.value = (reviewRes.code === 0 && reviewRes.data) ? ((reviewRes.data as any).items || []) : []
    } else {
      reviews.value = []
    }
  } catch {
    hotel.value = {}
    reviews.value = []
    error.value = '酒店详情加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    const parsed = Number(route.params.id)
    if (Number.isFinite(parsed)) {
      currentImg.value = 0
      loadHotelDetail()
    }
  },
  { immediate: true }
)
</script>

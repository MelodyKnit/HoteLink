<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Back nav -->
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="truncate text-sm font-semibold text-gray-800">{{ hotel.name || '酒店详情' }}</h1>
      <div class="flex-1" />
      <button @click="toggleFav" :disabled="togglingFav" class="text-xl transition-opacity" :class="[isFav ? 'text-red-500' : 'text-gray-300', togglingFav ? 'opacity-50' : '']" >{{ isFav ? '❤️' : '🤍' }}</button>
    </header>

    <div v-if="loading" class="mx-auto max-w-5xl space-y-4 px-4 py-6">
      <div class="h-56 animate-pulse rounded-2xl bg-gray-200 md:h-80" />
      <div class="rounded-2xl bg-white p-5 shadow-sm">
        <div class="mb-3 h-6 w-1/3 animate-pulse rounded bg-gray-200" />
        <div class="mb-2 h-4 w-2/3 animate-pulse rounded bg-gray-100" />
        <div class="h-4 w-1/2 animate-pulse rounded bg-gray-100" />
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm">
        <div class="mb-3 h-5 w-1/4 animate-pulse rounded bg-gray-200" />
        <div class="h-4 w-full animate-pulse rounded bg-gray-100" />
      </div>
    </div>

    <div v-else-if="error" class="mx-auto max-w-5xl px-4 py-16 text-center">
      <p class="text-sm text-red-500">{{ error }}</p>
      <router-link to="/hotels" class="mt-3 inline-block rounded-xl bg-brand px-4 py-2 text-sm text-white">返回酒店列表</router-link>
    </div>

    <template v-else>
      <!-- Image gallery -->
      <div
        class="relative h-56 overflow-hidden bg-gray-200 md:h-80"
        @touchstart="onGalleryTouchStart"
        @touchmove="onGalleryTouchMove"
        @touchend="onGalleryTouchEnd"
        @touchcancel="onGalleryTouchEnd"
      >
        <div v-if="hotel.images?.length" class="flex h-full" :style="galleryTrackStyle">
          <div v-for="(img, i) in hotel.images" :key="`${img}-${i}`" class="h-full w-full shrink-0">
            <img
              :src="img"
              :alt="`${hotel.name} 图片 ${i + 1}`"
              class="h-full w-full cursor-zoom-in select-none object-cover"
              draggable="false"
              @click="handleGalleryImageClick(i)"
            />
          </div>
        </div>
        <div v-else class="flex h-full items-center justify-center text-5xl text-gray-300">🏨</div>
        <p
          v-if="hotel.images?.length > 1"
          class="pointer-events-none absolute left-3 top-3 rounded-full bg-black/35 px-2.5 py-1 text-[11px] text-white/95 backdrop-blur"
        >
          左右滑动切换，点击看大图
        </p>
        <div v-if="hotel.images?.length > 1" class="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5">
          <button
            v-for="(_, i) in hotel.images"
            :key="i"
            type="button"
            class="h-1.5 w-6 rounded-full transition"
            :class="i === currentImg ? 'bg-white' : 'bg-white/40'"
            @click="jumpToImage(i)"
          />
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
          <p v-if="poiName && poiDistanceText" class="mt-2 rounded-lg bg-brand/10 px-3 py-2 text-xs text-brand">
            📍 距 {{ poiName }} 约 {{ poiDistanceText }} km（来自 AI 智能订房）
          </p>
          <p v-if="hotel.description" class="mt-3 text-sm leading-relaxed text-gray-600">{{ hotel.description }}</p>
        </div>

        <!-- Map -->
        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-800">地图位置</h3>
          <div v-if="hasCoordinates" class="mb-3 grid w-full grid-cols-3 gap-1 rounded-xl bg-gray-100 p-1 sm:inline-grid sm:w-auto">
            <button
              type="button"
              class="w-full rounded-lg px-3 py-1.5 text-center text-xs font-medium transition"
              :class="mapProvider === 'amap' ? 'bg-[#00b578] text-white shadow-sm' : 'text-gray-600 hover:bg-white'"
              @click="mapProvider = 'amap'"
            >
              高德
            </button>
            <button
              type="button"
              class="w-full rounded-lg px-3 py-1.5 text-center text-xs font-medium transition"
              :class="mapProvider === 'baidu' ? 'bg-[#2f88ff] text-white shadow-sm' : 'text-gray-600 hover:bg-white'"
              @click="mapProvider = 'baidu'"
            >
              百度
            </button>
            <button
              type="button"
              class="w-full rounded-lg px-3 py-1.5 text-center text-xs font-medium transition"
              :class="mapProvider === 'google' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-600 hover:bg-white'"
              @click="mapProvider = 'google'"
            >
              Google
            </button>
          </div>
          <div v-if="currentMapEmbedUrl" class="overflow-hidden rounded-xl border border-gray-100">
            <iframe
              :src="currentMapEmbedUrl"
              :key="mapProvider"
              class="h-64 w-full"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
            />
          </div>
          <div v-if="hasCoordinates" class="mt-3 flex justify-end">
            <a
              :href="currentMapOpenUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="rounded-lg px-3 py-1.5 text-xs font-medium text-white"
              :class="currentMapButtonClass"
            >
              {{ currentMapOpenLabel }}
            </a>
          </div>
          <p v-else class="text-sm text-gray-500">该酒店暂未配置坐标，暂时无法展示地图。</p>
        </div>

        <!-- Facilities -->
        <div v-if="hotel.facilities?.length" class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-800">设施与服务</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="f in hotel.facilities" :key="f" class="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">{{ formatFacilityLabel(f) }}</span>
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
                <img v-if="room.image_url" :src="room.image_thumb || room.image_url" :alt="room.name" class="h-full w-full object-cover" loading="lazy" decoding="async" />
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
                  <button @click="handleBook(room)" :disabled="bookingLoading === room.id" class="rounded-full bg-brand px-5 py-1.5 text-sm font-medium text-white transition hover:bg-brand-dark disabled:opacity-50">{{ bookingLoading === room.id ? '跳转中...' : '预订' }}</button>
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

    <div
      v-if="imagePreviewVisible && hotel.images?.[previewImgIndex]"
      class="fixed inset-0 z-[120] flex items-center justify-center bg-black/85 p-4"
    >
      <div class="absolute inset-0" @click="closeImagePreview" />
      <button
        type="button"
        class="absolute right-4 top-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-white/20 p-0 text-white transition hover:bg-white/30"
        @click="closeImagePreview"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true" class="h-4 w-4">
          <path d="M5 5 L15 15 M15 5 L5 15" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="2" />
        </svg>
      </button>
      <div
        class="relative z-10 flex h-full w-full items-center justify-center overflow-hidden"
        style="touch-action: none;"
        @wheel="onPreviewWheel"
        @touchstart="onPreviewTouchStart"
        @touchmove="onPreviewTouchMove"
        @touchend="onPreviewTouchEnd"
        @touchcancel="onPreviewTouchEnd"
        @click.stop
      >
        <img
          :src="hotel.images[previewImgIndex]"
          :alt="`${hotel.name} 预览图`"
          class="max-h-[88vh] max-w-[92vw] select-none rounded-lg object-contain will-change-transform"
          :style="previewImageStyle"
          draggable="false"
          @dblclick.stop="togglePreviewZoom"
        />
      </div>
      <p class="pointer-events-none absolute bottom-5 left-1/2 z-20 -translate-x-1/2 rounded-full bg-black/35 px-3 py-1 text-[11px] text-white/90 backdrop-blur">
        左右滑动切图，滚轮或双指缩放
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicApi, userFavoriteApi, getToken } from '@hotelink/api'
import { BED_TYPE_MAP, FACILITY_MAP, buildImageThumbUrl } from '@hotelink/utils'
import { useToast } from '@hotelink/ui'

const { showToast } = useToast()

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const hotel = ref<any>({})
const reviews = ref<any[]>([])
const currentImg = ref(0)
const imagePreviewVisible = ref(false)
const previewImgIndex = ref(0)
const galleryTouchStartX = ref(0)
const galleryTouchDeltaX = ref(0)
const galleryWidth = ref(1)
const galleryTouchActive = ref(false)
const galleryTouchMoved = ref(false)
const previewScale = ref(1)
const previewPanX = ref(0)
const previewPanY = ref(0)
const previewTouchStartX = ref(0)
const previewTouchStartY = ref(0)
const previewTouchDeltaX = ref(0)
const previewTouchDeltaY = ref(0)
const previewTouchActive = ref(false)
const previewPinchStartDistance = ref(0)
const previewPinchStartScale = ref(1)
const galleryAutoPlayTimer = ref<ReturnType<typeof setInterval> | null>(null)
const GALLERY_AUTO_PLAY_INTERVAL_MS = 5000
const mapProvider = ref<'amap' | 'baidu' | 'google'>('amap')
const isFav = ref(false)
const togglingFav = ref(false)
const bookingLoading = ref<number | null>(null)
const error = ref('')
const bedTypeMap = BED_TYPE_MAP

const poiName = computed(() => {
  const value = route.query.poi
  return typeof value === 'string' ? value : ''
})

const poiDistanceText = computed(() => {
  const value = route.query.distance_km
  return typeof value === 'string' ? value : ''
})

const hasCoordinates = computed(() => {
  const lat = Number(hotel.value?.latitude)
  const lng = Number(hotel.value?.longitude)
  return Number.isFinite(lat) && Number.isFinite(lng)
})

const aMapBaseParams = computed(() => {
  const lat = Number(hotel.value?.latitude)
  const lng = Number(hotel.value?.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return ''
  const name = encodeURIComponent(String(hotel.value?.name || '酒店'))
  const src = encodeURIComponent('HoteLink')
  return `position=${lng},${lat}&name=${name}&src=${src}&coordinate=gaode&callnative=0`
})

const aMapEmbedUrl = computed(() => {
  if (!aMapBaseParams.value) return ''
  return `https://uri.amap.com/marker?${aMapBaseParams.value}`
})

const aMapPageUrl = computed(() => {
  if (!aMapBaseParams.value) return '#'
  return `https://uri.amap.com/marker?${aMapBaseParams.value}`
})

const baiduMapPageUrl = computed(() => {
  const lat = Number(hotel.value?.latitude)
  const lng = Number(hotel.value?.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return '#'
  const title = encodeURIComponent(String(hotel.value?.name || '酒店'))
  const content = encodeURIComponent(String(hotel.value?.address || '酒店位置'))
  return `https://api.map.baidu.com/marker?location=${lat},${lng}&title=${title}&content=${content}&output=html`
})

const googleMapEmbedUrl = computed(() => {
  const lat = Number(hotel.value?.latitude)
  const lng = Number(hotel.value?.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return ''
  return `https://www.google.com/maps?q=${lat},${lng}&z=15&output=embed`
})

const googleMapPageUrl = computed(() => {
  const lat = Number(hotel.value?.latitude)
  const lng = Number(hotel.value?.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return '#'
  return `https://www.google.com/maps?q=${lat},${lng}`
})

const currentMapEmbedUrl = computed(() => {
  if (mapProvider.value === 'baidu') return baiduMapPageUrl.value
  if (mapProvider.value === 'google') return googleMapEmbedUrl.value
  return aMapEmbedUrl.value
})

const currentMapOpenUrl = computed(() => {
  if (mapProvider.value === 'baidu') return baiduMapPageUrl.value
  if (mapProvider.value === 'google') return googleMapPageUrl.value
  return aMapPageUrl.value
})

const currentMapOpenLabel = computed(() => {
  if (mapProvider.value === 'baidu') return '百度地图打开'
  if (mapProvider.value === 'google') return 'Google 地图打开'
  return '高德地图打开'
})

const currentMapButtonClass = computed(() => {
  if (mapProvider.value === 'baidu') return 'bg-[#2f88ff]'
  if (mapProvider.value === 'google') return 'bg-gray-800'
  return 'bg-[#00b578]'
})

const galleryTrackStyle = computed(() => {
  const baseOffsetPercent = -currentImg.value * 100
  const dragOffsetPercent = galleryTouchActive.value
    ? (galleryTouchDeltaX.value / Math.max(galleryWidth.value, 1)) * 100
    : 0
  return {
    transform: `translate3d(${baseOffsetPercent + dragOffsetPercent}%, 0, 0)`,
    transition: galleryTouchActive.value ? 'none' : 'transform 280ms ease',
  }
})

const previewImageStyle = computed(() => ({
  transform: `translate3d(${previewPanX.value}px, ${previewPanY.value}px, 0) scale(${previewScale.value})`,
  transition: previewTouchActive.value || previewPinchStartDistance.value > 0 ? 'none' : 'transform 180ms ease',
}))

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function touchDistance(a: Touch, b: Touch): number {
  const dx = a.clientX - b.clientX
  const dy = a.clientY - b.clientY
  return Math.hypot(dx, dy)
}

function stopGalleryAutoPlay() {
  if (!galleryAutoPlayTimer.value) return
  clearInterval(galleryAutoPlayTimer.value)
  galleryAutoPlayTimer.value = null
}

function startGalleryAutoPlay() {
  const total = hotel.value?.images?.length || 0
  if (imagePreviewVisible.value || total <= 1) {
    stopGalleryAutoPlay()
    return
  }
  stopGalleryAutoPlay()
  galleryAutoPlayTimer.value = setInterval(() => {
    showNextImage()
  }, GALLERY_AUTO_PLAY_INTERVAL_MS)
}

function restartGalleryAutoPlay() {
  startGalleryAutoPlay()
}

function formatRating(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(1) : '暂无'
}

function formatFacilityLabel(value: unknown): string {
  const key = String(value || '').trim()
  if (!key) return ''
  return FACILITY_MAP[key] || key.replace(/_/g, ' ')
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
      image_thumb: buildImageThumbUrl(room?.image_url || room?.image || cover || '', 256, 256) || room?.image_thumb || room?.image_url || room?.image || cover || '',
    })),
  }
}

function showPrevImage() {
  const total = hotel.value?.images?.length || 0
  if (total <= 1) return
  currentImg.value = (currentImg.value - 1 + total) % total
}

function showNextImage() {
  const total = hotel.value?.images?.length || 0
  if (total <= 1) return
  currentImg.value = (currentImg.value + 1) % total
}

function jumpToImage(index: number) {
  currentImg.value = index
  restartGalleryAutoPlay()
}

function onGalleryTouchStart(event: TouchEvent) {
  const total = hotel.value?.images?.length || 0
  if (total <= 1 || event.touches.length !== 1) return
  stopGalleryAutoPlay()
  galleryTouchStartX.value = event.touches[0].clientX
  galleryTouchDeltaX.value = 0
  galleryTouchMoved.value = false
  galleryTouchActive.value = true
  galleryWidth.value = (event.currentTarget as HTMLElement)?.clientWidth || 1
}

function onGalleryTouchMove(event: TouchEvent) {
  if (!galleryTouchActive.value || event.touches.length !== 1) return
  galleryTouchDeltaX.value = event.touches[0].clientX - galleryTouchStartX.value
  if (Math.abs(galleryTouchDeltaX.value) > 8) {
    galleryTouchMoved.value = true
  }
}

function onGalleryTouchEnd() {
  if (!galleryTouchActive.value) return
  const threshold = Math.min(110, galleryWidth.value * 0.2)
  let changed = false
  if (galleryTouchDeltaX.value > threshold) {
    showPrevImage()
    changed = true
  } else if (galleryTouchDeltaX.value < -threshold) {
    showNextImage()
    changed = true
  }
  galleryTouchDeltaX.value = 0
  galleryTouchActive.value = false
  if (changed) restartGalleryAutoPlay()
  else startGalleryAutoPlay()
}

function handleGalleryImageClick(index: number) {
  if (galleryTouchMoved.value) {
    galleryTouchMoved.value = false
    return
  }
  openImagePreview(index)
}

function resetPreviewTransform() {
  previewScale.value = 1
  previewPanX.value = 0
  previewPanY.value = 0
}

function openImagePreview(index: number) {
  const total = hotel.value?.images?.length || 0
  if (total <= 0) return
  previewImgIndex.value = index
  imagePreviewVisible.value = true
  resetPreviewTransform()
  stopGalleryAutoPlay()
}

function closeImagePreview() {
  imagePreviewVisible.value = false
  resetPreviewTransform()
  startGalleryAutoPlay()
}

function showPrevPreviewImage() {
  const total = hotel.value?.images?.length || 0
  if (total <= 1) return
  previewImgIndex.value = (previewImgIndex.value - 1 + total) % total
  currentImg.value = previewImgIndex.value
  resetPreviewTransform()
}

function showNextPreviewImage() {
  const total = hotel.value?.images?.length || 0
  if (total <= 1) return
  previewImgIndex.value = (previewImgIndex.value + 1) % total
  currentImg.value = previewImgIndex.value
  resetPreviewTransform()
}

function togglePreviewZoom() {
  if (previewScale.value > 1) {
    resetPreviewTransform()
  } else {
    previewScale.value = 2
  }
}

function onPreviewWheel(event: WheelEvent) {
  event.preventDefault()
  const step = event.deltaY < 0 ? 0.2 : -0.2
  previewScale.value = clamp(previewScale.value + step, 1, 4)
  if (previewScale.value === 1) {
    previewPanX.value = 0
    previewPanY.value = 0
  }
}

function onPreviewTouchStart(event: TouchEvent) {
  if (event.touches.length === 2) {
    previewPinchStartDistance.value = touchDistance(event.touches[0], event.touches[1])
    previewPinchStartScale.value = previewScale.value
    previewTouchActive.value = false
    return
  }
  if (event.touches.length !== 1) return
  previewTouchActive.value = true
  previewTouchStartX.value = event.touches[0].clientX
  previewTouchStartY.value = event.touches[0].clientY
  previewTouchDeltaX.value = 0
  previewTouchDeltaY.value = 0
}

function onPreviewTouchMove(event: TouchEvent) {
  if (event.touches.length === 2) {
    const distance = touchDistance(event.touches[0], event.touches[1])
    if (!previewPinchStartDistance.value) {
      previewPinchStartDistance.value = distance
      previewPinchStartScale.value = previewScale.value
      return
    }
    previewScale.value = clamp((distance / previewPinchStartDistance.value) * previewPinchStartScale.value, 1, 4)
    if (previewScale.value === 1) {
      previewPanX.value = 0
      previewPanY.value = 0
    }
    event.preventDefault()
    return
  }

  if (!previewTouchActive.value || event.touches.length !== 1) return

  const touch = event.touches[0]
  const deltaX = touch.clientX - previewTouchStartX.value
  const deltaY = touch.clientY - previewTouchStartY.value

  if (previewScale.value > 1) {
    previewPanX.value += deltaX
    previewPanY.value += deltaY
    previewTouchStartX.value = touch.clientX
    previewTouchStartY.value = touch.clientY
    event.preventDefault()
    return
  }

  previewTouchDeltaX.value = deltaX
  previewTouchDeltaY.value = deltaY
  if (Math.abs(deltaX) > Math.abs(deltaY)) {
    event.preventDefault()
  }
}

function onPreviewTouchEnd() {
  if (previewScale.value === 1 && previewTouchActive.value) {
    const threshold = 55
    if (Math.abs(previewTouchDeltaX.value) > threshold && Math.abs(previewTouchDeltaX.value) > Math.abs(previewTouchDeltaY.value)) {
      if (previewTouchDeltaX.value > 0) {
        showPrevPreviewImage()
      } else {
        showNextPreviewImage()
      }
    }
  }
  previewTouchActive.value = false
  previewTouchDeltaX.value = 0
  previewTouchDeltaY.value = 0
  previewPinchStartDistance.value = 0
}

async function checkFavStatus(hotelId: number) {
  if (!getToken()) return
  try {
    const res = await userFavoriteApi.list({ page: 1, page_size: 200 })
    if (res.code === 0 && res.data) {
      const items = (res.data as any).items || []
      isFav.value = items.some((item: any) => Number(item.hotel_id || item.hotel) === hotelId)
    }
  } catch { /* ignore */ }
}

// 切换Fav显示状态。
async function toggleFav() {
  if (togglingFav.value) return
  const hotelId = Number(route.params.id)
  if (!getToken()) {
    showToast('请先登录后再进行收藏操作', 'warning')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  if (!Number.isFinite(hotelId) || hotelId <= 0) return
  togglingFav.value = true
  try {
    if (isFav.value) {
      const res = await userFavoriteApi.remove(hotelId)
      if (res.code === 0) {
        isFav.value = false
        showToast('已取消收藏', 'success')
      } else {
        showToast(res.message || '取消收藏失败，请稍后重试', 'error')
      }
    } else {
      const res = await userFavoriteApi.add(hotelId)
      if (res.code === 0) {
        isFav.value = true
        showToast('收藏成功', 'success')
      } else {
        showToast(res.message || '收藏失败，请稍后重试', 'error')
      }
    }
  } catch {
    showToast('收藏操作失败，请检查网络后重试', 'error')
  } finally {
    togglingFav.value = false
  }
}

// 处理 Book 交互逻辑。
function handleBook(room: any) {
  if (bookingLoading.value) return
  const hotelId = Number(route.params.id)
  if (!getToken()) { router.push({ name: 'login', query: { redirect: route.fullPath } }); return }
  if (!Number.isFinite(hotelId) || hotelId <= 0) return
  bookingLoading.value = room.id
  router.push({ path: '/booking', query: { hotel_id: String(hotelId), room_type_id: String(room.id), room_name: room.name, price: String(room.base_price), hotel_name: hotel.value.name } })
  bookingLoading.value = null
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
        const total = hotel.value?.images?.length || 0
        if (currentImg.value >= total) {
          currentImg.value = 0
        }
        startGalleryAutoPlay()
        checkFavStatus(hotelId)
      } else {
        hotel.value = {}
        error.value = hotelRes.message || '酒店详情加载失败'
        stopGalleryAutoPlay()
      }
    } else {
      hotel.value = {}
      error.value = '酒店详情加载超时，请稍后重试'
      stopGalleryAutoPlay()
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
    stopGalleryAutoPlay()
  } finally {
    loading.value = false
  }
}

watch(
  () => imagePreviewVisible.value,
  (visible) => {
    if (visible) {
      stopGalleryAutoPlay()
    } else {
      startGalleryAutoPlay()
    }
  }
)

watch(
  () => hotel.value?.images?.length || 0,
  (length) => {
    if (length <= 1) {
      stopGalleryAutoPlay()
      currentImg.value = 0
      previewImgIndex.value = 0
      return
    }
    if (currentImg.value >= length) {
      currentImg.value = 0
    }
    if (previewImgIndex.value >= length) {
      previewImgIndex.value = 0
    }
    if (!imagePreviewVisible.value) {
      startGalleryAutoPlay()
    }
  }
)

watch(
  () => route.params.id,
  () => {
    const parsed = Number(route.params.id)
    if (Number.isFinite(parsed)) {
      stopGalleryAutoPlay()
      currentImg.value = 0
      galleryTouchStartX.value = 0
      galleryTouchDeltaX.value = 0
      galleryTouchMoved.value = false
      galleryTouchActive.value = false
      imagePreviewVisible.value = false
      previewImgIndex.value = 0
      resetPreviewTransform()
      previewTouchActive.value = false
      previewTouchDeltaX.value = 0
      previewTouchDeltaY.value = 0
      previewPinchStartDistance.value = 0
      loadHotelDetail()
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  stopGalleryAutoPlay()
})
</script>

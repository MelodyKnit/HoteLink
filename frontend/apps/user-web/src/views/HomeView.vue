<template>
  <div>
    <p v-if="error" class="mx-auto mt-4 max-w-5xl rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

    <!-- Hero Banner -->
    <section class="relative bg-gradient-to-br from-brand-dark via-brand to-teal-500 px-4 pb-12 pt-8 text-white md:pb-20 md:pt-16">
      <div class="mx-auto max-w-5xl">
        <h1 class="text-2xl font-bold leading-tight md:text-4xl">探索理想住处<br class="md:hidden" />开启美好旅程</h1>
        <p class="mt-2 text-sm text-teal-100 md:text-base">精选品质酒店，为您的每一次出行保驾护航</p>

        <!-- Search card -->
        <div class="mt-6 rounded-2xl bg-white p-4 shadow-xl md:mt-10 md:flex md:items-end md:gap-4 md:p-6">
          <div class="flex-1">
            <label class="mb-1 block text-xs font-medium text-gray-500">目的地 / 酒店名</label>
            <input v-model="keyword" type="text" placeholder="输入城市、商圈或酒店名" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-brand focus:ring-1 focus:ring-brand" />
          </div>
          <div class="mt-3 grid grid-cols-2 gap-3 md:mt-0 md:flex md:gap-4">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">入住日期</label>
              <input v-model="checkIn" type="date" :min="today" class="home-date-input w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-brand" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">离店日期</label>
              <input v-model="checkOut" type="date" :min="checkIn || today" class="home-date-input w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-brand" />
            </div>
          </div>
          <button type="button" @click="handleSearch" :disabled="!keyword && !checkIn" class="mt-4 w-full rounded-xl bg-brand px-8 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed md:mt-0 md:w-auto">搜索</button>
        </div>
      </div>
    </section>

    <!-- AI Signature Entry -->
    <section class="mx-auto max-w-5xl px-4 pt-5">
      <div class="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="inline-flex items-center gap-2 rounded-full bg-teal-50 px-2.5 py-1 text-[11px] font-semibold text-teal-700">
              <span class="inline-block h-1.5 w-1.5 rounded-full bg-teal-500" />
              特色功能
            </p>
            <h2 class="mt-2 text-base font-semibold text-gray-900 md:text-lg">AI 智能订房助手</h2>
            <p class="mt-1 text-xs leading-5 text-gray-500 md:text-sm">一句话即可进入“城市 → 酒店 → 房型 → 下单”流程。</p>
          </div>
          <button
            @click="goAiBooking()"
            class="shrink-0 rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-white transition hover:bg-brand-dark md:text-sm"
          >
            立即体验
          </button>
        </div>

        <div class="mt-3 flex flex-wrap gap-2">
          <button
            @click="goAiBooking('我想订酒店')"
            class="rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-600 transition hover:border-brand/40 hover:bg-brand/5 hover:text-brand"
          >
            我想订酒店
          </button>
          <button
            @click="goAiBooking('我想订上海的酒店')"
            class="rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-600 transition hover:border-brand/40 hover:bg-brand/5 hover:text-brand"
          >
            我想订上海的酒店
          </button>
          <button
            @click="goAiBooking('帮我找高评分的酒店')"
            class="rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-600 transition hover:border-brand/40 hover:bg-brand/5 hover:text-brand"
          >
            帮我找高评分的酒店
          </button>
        </div>
      </div>
    </section>

    <!-- AI Personalized Recommendations (logged-in only) -->
    <section v-if="aiRecommendations.length" class="mx-auto max-w-5xl px-4 pb-0 pt-6">
      <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="rounded-full bg-gradient-to-r from-brand to-teal-500 px-2.5 py-0.5 text-[11px] font-semibold text-white">AI 推荐</span>
          <h2 class="text-base font-bold text-gray-900">专属为您推荐</h2>
        </div>
        <button
          @click="refreshRecommendations(true)"
          :disabled="refreshingRecommendations"
          class="text-xs text-gray-400 transition hover:text-brand disabled:cursor-not-allowed disabled:text-gray-300"
        >
          {{ refreshingRecommendations ? '加载中...' : '🔄 换一批' }}
        </button>
      </div>
      <div class="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
        <router-link
          v-for="hotel in aiRecommendations"
          :key="hotel.id"
          :to="`/hotels/${hotel.id}`"
          class="group shrink-0 w-52 overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 transition hover:shadow-lg"
        >
          <div class="relative h-32 overflow-hidden bg-gray-200">
            <img v-if="hotel.cover_image" :src="hotel.cover_thumb || hotel.cover_image" :alt="hotel.name" class="h-full w-full object-cover transition group-hover:scale-105" loading="lazy" decoding="async" />
            <div v-else class="flex h-full items-center justify-center text-2xl text-gray-300">🏨</div>
            <div class="absolute right-2 top-2 rounded-full bg-white/90 px-1.5 py-0.5 text-xs font-semibold text-orange-600">¥{{ hotel.min_price }}<span class="text-gray-400 font-normal">起</span></div>
          </div>
          <div class="p-3">
            <h3 class="text-sm font-semibold text-gray-900 line-clamp-1">{{ hotel.name }}</h3>
            <p class="mt-0.5 text-[11px] text-gray-400">📍 {{ hotel.city }}</p>
            <p v-if="hotel.reason" class="mt-1 text-[10px] text-teal-600 line-clamp-2">💡 {{ hotel.reason }}</p>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Recommended Hotels -->
    <section class="mx-auto max-w-5xl px-4 py-8 md:py-12">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="text-lg font-bold text-gray-900 md:text-xl">推荐酒店</h2>
        <router-link to="/hotels" class="text-sm text-brand hover:underline">查看全部 →</router-link>
      </div>

      <div v-if="loading" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 3" :key="i" class="h-72 animate-pulse rounded-2xl bg-gray-200" />
      </div>

      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <router-link v-for="hotel in recommendedHotels" :key="hotel.id" :to="`/hotels/${hotel.id}`"
          class="group overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 transition hover:shadow-lg"
        >
          <div class="relative h-44 overflow-hidden bg-gray-200">
            <img v-if="hotel.image_url" :src="hotel.image_thumb || hotel.image_url" :alt="hotel.name" class="h-full w-full object-cover transition group-hover:scale-105" loading="lazy" decoding="async" />
            <div v-else class="flex h-full items-center justify-center text-3xl text-gray-300">🏨</div>
            <div class="absolute right-3 top-3 rounded-full bg-white/90 px-2 py-0.5 text-xs font-semibold text-orange-600">
              ¥{{ hotel.min_price }}<span class="font-normal text-gray-400">起</span>
            </div>
          </div>
          <div class="p-4">
            <div class="flex items-start justify-between">
              <h3 class="font-semibold text-gray-900 line-clamp-1">{{ hotel.name }}</h3>
              <span class="ml-2 shrink-0 text-xs text-yellow-500">{{ '★'.repeat(hotel.star) }}</span>
            </div>
            <p class="mt-1 text-xs text-gray-400 line-clamp-1">📍 {{ hotel.city }} · {{ hotel.address }}</p>
            <div class="mt-3 flex items-center gap-2">
              <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ formatRating(hotel.rating) }}</span>
              <span class="text-xs text-gray-400">{{ hotel.review_count || 0 }}条评价</span>
            </div>
            <div v-if="hotel.tags?.length" class="mt-2 flex flex-wrap gap-1">
              <span v-for="tag in hotel.tags.slice(0, 3)" :key="tag" class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">{{ tag }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Features -->
    <section class="bg-white py-10 md:py-14">
      <div class="mx-auto max-w-5xl px-4">
        <h2 class="mb-8 text-center text-lg font-bold text-gray-900 md:text-xl">为什么选择 HoteLink</h2>
        <div class="grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-8">
          <div v-for="f in features" :key="f.title" class="text-center">
            <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand/10 text-2xl">{{ f.icon }}</div>
            <p class="text-sm font-semibold text-gray-800">{{ f.title }}</p>
            <p class="mt-1 text-xs text-gray-400">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Promotions -->
    <section class="mx-auto max-w-5xl px-4 py-8 md:py-12">
      <h2 class="mb-6 text-lg font-bold text-gray-900 md:text-xl">限时优惠</h2>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div v-for="promo in promotions" :key="promo.id" class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-orange-500 to-pink-500 p-6 text-white">
          <h3 class="text-lg font-bold">{{ promo.title }}</h3>
          <p class="mt-1 text-sm text-white/80">{{ promo.desc }}</p>
          <router-link to="/hotels" class="mt-3 inline-block rounded-full bg-white/20 px-4 py-1.5 text-sm font-medium backdrop-blur transition hover:bg-white/30">立即查看</router-link>
        </div>
      </div>
    </section>

    <!-- Reviews -->
    <section class="bg-gray-50 py-10 md:py-14">
      <div class="mx-auto max-w-5xl px-4">
        <h2 class="mb-6 text-center text-lg font-bold text-gray-900 md:text-xl">住客好评</h2>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div v-for="review in previewReviews" :key="review.name" class="rounded-2xl bg-white p-5 shadow-sm">
            <div class="mb-2 text-sm text-yellow-500">{{ '★'.repeat(review.score) }}</div>
            <p class="text-sm text-gray-600 line-clamp-3">{{ review.content }}</p>
            <p class="mt-3 text-xs text-gray-400">—— {{ review.name }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { publicApi, userAiApi } from '@hotelink/api'
import { useUserAuthStore } from '@hotelink/store'
import { buildImageThumbUrl, formatDate } from '@hotelink/utils'
import { useToast } from '@hotelink/ui'

const router = useRouter()
const auth = useUserAuthStore()
const { showToast } = useToast()
const loading = ref(true)
const error = ref('')
const keyword = ref('')
const today = formatDate(new Date())
const checkIn = ref(today)
const tomorrow = new Date()
tomorrow.setDate(tomorrow.getDate() + 1)
const checkOut = ref(formatDate(tomorrow))

const recommendedHotels = ref<any[]>([])
const aiRecommendations = ref<any[]>([])
const refreshingRecommendations = ref(false)

function formatRating(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(1) : '暂无'
}

function getHomeThumbSize(scene: 'ai' | 'recommend'): { width: number; height: number } {
  const dpr = typeof window !== 'undefined' ? Math.min(2, Math.max(1, window.devicePixelRatio || 1)) : 1
  const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 1280

  if (scene === 'ai') {
    return { width: Math.round(208 * dpr), height: Math.round(128 * dpr) }
  }

  const cardWidth = viewportWidth < 640 ? 360 : (viewportWidth < 1024 ? 300 : 320)
  return { width: Math.round(cardWidth * dpr), height: Math.round(176 * dpr) }
}

function buildHomeThumb(url: string, scene: 'ai' | 'recommend'): string {
  const { width, height } = getHomeThumbSize(scene)
  return buildImageThumbUrl(url, width, height) || url
}

function mapHotel(item: any) {
  const image = item?.image_url || item?.cover_image || ''
  return {
    ...item,
    image_url: image,
    image_thumb: buildHomeThumb(image, 'recommend'),
  }
}

const features = [
  { icon: '🏆', title: '品质精选', desc: '严格筛选优质酒店' },
  { icon: '💰', title: '价格透明', desc: '无隐藏费用' },
  { icon: '🔒', title: '安全支付', desc: '多重安全保障' },
  { icon: '💬', title: 'AI 客服', desc: '7×24 智能服务' },
]

const promotions = ref([
  { id: 1, title: '新人首单立减', desc: '注册即享首单优惠，最高减 200 元' },
  { id: 2, title: '周末特惠', desc: '精选酒店周末入住低至 6 折' },
])

const previewReviews = ref([
  { name: '张先生', score: 5, content: '环境很好，设施齐全，服务态度也不错。下次一定还会选择这里。' },
  { name: '李女士', score: 5, content: '位置很方便，距离地铁站步行5分钟。房间干净整洁，早餐也很丰盛。' },
  { name: '王先生', score: 4, content: '整体不错，性价比很高。前台服务热情周到，退房流程也很便捷。' },
])

async function refreshRecommendations(showFeedback = false) {
  if (!auth.isLoggedIn) return
  refreshingRecommendations.value = true
  try {
    const res = await userAiApi.recommendations({ scene: 'home', limit: 6 })
    if (res.code === 0 && res.data) {
      aiRecommendations.value = ((res.data as any).recommendations || []).map((item: any) => ({
        ...item,
        cover_thumb: buildHomeThumb(String(item?.cover_image || ''), 'ai'),
      }))
      if (showFeedback) {
        showToast('推荐已更新', 'success')
      }
    } else if (showFeedback) {
      showToast(res.message || '刷新推荐失败，请稍后重试', 'error')
    }
  } catch {
    if (showFeedback) {
      showToast('刷新推荐失败，请检查网络后重试', 'error')
    }
  } finally {
    refreshingRecommendations.value = false
  }
}

// 处理 Search 交互逻辑。
function handleSearch() {
  const query: Record<string, string> = {}
  if (keyword.value) query.keyword = keyword.value
  if (checkIn.value) query.check_in_date = checkIn.value
  if (checkOut.value) query.check_out_date = checkOut.value
  router.push({ path: '/hotels', query })
}

function goAiBooking(question = '我想订酒店') {
  router.push({ path: '/ai-booking', query: { ask: question } })
}

onMounted(async () => {
  try {
    const res = await publicApi.home()
    if (res.code === 0 && res.data) {
      recommendedHotels.value = (res.data.recommended_hotels || []).map(mapHotel)
      if (res.data.promotions?.length) {
        promotions.value = res.data.promotions.map((p: any) => ({ ...p, desc: '' }))
      }
    } else {
      error.value = res.message || '首页数据加载失败'
    }
  } catch {
    recommendedHotels.value = []
    error.value = '首页数据加载失败，请稍后刷新重试'
  } finally {
    loading.value = false
  }
  // AI 推荐（登录用户）
  if (auth.isLoggedIn) {
    refreshRecommendations()
  }
})
</script>

<style scoped>
.home-date-input {
  -webkit-appearance: none;
  appearance: none;
  background-color: #fff;
  color-scheme: light;
}
</style>

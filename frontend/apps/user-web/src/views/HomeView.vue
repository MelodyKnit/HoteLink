<template>
  <div>
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
              <input v-model="checkIn" type="date" :min="today" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-brand" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">离店日期</label>
              <input v-model="checkOut" type="date" :min="checkIn || today" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-brand" />
            </div>
          </div>
          <button @click="handleSearch" class="mt-4 w-full rounded-xl bg-brand px-8 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark md:mt-0 md:w-auto">搜索</button>
        </div>
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
            <img v-if="hotel.image_url" :src="hotel.image_url" :alt="hotel.name" class="h-full w-full object-cover transition group-hover:scale-105" />
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
              <span class="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-semibold text-brand">{{ hotel.rating?.toFixed(1) || '暂无' }}</span>
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
import { publicApi } from '@hotelink/api'
import { formatDate } from '@hotelink/utils'

const router = useRouter()
const loading = ref(true)
const keyword = ref('')
const today = formatDate(new Date())
const checkIn = ref(today)
const tomorrow = new Date()
tomorrow.setDate(tomorrow.getDate() + 1)
const checkOut = ref(formatDate(tomorrow))

const recommendedHotels = ref<any[]>([])

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

// 处理 Search 交互逻辑。
function handleSearch() {
  const query: Record<string, string> = {}
  if (keyword.value) query.keyword = keyword.value
  if (checkIn.value) query.check_in_date = checkIn.value
  if (checkOut.value) query.check_out_date = checkOut.value
  router.push({ path: '/hotels', query })
}

onMounted(async () => {
  try {
    const res = await publicApi.home()
    if (res.code === 0 && res.data) {
      recommendedHotels.value = res.data.recommended_hotels || []
      if (res.data.promotions?.length) {
        promotions.value = res.data.promotions.map((p: any) => ({ ...p, desc: '' }))
      }
    }
  } catch {
    recommendedHotels.value = [
      { id: 1, name: 'HoteLink 北京国贸店', city: '北京', address: '朝阳区国贸 CBD', star: 5, min_price: 688, rating: 4.8, review_count: 256, image_url: '', tags: ['商务出行', '地铁直达'] },
      { id: 2, name: 'HoteLink 上海外滩店', city: '上海', address: '黄浦区外滩核心', star: 5, min_price: 888, rating: 4.9, review_count: 312, image_url: '', tags: ['江景房', '亲子友好'] },
      { id: 3, name: 'HoteLink 杭州西湖店', city: '杭州', address: '西湖景区旁', star: 4, min_price: 458, rating: 4.7, review_count: 189, image_url: '', tags: ['湖景', '温泉'] },
    ]
  } finally {
    loading.value = false
  }
})
</script>

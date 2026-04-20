<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="goBack()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">关于我们</h1>
    </header>

    <div class="mx-auto max-w-3xl px-4 py-6 pb-24 md:pb-6">
      <!-- Hero -->
      <div class="overflow-hidden rounded-2xl bg-gradient-to-br from-brand to-teal-600 p-8 text-white">
        <h2 class="text-2xl font-bold">HoteLink</h2>
        <p class="mt-2 text-lg opacity-90">连接每一段美好旅程</p>
        <p class="mt-4 text-sm leading-relaxed opacity-80">
          HoteLink 致力于为旅行者提供优质、便捷的酒店预订服务。
          我们汇聚全国精选酒店资源，以科技赋能传统酒旅行业，
          让每一位用户都能享受到智慧化的住宿体验。
        </p>
      </div>

      <!-- Values -->
      <div class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div v-for="v in values" :key="v.title" class="rounded-2xl bg-white p-5 text-center shadow-sm">
          <span class="text-3xl">{{ v.icon }}</span>
          <h3 class="mt-2 text-sm font-semibold text-gray-800">{{ v.title }}</h3>
          <p class="mt-1 text-xs text-gray-400">{{ v.desc }}</p>
        </div>
      </div>

      <!-- Story -->
      <div class="mt-6 rounded-2xl bg-white p-6 shadow-sm">
        <h3 class="text-lg font-bold text-gray-800">品牌故事</h3>
        <div class="mt-3 space-y-3 text-sm leading-relaxed text-gray-600">
          <p>
            HoteLink 诞生于对旅行美好体验的追求。我们相信，一段好的住宿体验能让整个旅程变得不同。
            从精心挑选每一家合作酒店，到持续优化预订流程，我们始终以用户体验为核心。
          </p>
          <p>
            借助 AI 智能推荐系统，我们为每位用户量身推荐最合适的酒店。
            无论是商务出差还是休闲度假，HoteLink 都能为您找到理想的住所。
          </p>
          <p>
            我们的会员体系为忠实用户提供丰厚回馈——专属折扣、延迟退房、免费升房等多重权益，
            让每一次入住都充满惊喜。
          </p>
        </div>
      </div>

      <!-- Numbers -->
      <div class="mt-6 grid grid-cols-3 gap-3">
        <div v-for="n in numbers" :key="n.label" class="rounded-2xl bg-white p-4 text-center shadow-sm">
          <p class="text-xl font-bold text-brand">{{ n.value }}</p>
          <p class="mt-1 text-xs text-gray-400">{{ n.label }}</p>
        </div>
      </div>

      <!-- Tech -->
      <div class="mt-6 rounded-2xl bg-white p-6 shadow-sm">
        <h3 class="text-lg font-bold text-gray-800">技术驱动</h3>
        <div class="mt-3 flex flex-wrap gap-2">
          <span v-for="t in techs" :key="t" class="rounded-full bg-gray-100 px-3 py-1.5 text-xs text-gray-600">{{ t }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

const values = [
  { icon: '🎯', title: '用户至上', desc: '以用户体验为核心' },
  { icon: '🔒', title: '安全可靠', desc: '保障信息与资金安全' },
  { icon: '🤖', title: '智能服务', desc: 'AI赋能智慧酒旅' },
  { icon: '💎', title: '品质严选', desc: '每一家都精心审核' },
  { icon: '🌍', title: '全国覆盖', desc: '覆盖主要城市' },
  { icon: '💬', title: '贴心客服', desc: '7×24小时在线' },
]

const numbers = [
  { value: '5,000+', label: '合作酒店' },
  { value: '100万+', label: '服务用户' },
  { value: '50+', label: '覆盖城市' },
]

const techs = [
  'Vue 3', 'Django', 'AI 智能推荐', '大数据分析', '实时房态管理',
  '智能定价', '会员体系', '多端适配', '微服务架构',
]
</script>

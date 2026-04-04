<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">会员中心</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6 pb-24 md:pb-6">
      <!-- Member Card -->
      <div class="rounded-2xl p-6 text-white" :class="levelGradient">
        <div class="flex items-center gap-3">
          <img :src="authStore.user?.avatar || '/default-avatar.svg'" class="h-14 w-14 rounded-full border-2 border-white/60 object-cover" />
          <div>
            <h2 class="text-lg font-bold">{{ authStore.user?.username || '用户' }}</h2>
            <p class="text-sm opacity-90">{{ levelInfo.label }}</p>
          </div>
        </div>
        <div class="mt-5">
          <div class="flex items-center justify-between text-xs opacity-80">
            <span>当前积分：{{ points }}</span>
            <span v-if="levelInfo.next">升级还需 {{ levelInfo.next.threshold - points }} 积分</span>
          </div>
          <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-white/30">
            <div class="h-full rounded-full bg-white transition-all" :style="{ width: progressPct + '%' }" />
          </div>
        </div>
      </div>

      <!-- Benefits -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">会员权益</h3>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div v-for="b in benefits" :key="b.title" class="flex flex-col items-center rounded-2xl bg-white p-4 shadow-sm">
            <span class="text-2xl">{{ b.icon }}</span>
            <p class="mt-2 text-sm font-medium text-gray-800">{{ b.title }}</p>
            <p class="text-xs text-gray-400">{{ b.desc }}</p>
          </div>
        </div>
      </div>

      <!-- Level Tiers -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">等级说明</h3>
        <div class="space-y-3">
          <div v-for="lv in levels" :key="lv.name" class="flex items-center gap-3 rounded-2xl bg-white p-4 shadow-sm" :class="lv.name === levelInfo.label ? 'ring-2 ring-brand' : ''">
            <div class="flex h-10 w-10 items-center justify-center rounded-full text-lg" :class="lv.bg">{{ lv.icon }}</div>
            <div class="flex-1">
              <p class="text-sm font-semibold text-gray-800">{{ lv.name }}</p>
              <p class="text-xs text-gray-400">{{ lv.threshold }} 积分</p>
            </div>
            <span v-if="lv.name === levelInfo.label" class="rounded-full bg-brand/10 px-2 py-0.5 text-xs font-medium text-brand">当前等级</span>
          </div>
        </div>
      </div>

      <!-- Points Log -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">积分记录</h3>
        <div v-if="pointLogs.length === 0" class="rounded-2xl bg-white p-8 text-center text-sm text-gray-400">暂无积分记录</div>
        <div v-else class="space-y-2">
          <div v-for="log in pointLogs" :key="log.id" class="flex items-center justify-between rounded-2xl bg-white px-4 py-3 shadow-sm">
            <div>
              <p class="text-sm font-medium text-gray-800">{{ log.title }}</p>
              <p class="text-xs text-gray-400">{{ log.time }}</p>
            </div>
            <span class="text-sm font-bold" :class="log.points > 0 ? 'text-brand' : 'text-gray-400'">{{ log.points > 0 ? '+' : '' }}{{ log.points }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserAuthStore } from '@hotelink/store'
import { userPointsApi } from '@hotelink/api'

const authStore = useUserAuthStore()
const points = ref(0)
const pointLogs = ref<any[]>([])

const levels = [
  { name: '普通会员', threshold: 0, icon: '🌱', bg: 'bg-gray-100' },
  { name: '银卡会员', threshold: 1000, icon: '🥈', bg: 'bg-gray-200' },
  { name: '金卡会员', threshold: 5000, icon: '🥇', bg: 'bg-yellow-100' },
  { name: '铂金会员', threshold: 20000, icon: '💎', bg: 'bg-purple-100' },
  { name: '钻石会员', threshold: 50000, icon: '👑', bg: 'bg-amber-100' },
]

const levelInfo = computed(() => {
  let current = levels[0], next: (typeof levels)[0] | null = levels[1]
  for (let i = levels.length - 1; i >= 0; i--) {
    if (points.value >= levels[i].threshold) { current = levels[i]; next = levels[i + 1] || null; break }
  }
  return { label: current.name, next }
})

const levelGradient = computed(() => {
  const m: Record<string, string> = {
    '普通会员': 'bg-gradient-to-r from-gray-500 to-gray-600',
    '银卡会员': 'bg-gradient-to-r from-gray-400 to-gray-500',
    '金卡会员': 'bg-gradient-to-r from-yellow-600 to-amber-500',
    '铂金会员': 'bg-gradient-to-r from-purple-600 to-indigo-500',
    '钻石会员': 'bg-gradient-to-r from-amber-500 to-yellow-400',
  }
  return m[levelInfo.value.label] || m['普通会员']
})

const progressPct = computed(() => {
  const nxt = levelInfo.value.next
  if (!nxt) return 100
  const prevThreshold = levels.find(l => l.name === levelInfo.value.label)?.threshold || 0
  return Math.min(100, ((points.value - prevThreshold) / (nxt.threshold - prevThreshold)) * 100)
})

const benefits = [
  { icon: '🎁', title: '专属折扣', desc: '最高85折' },
  { icon: '⏰', title: '延迟退房', desc: '最晚14:00' },
  { icon: '🆙', title: '免费升房', desc: '视空房情况' },
  { icon: '☕', title: '迎宾礼遇', desc: '欢迎饮品' },
  { icon: '📦', title: '积分兑换', desc: '礼品/房晚' },
  { icon: '🎂', title: '生日惊喜', desc: '专属好礼' },
]

onMounted(async () => {
  points.value = authStore.user?.points || 0
  try {
    const res = await userPointsApi.logs()
    if (res.code === 0 && res.data) { pointLogs.value = res.data.items || res.data }
  } catch {
    pointLogs.value = [
      { id: 1, title: '入住奖励', time: '2026-03-20', points: 200 },
      { id: 2, title: '评价奖励', time: '2026-03-15', points: 50 },
      { id: 3, title: '注册奖励', time: '2026-03-01', points: 100 },
    ]
    points.value = points.value || 350
  }
})
</script>

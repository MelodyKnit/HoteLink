<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">会员中心</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6 pb-24 md:pb-6">
      <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

      <!-- Member Card -->
      <div class="rounded-2xl p-6 text-white" :class="levelGradient">
        <div class="flex items-center gap-3">
          <div v-if="authStore.user?.avatar" class="h-14 w-14 overflow-hidden rounded-full border-2 border-white/60">
            <img :src="authStore.user.avatar" class="h-full w-full object-cover" @error="avatarError = true" v-show="!avatarError" />
            <div v-show="avatarError" class="flex h-full w-full items-center justify-center bg-white/20 text-xl font-bold">
              {{ userInitial }}
            </div>
          </div>
          <div v-else class="flex h-14 w-14 items-center justify-center rounded-full border-2 border-white/60 bg-white/20 text-xl font-bold">
            {{ userInitial }}
          </div>
          <div>
            <h2 class="text-lg font-bold">{{ authStore.user?.nickname || authStore.user?.username || '用户' }}</h2>
            <p class="text-sm opacity-90">{{ levelInfo.label }}</p>
          </div>
          <div class="ml-auto text-right">
            <p class="text-2xl font-bold">{{ points.toLocaleString() }}</p>
            <p class="text-xs opacity-80">积分</p>
          </div>
        </div>
        <div class="mt-5">
          <div class="flex items-center justify-between text-xs opacity-80">
            <span>{{ currentBenefitText }}</span>
            <span v-if="levelInfo.next">升级还需 {{ (levelInfo.next.threshold - points).toLocaleString() }} 积分</span>
            <span v-else>已达最高等级</span>
          </div>
          <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-white/30">
            <div class="h-full rounded-full bg-white transition-all" :style="{ width: progressPct + '%' }" />
          </div>
        </div>
      </div>

      <!-- Current Benefits -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">当前权益</h3>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div v-for="b in currentBenefits" :key="b.title" class="flex flex-col items-center rounded-2xl bg-white p-4 shadow-sm">
            <span class="text-2xl">{{ b.icon }}</span>
            <p class="mt-2 text-sm font-medium text-gray-800">{{ b.title }}</p>
            <p class="text-xs text-gray-400">{{ b.desc }}</p>
          </div>
        </div>
      </div>

      <!-- Level Tiers (clickable for preview) -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">等级说明 <span class="text-xs font-normal text-gray-400">点击查看权益</span></h3>
        <div class="space-y-3">
          <div v-for="lv in levels" :key="lv.key" @click="previewLevel = lv"
            class="flex cursor-pointer items-center gap-3 rounded-2xl bg-white p-4 shadow-sm transition hover:shadow-md"
            :class="lv.name === levelInfo.label ? 'ring-2 ring-brand' : ''">
            <div class="flex h-10 w-10 items-center justify-center rounded-full text-lg" :class="lv.bg">{{ lv.icon }}</div>
            <div class="flex-1">
              <p class="text-sm font-semibold text-gray-800">{{ lv.name }}</p>
              <p class="text-xs text-gray-400">{{ lv.threshold.toLocaleString() }} 积分 · 消费{{ lv.discountText }} · 积分{{ lv.multiplier }}x</p>
            </div>
            <span v-if="lv.name === levelInfo.label" class="rounded-full bg-brand/10 px-2 py-0.5 text-xs font-medium text-brand">当前</span>
            <span v-else class="text-xs text-gray-300">查看 ›</span>
          </div>
        </div>
      </div>

      <!-- Points Exchange -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">积分兑换</h3>
        <div class="rounded-2xl bg-white p-5 shadow-sm">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-sm text-gray-600">当前积分余额：<span class="font-bold text-brand">{{ points.toLocaleString() }}</span></p>
            <p class="text-xs text-gray-400">兑换比例 100积分 = ¥1</p>
          </div>
          <div v-if="exchangeTemplates.length === 0" class="py-6 text-center text-sm text-gray-400">暂无可兑换的优惠券</div>
          <div v-else class="space-y-3">
            <div v-for="tpl in exchangeTemplates" :key="tpl.id" class="flex items-center gap-3 rounded-xl border border-gray-100 p-3 transition hover:border-brand/30 hover:bg-brand/5">
              <div class="flex h-12 w-12 items-center justify-center rounded-lg text-white"
                :class="tpl.coupon_type === 'discount' ? 'bg-orange-500' : 'bg-brand'">
                <span class="text-xs font-bold">{{ tpl.coupon_type === 'discount' ? tpl.discount + '折' : '¥' + tpl.amount }}</span>
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">{{ tpl.name }}</p>
                <p class="text-xs text-gray-400">{{ tpl.min_amount > 0 ? `满¥${tpl.min_amount}可用` : '无门槛' }} · 剩余{{ tpl.remaining }}张</p>
              </div>
              <button @click="exchangeCoupon(tpl)" :disabled="exchanging || points < tpl.points_cost"
                class="rounded-lg px-3 py-1.5 text-xs font-medium transition"
                :class="points >= tpl.points_cost ? 'bg-brand text-white hover:bg-brand-dark' : 'bg-gray-100 text-gray-400 cursor-not-allowed'">
                {{ tpl.points_cost }} 积分兑换
              </button>
            </div>
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
              <p class="text-sm font-medium text-gray-800">{{ logTypeLabel(log.log_type) }}</p>
              <p class="text-xs text-gray-400">{{ log.description }}</p>
              <p class="text-xs text-gray-300">{{ formatTime(log.created_at) }}</p>
            </div>
            <div class="text-right">
              <span class="text-sm font-bold" :class="log.points > 0 ? 'text-brand' : 'text-orange-500'">{{ log.points > 0 ? '+' : '' }}{{ log.points }}</span>
              <p class="text-xs text-gray-300">余额 {{ log.balance }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Rules -->
      <div class="mt-6 rounded-2xl bg-white p-5 shadow-sm">
        <h3 class="mb-2 font-semibold text-gray-800">积分规则</h3>
        <ul class="space-y-1 text-xs text-gray-500">
          <li>📌 每消费 10 元获得 1 积分（受会员倍率加成）</li>
          <li>📌 评价订单额外获得 10 积分</li>
          <li>📌 积分可兑换优惠券，兑换比例 100积分 = ¥1</li>
          <li>📌 达到积分门槛自动升级，等级不会降级</li>
        </ul>
      </div>
    </div>

    <!-- Level Preview Modal -->
    <Teleport to="body">
      <div v-if="previewLevel" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" @click.self="previewLevel = null">
        <div class="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-xl">
          <div class="p-6 text-white" :class="previewLevelGradient">
            <div class="flex items-center gap-3">
              <span class="text-3xl">{{ previewLevel.icon }}</span>
              <div>
                <h3 class="text-lg font-bold">{{ previewLevel.name }}</h3>
                <p class="text-sm opacity-80">{{ previewLevel.threshold.toLocaleString() }} 积分解锁</p>
              </div>
            </div>
          </div>
          <div class="p-6">
            <h4 class="mb-3 font-semibold text-gray-800">专属权益</h4>
            <div class="grid grid-cols-2 gap-3">
              <div v-for="b in previewBenefits" :key="b.title" class="flex flex-col items-center rounded-xl bg-gray-50 p-3">
                <span class="text-xl">{{ b.icon }}</span>
                <p class="mt-1 text-xs font-medium text-gray-800">{{ b.title }}</p>
                <p class="text-xs text-gray-400">{{ b.desc }}</p>
              </div>
            </div>
            <div class="mt-4 rounded-xl bg-gray-50 p-3">
              <p class="text-xs text-gray-600">💰 消费折扣：<strong>{{ previewLevel.discountText }}</strong></p>
              <p class="mt-1 text-xs text-gray-600">⭐ 积分倍率：<strong>{{ previewLevel.multiplier }}x</strong></p>
              <p v-if="previewLevel.threshold > points" class="mt-2 text-xs text-orange-500">
                还需 {{ (previewLevel.threshold - points).toLocaleString() }} 积分即可解锁
              </p>
              <p v-else class="mt-2 text-xs text-brand">✅ 已解锁</p>
            </div>
            <button @click="previewLevel = null" class="mt-4 w-full rounded-xl bg-gray-100 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-200">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Exchange feedback toast -->
    <Teleport to="body">
      <div v-if="exchangeMsg" class="fixed bottom-20 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-gray-800 px-4 py-2 text-sm text-white shadow-lg">
        {{ exchangeMsg }}
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserAuthStore } from '@hotelink/store'
import { userPointsApi, userCouponApi } from '@hotelink/api'

const authStore = useUserAuthStore()
const points = ref(0)
const memberLevel = ref('normal')
const pointLogs = ref<any[]>([])
const error = ref('')
const avatarError = ref(false)
const previewLevel = ref<(typeof levels)[number] | null>(null)
const exchangeTemplates = ref<any[]>([])
const exchanging = ref(false)
const exchangeMsg = ref('')

const userInitial = computed(() =>
  (authStore.user?.nickname || authStore.user?.username || 'U').charAt(0).toUpperCase()
)

const levels = [
  { key: 'normal', name: '普通会员', threshold: 0, icon: '🌱', bg: 'bg-gray-100', gradient: 'bg-gradient-to-r from-gray-500 to-gray-600', discountRate: 1.00, discountText: '无折扣', multiplier: 1.0 },
  { key: 'silver', name: '银卡会员', threshold: 1000, icon: '🥈', bg: 'bg-gray-200', gradient: 'bg-gradient-to-r from-gray-400 to-gray-500', discountRate: 0.98, discountText: '98折', multiplier: 1.2 },
  { key: 'gold', name: '金卡会员', threshold: 10000, icon: '🥇', bg: 'bg-yellow-100', gradient: 'bg-gradient-to-r from-yellow-600 to-amber-500', discountRate: 0.95, discountText: '95折', multiplier: 1.5 },
  { key: 'platinum', name: '铂金会员', threshold: 100000, icon: '💎', bg: 'bg-purple-100', gradient: 'bg-gradient-to-r from-purple-600 to-indigo-500', discountRate: 0.92, discountText: '92折', multiplier: 2.0 },
  { key: 'diamond', name: '钻石会员', threshold: 1000000, icon: '👑', bg: 'bg-amber-100', gradient: 'bg-gradient-to-r from-amber-500 to-yellow-400', discountRate: 0.88, discountText: '88折', multiplier: 3.0 },
]

function getBenefitsForLevel(lv: (typeof levels)[number]) {
  const list = [
    { icon: '💰', title: '消费积分', desc: `每10元得${lv.multiplier}积分` },
    { icon: '📦', title: '积分兑券', desc: '100积分=¥1' },
  ]
  if (lv.discountRate < 1) {
    list.unshift({ icon: '🎁', title: '消费折扣', desc: `全场${lv.discountText}` })
  }
  if (lv.key === 'gold' || lv.key === 'platinum' || lv.key === 'diamond') {
    list.push({ icon: '⏰', title: '延迟退房', desc: '最晚14:00' })
  }
  if (lv.key === 'platinum' || lv.key === 'diamond') {
    list.push({ icon: '🆙', title: '免费升房', desc: '视空房情况' })
    list.push({ icon: '🎂', title: '生日惊喜', desc: '专属好礼' })
  }
  if (lv.key === 'diamond') {
    list.push({ icon: '☕', title: '迎宾礼遇', desc: '欢迎饮品' })
  }
  return list
}

const levelInfo = computed(() => {
  let current = levels[0], next: (typeof levels)[0] | null = levels[1]
  for (let i = levels.length - 1; i >= 0; i--) {
    if (points.value >= levels[i].threshold) { current = levels[i]; next = levels[i + 1] || null; break }
  }
  return { label: current.name, next, current }
})

const levelGradient = computed(() => levelInfo.value.current.gradient)

const previewLevelGradient = computed(() => previewLevel.value?.gradient || levels[0].gradient)

const previewBenefits = computed(() => previewLevel.value ? getBenefitsForLevel(previewLevel.value) : [])

const progressPct = computed(() => {
  const nxt = levelInfo.value.next
  if (!nxt) return 100
  const prevThreshold = levelInfo.value.current.threshold
  return Math.min(100, ((points.value - prevThreshold) / (nxt.threshold - prevThreshold)) * 100)
})

const currentBenefitText = computed(() => {
  const lv = levelInfo.value.current
  if (lv.discountRate >= 1) return '消费累计积分升级享专属折扣'
  return `享${lv.discountText}优惠 · ${lv.multiplier}x积分加成`
})

const currentBenefits = computed(() => getBenefitsForLevel(levelInfo.value.current))

const logTypeLabels: Record<string, string> = {
  consume_reward: '消费奖励',
  review_reward: '评价奖励',
  coupon_exchange: '积分兑券',
  admin_adjust: '积分调整',
  level_up_gift: '升级礼包',
  points_exchange: '积分兑换',
}
function logTypeLabel(type: string) { return logTypeLabels[type] || type }
function formatTime(t: string) { return t ? t.replace('T', ' ').slice(0, 19) : '' }

async function loadExchangeTemplates() {
  try {
    const res = await userCouponApi.available()
    if (res.code === 0 && res.data) {
      // 只显示需要积分的（积分兑换区）
      const all = (res.data as any).items || []
      exchangeTemplates.value = all.filter((t: any) => t.points_cost > 0)
    }
  } catch { /* ignore */ }
}

async function exchangeCoupon(tpl: any) {
  if (points.value < tpl.points_cost) {
    exchangeMsg.value = `积分不足，需要 ${tpl.points_cost} 积分`
    setTimeout(() => { exchangeMsg.value = '' }, 2000)
    return
  }
  exchanging.value = true
  exchangeMsg.value = ''
  try {
    const res = await userCouponApi.claim(tpl.id)
    if (res.code === 0) {
      exchangeMsg.value = '兑换成功！优惠券已发放到卡包'
      points.value -= tpl.points_cost
      await loadExchangeTemplates()
    } else {
      exchangeMsg.value = res.message || '兑换失败'
    }
  } catch {
    exchangeMsg.value = '网络错误'
  } finally {
    exchanging.value = false
    setTimeout(() => { exchangeMsg.value = '' }, 2500)
  }
}

onMounted(async () => {
  try {
    const res = await userPointsApi.logs()
    if (res.code === 0 && res.data) {
      const data = res.data as any
      points.value = data.current_points ?? 0
      memberLevel.value = data.member_level ?? 'normal'
      pointLogs.value = data.items || []
    }
  } catch {
    points.value = authStore.user?.points || 0
    error.value = '积分记录加载失败，请稍后重试'
  }
  await loadExchangeTemplates()
})
</script>

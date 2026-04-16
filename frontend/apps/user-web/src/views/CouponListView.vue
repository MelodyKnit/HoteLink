<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">我的优惠券</h1>
    </header>

    <!-- Tabs -->
    <div class="sticky top-14 z-30 flex gap-1 bg-white px-4 py-2">
      <button v-for="tab in tabs" :key="tab.value" @click="activeTab = tab.value"
        class="flex-1 rounded-xl py-2 text-xs font-medium transition"
        :class="activeTab === tab.value ? 'bg-brand text-white' : 'bg-gray-100 text-gray-600'">
        {{ tab.label }}
      </button>
    </div>

    <div class="mx-auto max-w-2xl px-4 py-4 pb-24 md:pb-4">
      <div v-if="loading" class="flex justify-center py-20">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
      </div>

      <!-- Claim Section -->
      <div v-if="activeTab === 'claim' && !loading">
        <div class="mb-3 flex items-center justify-between rounded-xl bg-brand/5 px-3 py-2">
          <span class="text-xs text-gray-600">我的积分：<span class="font-bold text-brand">{{ userPoints.toLocaleString() }}</span></span>
          <span class="text-xs text-gray-400">100积分 = ¥1</span>
        </div>
        <div v-if="availableTemplates.length === 0" class="py-20 text-center">
          <p class="text-4xl">🎫</p>
          <p class="mt-2 text-sm text-gray-400">暂无可领取的优惠券</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="tpl in availableTemplates" :key="tpl.id" class="flex overflow-hidden rounded-2xl bg-white shadow-sm">
            <div class="flex w-24 flex-col items-center justify-center text-white"
              :class="tpl.coupon_type === 'discount' ? 'bg-gradient-to-b from-orange-500 to-amber-500' : 'bg-gradient-to-b from-brand to-teal-500'">
              <span class="text-2xl font-bold">{{ tpl.coupon_type === 'discount' ? tpl.discount + '折' : '¥' + tpl.amount }}</span>
              <span class="text-xs opacity-80">{{ tpl.coupon_type === 'discount' ? '折扣券' : '满减券' }}</span>
            </div>
            <div class="flex flex-1 flex-col justify-center px-4 py-3">
              <p class="text-sm font-semibold text-gray-800">{{ tpl.name }}</p>
              <p class="mt-0.5 text-xs text-gray-400">{{ tpl.min_amount > 0 ? `满¥${tpl.min_amount}可用` : '无门槛' }}</p>
              <p class="mt-1 text-xs text-gray-400">
                剩余 {{ tpl.remaining }} 张
                <span v-if="tpl.points_cost > 0" class="ml-1 text-orange-500">需 {{ tpl.points_cost }} 积分</span>
                <span v-else class="ml-1 text-brand">免费领取</span>
              </p>
            </div>
            <div class="flex items-center pr-4">
              <button @click="claimCoupon(tpl)" :disabled="claimingTemplateId !== null || (tpl.points_cost > 0 && userPoints < tpl.points_cost)"
                class="rounded-lg px-3 py-1.5 text-xs font-medium transition"
                :class="(tpl.points_cost > 0 && userPoints < tpl.points_cost) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-brand text-white hover:bg-brand-dark disabled:opacity-50'">
                {{ claimingTemplateId === tpl.id ? '处理中…' : (tpl.points_cost > 0 ? (userPoints < tpl.points_cost ? '积分不足' : '兑换') : '领取') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- My Coupons -->
      <div v-if="activeTab !== 'claim' && !loading">
        <div v-if="filtered.length === 0" class="py-20 text-center">
          <p class="text-4xl">🎫</p>
          <p class="mt-2 text-sm text-gray-400">暂无{{ tabs.find(t => t.value === activeTab)?.label }}</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="c in filtered" :key="c.id"
            class="flex overflow-hidden rounded-2xl shadow-sm"
            :class="c.status === 'unused' ? 'bg-white' : 'bg-gray-100 opacity-70'">
            <div class="flex w-24 flex-col items-center justify-center text-white"
              :class="c.coupon_type === 'discount' ? 'bg-gradient-to-b from-orange-500 to-amber-500' : 'bg-gradient-to-b from-brand to-teal-500'">
              <span class="text-2xl font-bold">{{ c.coupon_type === 'discount' ? c.discount + '折' : '¥' + c.amount }}</span>
              <span class="text-xs opacity-80">{{ c.coupon_type === 'discount' ? '折扣券' : '满减券' }}</span>
            </div>
            <div class="flex flex-1 flex-col justify-center px-4 py-3">
              <p class="text-sm font-semibold text-gray-800">{{ c.name }}</p>
              <p class="mt-0.5 text-xs text-gray-400">{{ c.condition || '无门槛' }}</p>
              <p class="mt-1 text-xs text-gray-400">有效期：{{ c.valid_start }} ~ {{ c.valid_end }}</p>
            </div>
            <div class="flex items-center pr-4">
              <span v-if="c.status === 'used'" class="text-xs text-gray-400">已使用</span>
              <span v-else-if="c.status === 'expired'" class="text-xs text-gray-400">已过期</span>
              <router-link v-else to="/hotels" class="rounded-lg bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-dark">去使用</router-link>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { userCouponApi, userPointsApi } from '@hotelink/api'
import { useToast, useConfirm } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

const tabs = [
  { label: '领券中心', value: 'claim' },
  { label: '可使用', value: 'unused' },
  { label: '已使用', value: 'used' },
  { label: '已过期', value: 'expired' },
]
const activeTab = ref('claim')
const loading = ref(true)
const coupons = ref<any[]>([])
const availableTemplates = ref<any[]>([])
const claimingTemplateId = ref<number | null>(null)
const userPoints = ref(0)

const filtered = computed(() => coupons.value.filter(c => c.status === activeTab.value))

async function loadMyCoupons() {
  try {
    const res = await userCouponApi.list({ page_size: 100 })
    if (res.code === 0 && res.data) coupons.value = (res.data as any).items || []
  } catch { coupons.value = [] }
}

async function loadAvailable() {
  try {
    const res = await userCouponApi.available()
    if (res.code === 0 && res.data) availableTemplates.value = (res.data as any).items || []
  } catch { availableTemplates.value = [] }
}

async function claimCoupon(tpl: any) {
  const needPoints = Number(tpl.points_cost || 0)
  const confirmText = needPoints > 0
    ? `确认使用 ${needPoints} 积分兑换「${tpl.name}」吗？`
    : `确认领取「${tpl.name}」吗？`
  if (!await confirmDialog(confirmText)) return

  claimingTemplateId.value = Number(tpl.id)
  try {
    const res = await userCouponApi.claim(tpl.id)
    if (res.code === 0) {
      if (needPoints > 0) userPoints.value = Math.max(0, userPoints.value - needPoints)
      await loadAvailable()
      await loadMyCoupons()
      showToast(needPoints > 0 ? '兑换成功' : '领取成功', 'success')
    } else {
      showToast(res.message || '领取失败，请稍后重试', 'error')
    }
  } catch {
    showToast('网络错误，请稍后重试', 'error')
  } finally {
    claimingTemplateId.value = null
  }
}

watch(activeTab, () => {
  if (activeTab.value === 'claim') loadAvailable()
})

onMounted(async () => {
  await Promise.all([
    loadMyCoupons(),
    loadAvailable(),
    userPointsApi.logs().then(res => {
      if (res.code === 0 && res.data) userPoints.value = (res.data as any).current_points ?? 0
    }).catch(() => {}),
  ])
  loading.value = false
})
</script>

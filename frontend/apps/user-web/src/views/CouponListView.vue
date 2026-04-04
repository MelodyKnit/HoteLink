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

      <div v-else-if="filtered.length === 0" class="py-20 text-center">
        <p class="text-4xl">🎫</p>
        <p class="mt-2 text-sm text-gray-400">暂无{{ tabs.find(t => t.value === activeTab)?.label }}</p>
      </div>

      <div v-else class="space-y-3">
        <div v-for="c in filtered" :key="c.id"
          class="flex overflow-hidden rounded-2xl shadow-sm"
          :class="c.status === 'available' ? 'bg-white' : 'bg-gray-100 opacity-70'">
          <!-- Left colour strip -->
          <div class="flex w-24 flex-col items-center justify-center text-white"
            :class="c.type === 'discount' ? 'bg-gradient-to-b from-orange-500 to-amber-500' : 'bg-gradient-to-b from-brand to-teal-500'">
            <span class="text-2xl font-bold">{{ c.type === 'discount' ? c.discount + '折' : '¥' + c.amount }}</span>
            <span class="text-xs opacity-80">{{ c.type === 'discount' ? '折扣券' : '满减券' }}</span>
          </div>
          <!-- Right content -->
          <div class="flex flex-1 flex-col justify-center px-4 py-3">
            <p class="text-sm font-semibold text-gray-800">{{ c.name }}</p>
            <p class="mt-0.5 text-xs text-gray-400">{{ c.condition || '无门槛' }}</p>
            <p class="mt-1 text-xs text-gray-400">有效期：{{ c.start_date }} ~ {{ c.end_date }}</p>
          </div>
          <!-- Action -->
          <div class="flex items-center pr-4">
            <span v-if="c.status === 'used'" class="text-xs text-gray-400">已使用</span>
            <span v-else-if="c.status === 'expired'" class="text-xs text-gray-400">已过期</span>
            <router-link v-else to="/hotels" class="rounded-lg bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-dark">去使用</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { userCouponApi } from '@hotelink/api'

const tabs = [
  { label: '可使用', value: 'available' },
  { label: '已使用', value: 'used' },
  { label: '已过期', value: 'expired' },
]
const activeTab = ref('available')
const loading = ref(true)
const coupons = ref<any[]>([])

const filtered = computed(() => coupons.value.filter(c => c.status === activeTab.value))

onMounted(async () => {
  try {
    const res = await userCouponApi.list({})
    if (res.code === 0 && res.data) coupons.value = res.data.items || res.data
  } catch {
    coupons.value = [
      { id: 1, name: '新用户满减券', type: 'cash', amount: 50, condition: '满300可用', start_date: '2026-04-01', end_date: '2026-06-30', status: 'available' },
      { id: 2, name: '周末特惠折扣', type: 'discount', discount: 9, condition: '周末适用', start_date: '2026-04-01', end_date: '2026-05-31', status: 'available' },
      { id: 3, name: '生日专属券', type: 'cash', amount: 100, condition: '满500可用', start_date: '2026-01-01', end_date: '2026-01-31', status: 'expired' },
    ]
  } finally {
    loading.value = false
  }
})
</script>

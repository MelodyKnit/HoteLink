<template>
  <div class="mx-auto max-w-2xl px-4 py-6">
    <h2 class="mb-4 text-lg font-bold text-gray-900">我的订单</h2>

    <!-- Status tabs -->
    <div class="mb-4 flex gap-2 overflow-x-auto pb-2">
      <button v-for="tab in tabs" :key="tab.value" @click="currentTab = tab.value; page = 1; fetchOrders()"
        class="shrink-0 rounded-full px-4 py-1.5 text-sm transition"
        :class="currentTab === tab.value ? 'bg-brand text-white' : 'bg-white text-gray-600 ring-1 ring-gray-200 hover:bg-gray-50'"
      >{{ tab.label }}</button>
    </div>

    <!-- Orders list -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-32 animate-pulse rounded-2xl bg-gray-200" />
    </div>

    <div v-else-if="orders.length === 0" class="py-16 text-center text-gray-400">
      <p class="text-4xl">📋</p>
      <p class="mt-3 text-sm">暂无订单</p>
    </div>

    <div v-else class="space-y-3">
      <router-link v-for="order in orders" :key="order.id" :to="`/my/orders/${order.id}`"
        class="block rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-100 transition hover:shadow-md"
      >
        <div class="flex items-start justify-between">
          <div>
            <h4 class="font-semibold text-gray-800">{{ order.hotel_name || '酒店' }}</h4>
            <p class="mt-0.5 text-xs text-gray-400">{{ order.room_type_name || '房型' }}</p>
          </div>
          <span class="shrink-0 text-xs font-medium" :class="statusColor(order.status)">
            {{ statusLabel(order.status) }}
          </span>
        </div>
        <div class="mt-3 flex items-end justify-between text-sm text-gray-500">
          <div>
            <p>{{ order.check_in_date }} — {{ order.check_out_date }}</p>
            <p class="text-xs text-gray-400">订单号：{{ order.order_no }}</p>
          </div>
          <span class="text-base font-bold text-orange-600">¥{{ formatMoney(order.pay_amount || order.total_amount || order.original_amount || 0) }}</span>
        </div>
      </router-link>
    </div>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="mt-6 flex justify-center gap-2">
      <button :disabled="page <= 1" @click="page--; fetchOrders()" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">上一页</button>
      <span class="flex items-center px-3 text-sm text-gray-500">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchOrders()" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { userOrderApi } from '@hotelink/api'
import { ORDER_STATUS_MAP, formatMoney } from '@hotelink/utils'

const route = useRoute()
const loading = ref(true)
const orders = ref<any[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const currentTab = ref((route.query.status as string) || '')

const tabs = [
  { value: '', label: '全部' },
  { value: 'pending_payment', label: '待支付' },
  { value: 'confirmed', label: '待入住' },
  { value: 'checked_in', label: '入住中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
]

// 根据状态值返回对应展示信息。
function statusLabel(s: string): string { return ORDER_STATUS_MAP[s]?.label || s }
// 根据状态值返回对应展示信息。
function statusColor(s: string): string { return ORDER_STATUS_MAP[s]?.color || 'text-gray-500' }

// 加载 fetchOrders 相关数据。
async function fetchOrders() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize }
    if (currentTab.value) params.status = currentTab.value
    const res = await userOrderApi.list(params)
    if (res.code === 0 && res.data) {
      orders.value = (res.data as any).items || []
      total.value = (res.data as any).total || 0
    }
  } catch {
    orders.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(fetchOrders)
</script>

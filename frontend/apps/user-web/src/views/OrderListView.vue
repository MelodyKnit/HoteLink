<template>
  <div class="mx-auto max-w-2xl px-4 py-6">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-lg font-bold text-gray-900">我的订单</h2>
      <span class="text-xs text-gray-400">共 {{ total }} 条</span>
    </div>

    <div class="mb-4 rounded-2xl bg-white p-3 shadow-sm ring-1 ring-gray-100">
      <div class="flex gap-2">
        <input
          v-model="keyword"
          @keydown.enter="applyFilters"
          placeholder="搜索订单号 / 酒店 / 房型 / 入住人 / 手机号"
          class="min-w-0 flex-1 rounded-xl border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <button
          @click="applyFilters"
          class="shrink-0 rounded-xl bg-brand px-3 py-2 text-sm font-medium text-white transition hover:bg-brand-dark"
        >
          搜索
        </button>
      </div>
      <div class="mt-2 flex items-center justify-between">
        <button
          @click="showAdvanced = !showAdvanced"
          class="text-xs font-medium text-brand"
        >
          {{ showAdvanced ? '收起高级筛选' : '展开高级筛选' }}
        </button>
        <button
          @click="resetFilters"
          class="text-xs text-gray-500 transition hover:text-gray-700"
        >
          重置筛选
        </button>
      </div>

      <div v-if="showAdvanced" class="mt-3 space-y-3 border-t border-gray-100 pt-3">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label class="text-xs text-gray-500">
            支付状态
            <select
              v-model="paymentStatus"
              class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="">全部</option>
              <option value="unpaid">未支付</option>
              <option value="paid">已支付</option>
              <option value="failed">支付失败</option>
              <option value="refunded">已退款</option>
            </select>
          </label>
          <div class="grid grid-cols-2 gap-2">
            <label class="text-xs text-gray-500">
              最低金额
              <input
                v-model="amountMin"
                type="number"
                min="0"
                step="0.01"
                placeholder="0"
                class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
              />
            </label>
            <label class="text-xs text-gray-500">
              最高金额
              <input
                v-model="amountMax"
                type="number"
                min="0"
                step="0.01"
                placeholder="不限"
                class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
              />
            </label>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div class="grid grid-cols-2 gap-2">
            <label class="text-xs text-gray-500">
              入住开始
              <input
                v-model="checkInStart"
                type="date"
                class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
              />
            </label>
            <label class="text-xs text-gray-500">
              入住结束
              <input
                v-model="checkInEnd"
                type="date"
                class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
              />
            </label>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <label class="text-xs text-gray-500">
              下单开始
              <input
                v-model="createdStart"
                type="date"
                class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
              />
            </label>
            <label class="text-xs text-gray-500">
              下单结束
              <input
                v-model="createdEnd"
                type="date"
                class="mt-1 w-full rounded-lg border border-gray-200 px-2 py-2 text-sm outline-none focus:border-brand"
              />
            </label>
          </div>
        </div>

        <div class="flex justify-end">
          <button
            @click="applyFilters"
            class="rounded-xl border border-brand/30 bg-brand/5 px-4 py-2 text-sm font-medium text-brand transition hover:bg-brand/10"
          >
            应用高级筛选
          </button>
        </div>
      </div>
    </div>

    <!-- Status tabs -->
    <div class="mb-4 flex gap-2 overflow-x-auto pb-2">
      <button v-for="tab in tabs" :key="tab.value" @click="switchTab(tab.value)"
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
      <p class="mt-3 text-sm">暂无符合条件的订单</p>
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
          <div class="flex flex-col items-end gap-1">
            <span class="shrink-0 text-xs font-medium" :class="statusColor(order.status)">
              {{ statusLabel(order.status) }}
            </span>
            <span v-if="order.status === 'completed' && !order.has_review"
              class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              待评价
            </span>
          </div>
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
      <button :disabled="page <= 1" @click="page--; fetchOrders(true)" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">上一页</button>
      <span class="flex items-center px-3 text-sm text-gray-500">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchOrders(true)" class="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi } from '@hotelink/api'
import { ORDER_STATUS_MAP, formatMoney } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const orders = ref<any[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const currentTab = ref('')
const keyword = ref('')
const paymentStatus = ref('')
const checkInStart = ref('')
const checkInEnd = ref('')
const createdStart = ref('')
const createdEnd = ref('')
const amountMin = ref('')
const amountMax = ref('')
const showAdvanced = ref(false)

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

function readQueryValue(key: string): string {
  const value = route.query[key]
  return typeof value === 'string' ? value : ''
}

function hydrateFromQuery() {
  currentTab.value = readQueryValue('status')
  keyword.value = readQueryValue('keyword')
  paymentStatus.value = readQueryValue('payment_status')
  checkInStart.value = readQueryValue('check_in_start')
  checkInEnd.value = readQueryValue('check_in_end')
  createdStart.value = readQueryValue('created_start')
  createdEnd.value = readQueryValue('created_end')
  amountMin.value = readQueryValue('amount_min')
  amountMax.value = readQueryValue('amount_max')

  const parsedPage = Number(readQueryValue('page') || '1')
  page.value = Number.isFinite(parsedPage) && parsedPage > 0 ? Math.floor(parsedPage) : 1

  showAdvanced.value = Boolean(
    paymentStatus.value ||
    checkInStart.value ||
    checkInEnd.value ||
    createdStart.value ||
    createdEnd.value ||
    amountMin.value ||
    amountMax.value
  )
}

function buildOrderQueryParams(includePage = true): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (includePage) params.page = page.value
  if (currentTab.value) params.status = currentTab.value
  if (keyword.value.trim()) params.keyword = keyword.value.trim()
  if (paymentStatus.value) params.payment_status = paymentStatus.value
  if (checkInStart.value) params.check_in_start = checkInStart.value
  if (checkInEnd.value) params.check_in_end = checkInEnd.value
  if (createdStart.value) params.created_start = createdStart.value
  if (createdEnd.value) params.created_end = createdEnd.value
  if (amountMin.value) params.amount_min = amountMin.value
  if (amountMax.value) params.amount_max = amountMax.value
  return params
}

async function syncRouteQuery() {
  const query = buildOrderQueryParams(true)
  await router.replace({ path: '/my/orders', query })
}

// 加载 fetchOrders 相关数据。
async function fetchOrders(syncQuery = false) {
  loading.value = true
  try {
    if (syncQuery) {
      await syncRouteQuery()
    }
    const params: Record<string, unknown> = { ...buildOrderQueryParams(true), page_size: pageSize }
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

function switchTab(status: string) {
  currentTab.value = status
  page.value = 1
  fetchOrders(true)
}

function applyFilters() {
  page.value = 1
  fetchOrders(true)
}

function resetFilters() {
  currentTab.value = ''
  keyword.value = ''
  paymentStatus.value = ''
  checkInStart.value = ''
  checkInEnd.value = ''
  createdStart.value = ''
  createdEnd.value = ''
  amountMin.value = ''
  amountMax.value = ''
  showAdvanced.value = false
  page.value = 1
  fetchOrders(true)
}

onMounted(async () => {
  hydrateFromQuery()
  await fetchOrders(false)
})
</script>

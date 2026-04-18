<template>
  <section>
    <PageHeader title="入住办理" subtitle="按订单执行身份核验、房间分配与入住确认" />

    <div class="mb-4 flex flex-wrap gap-3">
      <input
        v-model="keyword"
        placeholder="订单号/手机号/入住人"
        class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500"
        @keyup.enter="loadList"
      />
      <SelectField v-model="status" size="sm" @change="onFilterChange">
        <option value="">全部状态</option>
        <option value="pending_payment">待支付</option>
        <option value="confirmed">已确认</option>
        <option value="paid">已支付</option>
        <option value="checked_in">已入住</option>
        <option value="completed">已完成</option>
        <option value="cancelled">已取消</option>
      </SelectField>
      <input
        v-model="checkInDate"
        type="date"
        class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500"
        title="入住日期筛选"
        @change="onFilterChange"
      />
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
      <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <DataTable :columns="columns" :rows="list" :loading="loading">
          <template #col-status="{ value }">
            <StatusBadge :label="ORDER_STATUS_MAP[String(value)]?.label || String(value)" :type="String(value) === 'confirmed' ? 'info' : 'warning'" />
          </template>
          <template #actions="{ row }">
            <button class="text-sm text-teal-600 hover:underline" @click="selectOrder(row)">选择</button>
          </template>
        </DataTable>
        <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="onPageChange" />
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-base font-semibold text-slate-700">办理面板</h3>
        <div v-if="!selectedOrder" class="rounded-lg border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-400">
          请先在左侧选择订单
        </div>
        <div v-else-if="!canCheckIn" class="space-y-4">
          <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <p>订单号：{{ selectedOrder.order_no }}</p>
            <p>入住人：{{ selectedOrder.guest_name }} / {{ selectedOrder.guest_mobile }}</p>
            <p>状态：{{ ORDER_STATUS_MAP[String(selectedOrder.status)]?.label || selectedOrder.status }}</p>
          </div>
          <div class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            当前订单状态不支持办理入住，仅「已支付」或「已确认」的订单可操作。
          </div>
        </div>
        <form v-else class="space-y-4" @submit.prevent="handleCheckIn">
          <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <p>订单号：{{ selectedOrder.order_no }}</p>
            <p>入住人：{{ selectedOrder.guest_name }} / {{ selectedOrder.guest_mobile }}</p>
            <p>入住日期：{{ selectedOrder.check_in_date }} → {{ selectedOrder.check_out_date }}</p>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">分配房间号</label>
            <input
              v-model="roomNo"
              required
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
              placeholder="例如：1808"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">押金记录（前端登记）</label>
            <input
              v-model.number="depositAmount"
              type="number"
              min="0"
              step="0.01"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
              placeholder="例如：500.00"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">操作备注</label>
            <textarea
              v-model="remark"
              rows="3"
              maxlength="255"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
              placeholder="证件已核验，押金收取完成"
            />
          </div>
          <button class="w-full rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting">
            {{ submitting ? '办理中…' : '确认入住' }}
          </button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { orderApi } from '@hotelink/api'
import { extractApiError, ORDER_STATUS_MAP } from '@hotelink/utils'
import { DataTable, PageHeader, Pagination, SelectField, StatusBadge, useToast } from '@hotelink/ui'
import { emitOrderSync, onOrderSync } from '../utils/order-sync'

type OrderRow = Record<string, unknown>

const { showToast } = useToast()
const route = useRoute()

const columns = [
  { key: 'order_no', label: '订单号' },
  { key: 'guest_name', label: '入住人' },
  { key: 'hotel_name', label: '酒店' },
  { key: 'room_type_name', label: '房型' },
  { key: 'check_in_date', label: '入住日' },
  { key: 'check_out_date', label: '离店日' },
  { key: 'status', label: '状态' },
]

const list = ref<OrderRow[]>([])
const loading = ref(false)
const submitting = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const status = ref('confirmed')
const checkInDate = ref(new Date().toISOString().slice(0, 10))

const selectedOrder = ref<OrderRow | null>(null)
const roomNo = ref('')
const depositAmount = ref<number>(0)
const remark = ref('')

const allowedStatuses = new Set(['pending_payment', 'paid', 'confirmed', 'checked_in', 'completed', 'cancelled'])
const checkInEligible = new Set(['paid', 'confirmed'])

const canCheckIn = computed(() => {
  if (!selectedOrder.value) return false
  return checkInEligible.has(String(selectedOrder.value.status))
})

function onPageChange(p: number) {
  page.value = p
  loadList()
}

function onFilterChange() {
  page.value = 1
  loadList()
}

function selectOrder(row: OrderRow) {
  selectedOrder.value = row
  roomNo.value = String(row.room_no || '')
  depositAmount.value = 0
  remark.value = ''
}

function syncSelectedOrderVisible() {
  if (!selectedOrder.value) return
  const selectedId = Number(selectedOrder.value.id)
  const matched = list.value.find((item) => Number(item.id) === selectedId)
  if (matched) {
    selectedOrder.value = matched
    return
  }
  list.value = [selectedOrder.value, ...list.value.filter((item) => Number(item.id) !== selectedId)]
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      page_size: pageSize.value,
      ordering: '-id',
      status: status.value,
    }
    if (keyword.value.trim()) {
      params.keyword = keyword.value.trim()
    }
    if (checkInDate.value) {
      params.check_in_date = checkInDate.value
    }
    const res = await orderApi.list(params)
    if (res.code === 0 && res.data) {
      list.value = (res.data.items || []) as OrderRow[]
      total.value = Number(res.data.total || 0)
    } else {
      showToast(extractApiError(res, '加载订单失败'), 'error')
    }
  } catch {
    showToast('加载订单失败，请重试', 'error')
  } finally {
    loading.value = false
  }
}

async function preloadOrderFromQuery() {
  const orderId = Number(route.query.order_id || 0)
  if (!orderId) return
  try {
    const res = await orderApi.detail(orderId)
    if (res.code === 0 && res.data) {
      const detail = res.data as OrderRow
      const statusValue = String(detail.status || '')
      if (allowedStatuses.has(statusValue) && status.value !== statusValue) {
        status.value = statusValue
        page.value = 1
        await loadList()
      }
      selectOrder(detail)
      syncSelectedOrderVisible()
    }
  } catch {
    // 忽略预加载失败，不影响主流程。
  }
}

async function handleCheckIn() {
  if (!selectedOrder.value) {
    showToast('请先选择订单', 'warning')
    return
  }
  if (!roomNo.value.trim()) {
    showToast('请填写房间号', 'warning')
    return
  }
  submitting.value = true
  try {
    const mergedRemark = [
      remark.value.trim(),
      depositAmount.value > 0 ? `押金登记：${depositAmount.value.toFixed(2)}` : '',
    ].filter(Boolean).join('；')
    const res = await orderApi.checkIn({
      order_id: Number(selectedOrder.value.id),
      room_no: roomNo.value.trim(),
      operator_remark: mergedRemark || undefined,
    })
    if (res.code === 0) {
      const orderId = Number(selectedOrder.value.id)
      showToast('入住办理成功', 'success')
      emitOrderSync({ action: 'check-in', orderId, source: 'admin-frontdesk-check-in' })
      selectedOrder.value = null
      roomNo.value = ''
      depositAmount.value = 0
      remark.value = ''
      await loadList()
    } else {
      showToast(extractApiError(res, '入住办理失败'), 'error')
      await loadList()
    }
  } catch {
    showToast('入住办理失败，请重试', 'error')
  } finally {
    submitting.value = false
  }
}

let cleanupSync: (() => void) | undefined

onMounted(async () => {
  await loadList()
  await preloadOrderFromQuery()
  cleanupSync = onOrderSync(() => loadList())
})

onBeforeUnmount(() => {
  cleanupSync?.()
})
</script>

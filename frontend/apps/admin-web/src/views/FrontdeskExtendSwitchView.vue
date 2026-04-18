<template>
  <section>
    <PageHeader title="续住 / 换房" subtitle="逐单完成离店日延长与房间切换，并记录操作轨迹" />

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
        <option value="checked_in">已入住</option>
        <option value="confirmed">已确认</option>
        <option value="paid">已支付</option>
        <option value="completed">已完成</option>
        <option value="cancelled">已取消</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="mb-4 inline-flex rounded-lg border border-slate-200 bg-white p-1">
      <button
        class="rounded-md px-4 py-2 text-sm transition"
        :class="tab === 'extend' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'"
        @click="tab = 'extend'"
      >续住</button>
      <button
        class="rounded-md px-4 py-2 text-sm transition"
        :class="tab === 'switch' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'"
        @click="tab = 'switch'"
      >换房</button>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
      <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <DataTable :columns="columns" :rows="list" :loading="loading">
          <template #col-status="{ value }">
            <StatusBadge :label="ORDER_STATUS_MAP[String(value)]?.label || String(value)" :type="String(value) === 'checked_in' ? 'success' : 'info'" />
          </template>
          <template #actions="{ row }">
            <button class="text-sm text-teal-600 hover:underline" @click="selectOrder(row)">选择</button>
          </template>
        </DataTable>
        <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="onPageChange" />
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-base font-semibold text-slate-700">{{ tab === 'extend' ? '续住办理' : '换房办理' }}</h3>
        <div v-if="!selectedOrder" class="rounded-lg border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-400">
          请先在左侧选择订单
        </div>

        <form v-else-if="tab === 'extend'" class="space-y-4" @submit.prevent="handleExtendStay">
          <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <p>订单号：{{ selectedOrder.order_no }}</p>
            <p>当前离店日：{{ selectedOrder.check_out_date }}</p>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">新离店日期</label>
            <input v-model="newCheckOutDate" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">操作备注</label>
            <textarea v-model="remark" rows="3" maxlength="255" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="续住原因与差价说明" />
          </div>
          <button class="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting">
            {{ submitting ? '提交中…' : '确认续住' }}
          </button>
        </form>

        <form v-else class="space-y-4" @submit.prevent="handleSwitchRoom">
          <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <p>订单号：{{ selectedOrder.order_no }}</p>
            <p>当前房间号：{{ selectedOrder.room_no || '未分配' }}</p>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">新房间号</label>
            <input v-model="newRoomNo" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="例如：1203" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">操作备注</label>
            <textarea v-model="remark" rows="3" maxlength="255" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="换房原因与差价说明" />
          </div>
          <button class="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting">
            {{ submitting ? '提交中…' : '确认换房' }}
          </button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
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
  { key: 'room_no', label: '当前房间号' },
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
const status = ref('checked_in')
const tab = ref<'extend' | 'switch'>('extend')

const selectedOrder = ref<OrderRow | null>(null)
const newCheckOutDate = ref('')
const newRoomNo = ref('')
const remark = ref('')

const allowedStatuses = new Set(['pending_payment', 'paid', 'confirmed', 'checked_in', 'completed', 'cancelled'])

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
  newCheckOutDate.value = ''
  newRoomNo.value = ''
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

async function handleExtendStay() {
  if (!selectedOrder.value) {
    showToast('请先选择订单', 'warning')
    return
  }
  if (!newCheckOutDate.value) {
    showToast('请选择新的离店日期', 'warning')
    return
  }
  submitting.value = true
  try {
    const res = await orderApi.extendStay({
      order_id: Number(selectedOrder.value.id),
      new_check_out_date: newCheckOutDate.value,
      operator_remark: remark.value.trim() || undefined,
    })
    if (res.code === 0) {
      const orderId = Number(selectedOrder.value.id)
      showToast('续住办理成功', 'success')
      emitOrderSync({ action: 'extend-stay', orderId, source: 'admin-frontdesk-extend-switch' })
      selectedOrder.value = null
      newCheckOutDate.value = ''
      remark.value = ''
      await loadList()
    } else {
      showToast(extractApiError(res, '续住办理失败'), 'error')
      await loadList()
    }
  } catch {
    showToast('续住办理失败，请重试', 'error')
  } finally {
    submitting.value = false
  }
}

async function handleSwitchRoom() {
  if (!selectedOrder.value) {
    showToast('请先选择订单', 'warning')
    return
  }
  if (!newRoomNo.value.trim()) {
    showToast('请输入新房间号', 'warning')
    return
  }
  submitting.value = true
  try {
    const res = await orderApi.switchRoom({
      order_id: Number(selectedOrder.value.id),
      new_room_no: newRoomNo.value.trim(),
      operator_remark: remark.value.trim() || undefined,
    })
    if (res.code === 0) {
      const orderId = Number(selectedOrder.value.id)
      showToast('换房办理成功', 'success')
      emitOrderSync({ action: 'switch-room', orderId, source: 'admin-frontdesk-extend-switch' })
      selectedOrder.value = null
      newRoomNo.value = ''
      remark.value = ''
      await loadList()
    } else {
      showToast(extractApiError(res, '换房办理失败'), 'error')
      await loadList()
    }
  } catch {
    showToast('换房办理失败，请重试', 'error')
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

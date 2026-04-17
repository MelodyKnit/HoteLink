<template>
  <section>
    <PageHeader title="退房结算" subtitle="按订单完成消费结算、押金处理与退房确认" />

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
        <option value="confirmed">已确认（补录）</option>
        <option value="paid">已支付（补录）</option>
        <option value="completed">已完成</option>
        <option value="cancelled">已取消</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
      <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <DataTable :columns="columns" :rows="list" :loading="loading">
          <template #col-status="{ value }">
            <StatusBadge :label="ORDER_STATUS_MAP[String(value)]?.label || String(value)" :type="String(value) === 'checked_in' ? 'success' : 'warning'" />
          </template>
          <template #col-pay_amount="{ value }">
            ¥{{ formatMoney(Number(value || 0)) }}
          </template>
          <template #actions="{ row }">
            <button class="text-sm text-teal-600 hover:underline" @click="selectOrder(row)">选择</button>
          </template>
        </DataTable>
        <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="onPageChange" />
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-base font-semibold text-slate-700">结算面板</h3>
        <div v-if="!selectedOrder" class="rounded-lg border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-400">
          请先在左侧选择订单
        </div>
        <form v-else class="space-y-4" @submit.prevent="handleCheckOut">
          <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <p>订单号：{{ selectedOrder.order_no }}</p>
            <p>入住人：{{ selectedOrder.guest_name }} / {{ selectedOrder.guest_mobile }}</p>
            <p>房费实付：¥{{ formatMoney(Number(selectedOrder.pay_amount || 0)) }}</p>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium">额外消费金额</label>
            <input
              v-model.number="consumeAmount"
              type="number"
              min="0"
              step="0.01"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium">押金抵扣（前端登记）</label>
            <input
              v-model.number="depositDeduction"
              type="number"
              min="0"
              step="0.01"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium">结算备注</label>
            <textarea
              v-model="remark"
              rows="3"
              maxlength="255"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
              placeholder="补收/退款说明、发票处理说明"
            />
          </div>

          <button class="w-full rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting">
            {{ submitting ? '结算中…' : '确认退房并结算' }}
          </button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { orderApi } from '@hotelink/api'
import { extractApiError, formatMoney, ORDER_STATUS_MAP } from '@hotelink/utils'
import { DataTable, PageHeader, Pagination, SelectField, StatusBadge, useToast } from '@hotelink/ui'
import { emitOrderSync } from '../utils/order-sync'

type OrderRow = Record<string, unknown>

const { showToast } = useToast()
const route = useRoute()

const columns = [
  { key: 'order_no', label: '订单号' },
  { key: 'guest_name', label: '入住人' },
  { key: 'hotel_name', label: '酒店' },
  { key: 'room_no', label: '房间号' },
  { key: 'check_in_date', label: '入住日' },
  { key: 'check_out_date', label: '离店日' },
  { key: 'pay_amount', label: '实付金额' },
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

const selectedOrder = ref<OrderRow | null>(null)
const consumeAmount = ref<number>(0)
const depositDeduction = ref<number>(0)
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
  consumeAmount.value = 0
  depositDeduction.value = 0
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

async function handleCheckOut() {
  if (!selectedOrder.value) {
    showToast('请先选择订单', 'warning')
    return
  }
  submitting.value = true
  try {
    const mergedRemark = [
      remark.value.trim(),
      depositDeduction.value > 0 ? `押金抵扣登记：${depositDeduction.value.toFixed(2)}` : '',
    ].filter(Boolean).join('；')
    const res = await orderApi.checkOut({
      order_id: Number(selectedOrder.value.id),
      consume_amount: consumeAmount.value,
      operator_remark: mergedRemark || undefined,
    })
    if (res.code === 0) {
      const orderId = Number(selectedOrder.value.id)
      showToast('退房结算成功', 'success')
      emitOrderSync({ action: 'check-out', orderId, source: 'admin-frontdesk-check-out' })
      selectedOrder.value = null
      consumeAmount.value = 0
      depositDeduction.value = 0
      remark.value = ''
      await loadList()
    } else {
      showToast(extractApiError(res, '退房结算失败'), 'error')
      await loadList()
    }
  } catch {
    showToast('退房结算失败，请重试', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadList()
  await preloadOrderFromQuery()
})
</script>

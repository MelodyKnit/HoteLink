<template>
  <section>
    <PageHeader title="订单管理" subtitle="查看和处理所有预订订单" />

    <div class="mb-3 flex flex-wrap items-center gap-2.5">
      <input v-model="filters.keyword" placeholder="订单号/手机号/入住人" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="loadList" />
      <SelectField v-model="filters.status" size="sm" @change="loadList">
        <option value="">全部状态</option>
        <option value="pending_payment">待支付</option>
        <option value="paid">已支付</option>
        <option value="confirmed">已确认</option>
        <option value="checked_in">已入住</option>
        <option value="completed">已完成</option>
        <option value="cancelled">已取消</option>
        <option value="refunding">退款中</option>
        <option value="refunded">已退款</option>
      </SelectField>
      <SelectField v-model="filters.ordering" size="sm" @change="onSortChange">
        <option value="-id">ID 最新优先</option>
        <option value="id">ID 最旧优先</option>
        <option value="order_no">订单号 A→Z</option>
        <option value="-order_no">订单号 Z→A</option>
        <option value="guest_name">入住人 A→Z</option>
        <option value="-guest_name">入住人 Z→A</option>
        <option value="hotel__name">酒店 A→Z</option>
        <option value="-hotel__name">酒店 Z→A</option>
        <option value="room_type__name">房型 A→Z</option>
        <option value="-room_type__name">房型 Z→A</option>
        <option value="check_in_date">入住日期升序</option>
        <option value="-check_in_date">入住日期降序</option>
        <option value="check_out_date">离店日期升序</option>
        <option value="-check_out_date">离店日期降序</option>
        <option value="pay_amount">金额从低到高</option>
        <option value="-pay_amount">金额从高到低</option>
        <option value="status">订单状态升序</option>
        <option value="-status">订单状态降序</option>
        <option value="payment_status">支付状态升序</option>
        <option value="-payment_status">支付状态降序</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading" :sort-value="filters.ordering" :compact="true" @sort-change="onTableSortChange">
        <template #col-order_no="{ value }">
          <span class="inline-block max-w-[220px] truncate align-middle" :title="String(value || '')">
            {{ value || '-' }}
          </span>
        </template>
        <template #col-hotel_name="{ value }">
          <span class="inline-block max-w-[240px] truncate align-middle" :title="String(value || '')">
            {{ value || '-' }}
          </span>
        </template>
        <template #col-room_type_name="{ value }">
          <span class="inline-block max-w-[140px] truncate align-middle" :title="String(value || '')">
            {{ value || '-' }}
          </span>
        </template>
        <template #col-status="{ value }">
          <StatusBadge :label="ORDER_STATUS_MAP[value as string]?.label || String(value)" :type="statusType(value as string)" />
        </template>
        <template #col-lifecycle_warning="{ row }">
          <router-link
            v-if="row.is_lifecycle_anomaly"
            :to="{ path: `/admin/orders/${row.id}`, query: route.query }"
            class="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-100"
            title="存在异常，请进入详情查看"
          >
            <span class="h-1.5 w-1.5 rounded-full bg-rose-500" />
            异常
          </router-link>
          <span v-else class="inline-flex items-center text-xs text-slate-300">—</span>
        </template>
        <template #col-payment_status="{ value }">
          <StatusBadge :label="PAYMENT_STATUS_MAP[value as string] || String(value)" :type="value === 'paid' ? 'success' : value === 'unpaid' ? 'warning' : 'default'" />
        </template>
        <template #col-pay_amount="{ value }">¥{{ formatMoney(value as number) }}</template>
        <template #actions="{ row }">
          <div class="relative inline-flex items-center justify-start pr-0.5">
            <div class="relative">
              <button
                class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-transparent text-slate-500 transition hover:border-slate-200 hover:bg-slate-100 hover:text-slate-700"
                :class="isActionMenuOpen(Number(row.id)) ? 'border-slate-200 bg-slate-100 text-slate-700' : ''"
                :aria-label="`展开订单 ${String(row.order_no || row.id)} 的操作菜单`"
                @click.stop="toggleActionMenu(Number(row.id))"
              >
                <span aria-hidden="true" class="text-base leading-none">⋯</span>
              </button>
              <div
                v-if="isActionMenuOpen(Number(row.id))"
                class="absolute right-0 top-full z-30 mt-2 w-44 rounded-xl border border-slate-200 bg-white/95 p-1.5 shadow-[0_10px_24px_rgba(15,23,42,0.12)] backdrop-blur-sm"
                @click.stop
              >
                <router-link
                  :to="{ path: `/admin/orders/${row.id}`, query: route.query }"
                  class="block rounded-md px-2 py-1.5 text-left text-[13px] text-slate-700 transition hover:bg-slate-100"
                  @click="closeActionMenu"
                >查看详情</router-link>
                <div class="my-1.5 h-px bg-slate-100" />
                <router-link
                  v-if="row.status === 'paid' || row.status === 'confirmed'"
                  :to="{ path: '/admin/frontdesk/check-in', query: { order_id: String(row.id) } }"
                  class="block rounded-md px-2 py-1.5 text-left text-[13px] text-teal-700 transition hover:bg-teal-50"
                  @click="closeActionMenu"
                >完整入住流程</router-link>
                <router-link
                  v-if="row.status === 'checked_in' || row.status === 'paid' || row.status === 'confirmed'"
                  :to="{ path: '/admin/frontdesk/check-out', query: { order_id: String(row.id) } }"
                  class="block rounded-md px-2 py-1.5 text-left text-[13px] text-teal-700 transition hover:bg-teal-50"
                  @click="closeActionMenu"
                >完整退房流程</router-link>
                <router-link
                  v-if="row.status === 'checked_in' || row.status === 'paid' || row.status === 'confirmed'"
                  :to="{ path: '/admin/frontdesk/extend-switch', query: { order_id: String(row.id) } }"
                  class="block rounded-md px-2 py-1.5 text-left text-[13px] text-teal-700 transition hover:bg-teal-50"
                  @click="closeActionMenu"
                >续住/换房</router-link>
                <div class="my-1.5 h-px bg-slate-100" />
                <div class="flex items-center gap-1.5 px-1 pb-0.5">
                  <button
                    v-if="row.status === 'paid'"
                    class="inline-flex h-7 flex-1 items-center justify-center rounded-md border border-indigo-200 bg-indigo-50 text-[12px] font-medium text-indigo-700 transition hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="actionOrderId === row.id"
                    @click="handleMenuConfirm(row)"
                  >确认</button>
                  <button
                    v-if="row.status === 'confirmed' || row.status === 'paid'"
                    class="inline-flex h-7 flex-1 items-center justify-center rounded-md border border-teal-200 bg-teal-50 text-[12px] font-medium text-teal-700 transition hover:bg-teal-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="actionOrderId === row.id"
                    @click="handleMenuOpenCheckIn(row)"
                  >入住</button>
                  <button
                    v-if="row.status === 'checked_in'"
                    class="inline-flex h-7 flex-1 items-center justify-center rounded-md border border-slate-200 bg-slate-100 text-[12px] font-medium text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="actionOrderId === row.id"
                    @click="handleMenuOpenCheckOut(row)"
                  >退房</button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <!-- Check-In Modal -->
    <ModalDialog :visible="showCheckIn" title="办理入住" size="sm" @close="showCheckIn = false">
      <form class="space-y-4" @submit.prevent="handleCheckIn">
        <div>
          <label class="mb-1 block text-sm font-medium">订单号</label>
          <input :value="checkInForm.order_no" disabled class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">分配房间号</label>
          <RoomSuggestInput v-model="checkInForm.room_no" :available="roomSuggestions" :occupied="occupiedRooms" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">备注</label>
          <textarea v-model="checkInForm.operator_remark" rows="2" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCheckIn = false">取消</button>
        <button class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="actionOrderId !== null" @click="handleCheckIn">{{ actionOrderId !== null ? '处理中…' : '确认入住' }}</button>
      </template>
    </ModalDialog>

    <!-- Check-Out Modal -->
    <ModalDialog :visible="showCheckOut" title="办理退房" size="sm" @close="showCheckOut = false">
      <form class="space-y-4" @submit.prevent="handleCheckOut">
        <div>
          <label class="mb-1 block text-sm font-medium">订单号</label>
          <input :value="checkOutForm.order_no" disabled class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">额外消费金额</label>
          <input v-model.number="checkOutForm.consume_amount" type="number" step="0.01" min="0" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">备注</label>
          <textarea v-model="checkOutForm.operator_remark" rows="2" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCheckOut = false">取消</button>
        <button class="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="actionOrderId !== null" @click="handleCheckOut">{{ actionOrderId !== null ? '处理中…' : '确认退房' }}</button>
      </template>
    </ModalDialog>

  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { orderApi } from '@hotelink/api'
import { formatMoney, ORDER_STATUS_MAP, PAYMENT_STATUS_MAP, extractApiError } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, RoomSuggestInput, useToast, useConfirm, SelectField } from '@hotelink/ui'
import { emitOrderSync, onOrderSync } from '../utils/order-sync'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()
const route = useRoute()

const columns = [
  { key: 'order_no', label: '订单号', sortField: 'order_no' },
  { key: 'guest_name', label: '入住人', sortField: 'guest_name' },
  { key: 'hotel_name', label: '酒店', sortField: 'hotel__name' },
  { key: 'room_type_name', label: '房型', sortField: 'room_type__name' },
  { key: 'check_in_date', label: '入住日期', sortField: 'check_in_date' },
  { key: 'check_out_date', label: '离店日期', sortField: 'check_out_date' },
  { key: 'pay_amount', label: '金额', sortField: 'pay_amount' },
  { key: 'status', label: '订单状态', sortField: 'status' },
  { key: 'lifecycle_warning', label: '异常' },
  { key: 'payment_status', label: '支付状态', sortField: 'payment_status' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ keyword: '', status: '', ordering: '-id' })

const showCheckIn = ref(false)
const checkInForm = reactive({ order_id: 0, order_no: '', room_no: '', operator_remark: '' })
const roomSuggestions = ref<string[]>([])
const occupiedRooms = ref<string[]>([])

const showCheckOut = ref(false)
const checkOutForm = reactive({ order_id: 0, order_no: '', consume_amount: 0, operator_remark: '' })
const actionOrderId = ref<number | null>(null)
const activeActionMenuId = ref<number | null>(null)
let stopOrderSync: (() => void) | null = null

function toggleActionMenu(orderId: number) {
  activeActionMenuId.value = activeActionMenuId.value === orderId ? null : orderId
}

function closeActionMenu() {
  activeActionMenuId.value = null
}

function isActionMenuOpen(orderId: number) {
  return activeActionMenuId.value === orderId
}

function handleMenuConfirm(row: Record<string, unknown>) {
  closeActionMenu()
  return confirmOrder(row)
}

function handleMenuOpenCheckIn(row: Record<string, unknown>) {
  closeActionMenu()
  openCheckIn(row)
}

function handleMenuOpenCheckOut(row: Record<string, unknown>) {
  closeActionMenu()
  openCheckOut(row)
}

function patchOrderRow(orderId: number, patch: Record<string, unknown>) {
  const nextStatus = String(patch.status || '')
  if (filters.status && nextStatus && filters.status !== nextStatus) {
    list.value = list.value.filter((item) => Number(item.id) !== orderId)
    total.value = Math.max(0, total.value - 1)
    return
  }
  list.value = list.value.map((item) => (Number(item.id) === orderId ? { ...item, ...patch } : item))
}

// 根据状态值返回对应展示信息。
function statusType(status: string) {
  if (status === 'checked_in' || status === 'completed') return 'success' as const
  if (status === 'cancelled' || status === 'refunded') return 'danger' as const
  if (status === 'pending_payment') return 'warning' as const
  if (status === 'refunding') return 'warning' as const
  return 'info' as const
}

function onSortChange() {
  page.value = 1
  loadList()
}

function onTableSortChange(ordering: string) {
  if (filters.ordering === ordering) return
  filters.ordering = ordering
  onSortChange()
}

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value, ordering: filters.ordering }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    const res = await orderApi.list(params)
    if (res.code === 0 && res.data) {
      list.value = (res.data as unknown as { items: Record<string, unknown>[] }).items || []
      total.value = (res.data as unknown as { total: number }).total || 0
    } else {
      showToast(res.message || '加载订单列表失败', 'error')
    }
  } catch {
    showToast('加载订单列表失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

// 处理 confirmOrder 业务流程。
async function confirmOrder(row: Record<string, unknown>) {
  if (actionOrderId.value !== null) return
  if (!await confirmDialog('确认此订单？')) return
  actionOrderId.value = row.id as number
  try {
    const res = await orderApi.changeStatus({ order_id: row.id as number, target_status: 'confirmed' })
    if (res.code === 0) {
      showToast('订单已确认', 'success')
      patchOrderRow(row.id as number, { status: 'confirmed' })
      emitOrderSync({ action: 'change-status', orderId: Number(row.id), source: 'admin-order-list' })
    } else {
      showToast(extractApiError(res, '确认订单失败'), 'error')
    }
  } catch {
    showToast('确认订单失败，请重试', 'error')
  } finally {
    actionOrderId.value = null
  }
}

// 打开 CheckIn 相关界面。
function openCheckIn(row: Record<string, unknown>) {
  checkInForm.order_id = row.id as number
  checkInForm.order_no = row.order_no as string
  checkInForm.room_no = ''
  checkInForm.operator_remark = ''
  showCheckIn.value = true
  fetchRoomSuggestions(row)
}

async function fetchRoomSuggestions(row: Record<string, unknown>) {
  const hotelId = Number(row.hotel_id || row.hotel || 0)
  if (!hotelId) return
  try {
    const res = await orderApi.roomSuggestions({
      hotel_id: hotelId,
      check_in: String(row.check_in_date || ''),
      check_out: String(row.check_out_date || ''),
    })
    if (res.code === 0 && res.data) {
      roomSuggestions.value = res.data.available || []
      occupiedRooms.value = res.data.occupied || []
    }
  } catch {
    roomSuggestions.value = []
    occupiedRooms.value = []
  }
}

// 处理 CheckIn 交互逻辑。
async function handleCheckIn() {
  if (actionOrderId.value !== null) return
  if (!checkInForm.room_no.trim()) {
    showToast('请填写房间号', 'error')
    return
  }
  actionOrderId.value = checkInForm.order_id
  try {
    const res = await orderApi.checkIn({
      order_id: checkInForm.order_id,
      room_no: checkInForm.room_no,
      operator_remark: checkInForm.operator_remark,
    })
    if (res.code === 0) {
      showToast('入住办理成功', 'success')
      showCheckIn.value = false
      patchOrderRow(checkInForm.order_id, { room_no: checkInForm.room_no, status: 'checked_in' })
      emitOrderSync({ action: 'check-in', orderId: checkInForm.order_id, source: 'admin-order-list' })
    } else {
      showToast(extractApiError(res, '入住办理失败'), 'error')
    }
  } catch {
    showToast('入住办理失败，请重试', 'error')
  } finally {
    actionOrderId.value = null
  }
}

// 打开 CheckOut 相关界面。
function openCheckOut(row: Record<string, unknown>) {
  checkOutForm.order_id = row.id as number
  checkOutForm.order_no = row.order_no as string
  checkOutForm.consume_amount = 0
  checkOutForm.operator_remark = ''
  showCheckOut.value = true
}

// 处理 CheckOut 交互逻辑。
async function handleCheckOut() {
  if (actionOrderId.value !== null) return
  actionOrderId.value = checkOutForm.order_id
  try {
    const res = await orderApi.checkOut({
      order_id: checkOutForm.order_id,
      consume_amount: checkOutForm.consume_amount,
      operator_remark: checkOutForm.operator_remark,
    })
    if (res.code === 0) {
      showToast('退房办理成功', 'success')
      showCheckOut.value = false
      patchOrderRow(checkOutForm.order_id, { status: 'completed' })
      emitOrderSync({ action: 'check-out', orderId: checkOutForm.order_id, source: 'admin-order-list' })
    } else {
      showToast(extractApiError(res, '退房办理失败'), 'error')
    }
  } catch {
    showToast('退房办理失败，请重试', 'error')
  } finally {
    actionOrderId.value = null
  }
}

onMounted(() => {
  loadList()
  window.addEventListener('click', closeActionMenu)
  stopOrderSync = onOrderSync((payload) => {
    if (payload.action === 'refresh' || payload.action === 'change-status' || payload.action === 'check-in' || payload.action === 'check-out' || payload.action === 'extend-stay' || payload.action === 'switch-room') {
      loadList()
    }
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeActionMenu)
  if (stopOrderSync) {
    stopOrderSync()
    stopOrderSync = null
  }
})
</script>

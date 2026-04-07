<template>
  <section>
    <PageHeader title="订单管理" subtitle="查看和处理所有预订订单" />

    <div class="mb-4 flex flex-wrap gap-3">
      <input v-model="filters.keyword" placeholder="订单号/手机号/入住人" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="loadList" />
      <SelectField v-model="filters.status" size="sm" @change="loadList">
        <option value="">全部状态</option>
        <option value="pending_payment">待支付</option>
        <option value="paid">已支付</option>
        <option value="confirmed">已确认</option>
        <option value="checked_in">已入住</option>
        <option value="completed">已完成</option>
        <option value="cancelled">已取消</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-status="{ value }">
          <StatusBadge :label="ORDER_STATUS_MAP[value as string]?.label || String(value)" :type="statusType(value as string)" />
        </template>
        <template #col-payment_status="{ value }">
          <StatusBadge :label="PAYMENT_STATUS_MAP[value as string] || String(value)" :type="value === 'paid' ? 'success' : value === 'unpaid' ? 'warning' : 'default'" />
        </template>
        <template #col-pay_amount="{ value }">¥{{ formatMoney(value as number) }}</template>
        <template #actions="{ row }">
          <div class="flex flex-wrap gap-2">
            <router-link :to="`/admin/orders/${row.id}`" class="text-sm text-teal-600 hover:underline">详情</router-link>
            <button v-if="row.status === 'paid'" class="text-sm text-indigo-600 hover:underline" @click="confirmOrder(row)">确认</button>
            <button v-if="row.status === 'confirmed' || row.status === 'paid'" class="text-sm text-green-600 hover:underline" @click="openCheckIn(row)">入住</button>
            <button v-if="row.status === 'checked_in'" class="text-sm text-orange-600 hover:underline" @click="openCheckOut(row)">退房</button>
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
          <input v-model="checkInForm.room_no" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="例如：1808" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">备注</label>
          <textarea v-model="checkInForm.operator_remark" rows="2" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCheckIn = false">取消</button>
        <button class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700" @click="handleCheckIn">确认入住</button>
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
        <button class="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700" @click="handleCheckOut">确认退房</button>
      </template>
    </ModalDialog>

    <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" @close="closeToast" />
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { orderApi } from '@hotelink/api'
import { formatMoney, ORDER_STATUS_MAP, PAYMENT_STATUS_MAP, extractApiError } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, Toast, useToast, SelectField } from '@hotelink/ui'

const { toastVisible, toastMessage, toastType, showToast, closeToast } = useToast()

const columns = [
  { key: 'order_no', label: '订单号' },
  { key: 'guest_name', label: '入住人' },
  { key: 'hotel_name', label: '酒店' },
  { key: 'room_type_name', label: '房型' },
  { key: 'check_in_date', label: '入住日期' },
  { key: 'check_out_date', label: '离店日期' },
  { key: 'pay_amount', label: '金额' },
  { key: 'status', label: '订单状态' },
  { key: 'payment_status', label: '支付状态' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ keyword: '', status: '' })

const showCheckIn = ref(false)
const checkInForm = reactive({ order_id: 0, order_no: '', room_no: '', operator_remark: '' })

const showCheckOut = ref(false)
const checkOutForm = reactive({ order_id: 0, order_no: '', consume_amount: 0, operator_remark: '' })

// 根据状态值返回对应展示信息。
function statusType(status: string) {
  if (status === 'checked_in' || status === 'completed') return 'success' as const
  if (status === 'cancelled') return 'danger' as const
  if (status === 'pending_payment') return 'warning' as const
  return 'info' as const
}

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
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
  if (!confirm('确认此订单？')) return
  try {
    const res = await orderApi.changeStatus({ order_id: row.id as number, target_status: 'confirmed' })
    if (res.code === 0) {
      showToast('订单已确认', 'success')
      loadList()
    } else {
      showToast(extractApiError(res, '确认订单失败'), 'error')
    }
  } catch {
    showToast('确认订单失败，请重试', 'error')
  }
}

// 打开 CheckIn 相关界面。
function openCheckIn(row: Record<string, unknown>) {
  checkInForm.order_id = row.id as number
  checkInForm.order_no = row.order_no as string
  checkInForm.room_no = ''
  checkInForm.operator_remark = ''
  showCheckIn.value = true
}

// 处理 CheckIn 交互逻辑。
async function handleCheckIn() {
  if (!checkInForm.room_no.trim()) {
    showToast('请填写房间号', 'error')
    return
  }
  try {
    const res = await orderApi.checkIn({
      order_id: checkInForm.order_id,
      room_no: checkInForm.room_no,
      operator_remark: checkInForm.operator_remark,
    })
    if (res.code === 0) {
      showToast('入住办理成功', 'success')
      showCheckIn.value = false
      loadList()
    } else {
      showToast(extractApiError(res, '入住办理失败'), 'error')
    }
  } catch {
    showToast('入住办理失败，请重试', 'error')
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
  try {
    const res = await orderApi.checkOut({
      order_id: checkOutForm.order_id,
      consume_amount: checkOutForm.consume_amount,
      operator_remark: checkOutForm.operator_remark,
    })
    if (res.code === 0) {
      showToast('退房办理成功', 'success')
      showCheckOut.value = false
      loadList()
    } else {
      showToast(extractApiError(res, '退房办理失败'), 'error')
    }
  } catch {
    showToast('退房办理失败，请重试', 'error')
  }
}

onMounted(loadList)
</script>

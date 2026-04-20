<template>
  <section>
    <div class="mb-4 flex items-center justify-between gap-3">
      <router-link :to="{ path: '/admin/orders', query: route.query }" class="text-sm text-teal-600 hover:underline">&larr; 返回订单列表</router-link>
      <span v-if="refreshing && order" class="text-xs text-slate-400">正在更新订单信息…</span>
    </div>

    <div v-if="loading && !order" class="text-center py-20 text-slate-400">加载中…</div>

    <template v-else-if="order">
      <PageHeader :title="`订单 ${order.order_no}`">
        <template #actions>
          <StatusBadge :label="ORDER_STATUS_MAP[order.status as string]?.label || String(order.status)" :type="statusType(order.status as string)" />
        </template>
      </PageHeader>

      <!-- 订单状态流转 -->
      <div class="mb-6 rounded-2xl bg-white px-6 py-5 shadow-sm ring-1 ring-slate-200">
        <p class="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-400">订单进度</p>
        <OrderStepBar :status="order.status as string" :timestamps="orderTimestamps" />
      </div>

      <div class="mb-6 grid gap-4 xl:grid-cols-3">
        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 xl:col-span-2">
          <div class="mb-4 flex items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-slate-700">状态摘要</h3>
            <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500">当前状态：{{ ORDER_STATUS_MAP[order.status as string]?.label || String(order.status) }}</span>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div class="rounded-xl bg-slate-50 px-4 py-3">
              <p class="text-xs text-slate-400">房间号</p>
              <p class="mt-1 text-sm font-semibold text-slate-800">{{ order.room_no || '未分配' }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 px-4 py-3">
              <p class="text-xs text-slate-400">入住日期</p>
              <p class="mt-1 text-sm font-semibold text-slate-800">{{ order.check_in_date }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 px-4 py-3">
              <p class="text-xs text-slate-400">离店日期</p>
              <p class="mt-1 text-sm font-semibold text-slate-800">{{ order.check_out_date }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 px-4 py-3">
              <p class="text-xs text-slate-400">支付状态</p>
              <p class="mt-1 text-sm font-semibold text-slate-800">{{ PAYMENT_STATUS_MAP[order.payment_status as string] || String(order.payment_status) }}</p>
            </div>
          </div>
          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <div class="rounded-xl border border-slate-200 bg-white px-4 py-3">
              <p class="text-xs text-slate-400">异常提示</p>
              <div v-if="lifecycleWarningText" class="mt-1 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm leading-6 text-rose-700">
                {{ lifecycleWarningText }}
              </div>
              <p v-else class="mt-1 text-sm text-slate-400">无异常</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white px-4 py-3">
              <p class="text-xs text-slate-400">本次变更</p>
              <div v-if="operatorRemarkItems.length" class="mt-2 space-y-1.5">
                <div v-for="(item, index) in operatorRemarkItems" :key="index" class="rounded-lg bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700">
                  {{ item }}
                </div>
              </div>
              <p v-else class="mt-1 text-sm text-slate-400">暂无操作记录</p>
            </div>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h3 class="text-sm font-semibold text-slate-700">订单定位</h3>
          <dl class="mt-4 space-y-3 text-sm">
            <div class="flex justify-between gap-4"><dt class="text-slate-400">订单号</dt><dd class="text-right">{{ order.order_no }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-slate-400">酒店</dt><dd class="text-right">{{ order.hotel_name }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-slate-400">房型</dt><dd class="text-right">{{ order.room_type_name }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-slate-400">下单时间</dt><dd class="text-right">{{ formatDateTime(order.created_at as string) }}</dd></div>
          </dl>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <!-- 订单基本信息 -->
        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-4 text-sm font-semibold text-slate-500">订单信息</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">订单号</dt><dd>{{ order.order_no }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">酒店</dt><dd>{{ order.hotel_name }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">房型</dt><dd>{{ order.room_type_name }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">房间号</dt><dd>{{ order.room_no || '-' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">入住日期</dt><dd>{{ order.check_in_date }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">离店日期</dt><dd>{{ order.check_out_date }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">下单时间</dt><dd>{{ formatDateTime(order.created_at as string) }}</dd></div>
          </dl>
        </div>

        <!-- 入住人信息 -->
        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-4 text-sm font-semibold text-slate-500">入住人信息</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">姓名</dt><dd>{{ order.guest_name }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">手机号</dt><dd>{{ order.guest_mobile }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">入住人数</dt><dd>{{ order.guest_count }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">客户备注</dt><dd>{{ order.remark || '-' }}</dd></div>
          </dl>
        </div>

        <!-- 费用明细 -->
        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-4 text-sm font-semibold text-slate-500">费用明细</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">原价</dt><dd>¥{{ formatMoney(order.original_amount as number) }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">优惠</dt><dd class="text-red-500">-¥{{ formatMoney(order.discount_amount as number) }}</dd></div>
            <div class="flex justify-between font-semibold"><dt class="text-slate-600">实付</dt><dd class="text-teal-700">¥{{ formatMoney(order.pay_amount as number) }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">支付状态</dt><dd><StatusBadge :label="PAYMENT_STATUS_MAP[order.payment_status as string] || String(order.payment_status)" :type="order.payment_status === 'paid' ? 'success' : order.payment_status === 'refunded' ? 'danger' : order.payment_status === 'refunding' ? 'warning' : 'warning'" /></dd></div>
          </dl>
        </div>

        <!-- 支付记录 -->
        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-4 text-sm font-semibold text-slate-500">支付记录</h3>
          <div v-if="payments.length === 0" class="text-sm text-slate-400">暂无支付记录</div>
          <div v-else class="space-y-3">
            <div v-for="p in payments" :key="p.id" class="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 text-sm">
              <div>
                <div class="font-medium">{{ p.payment_no }}</div>
                <div class="text-xs text-slate-400">{{ PAYMENT_METHOD_MAP[p.method as string] || p.method }} · {{ formatDateTime(p.paid_at as string || p.created_at as string) }}</div>
              </div>
              <div class="font-semibold">¥{{ formatMoney(p.amount as number) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="mt-6 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p class="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">流程入口</p>
          <div class="flex flex-wrap gap-3">
            <router-link
              v-if="order.status === 'paid' || order.status === 'confirmed'"
              :to="{ path: '/admin/frontdesk/check-in', query: { order_id: String(order.id) } }"
              class="rounded-lg border border-cyan-200 bg-cyan-50 px-4 py-2 text-sm font-medium text-cyan-700 transition hover:bg-cyan-100"
            >进入完整入住流程</router-link>
            <router-link
              v-if="order.status === 'checked_in' || order.status === 'paid' || order.status === 'confirmed'"
              :to="{ path: '/admin/frontdesk/check-out', query: { order_id: String(order.id) } }"
              class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 transition hover:bg-amber-100"
            >进入完整退房流程</router-link>
            <router-link
              v-if="order.status === 'checked_in' || order.status === 'paid' || order.status === 'confirmed'"
              :to="{ path: '/admin/frontdesk/extend-switch', query: { order_id: String(order.id) } }"
              class="rounded-lg border border-violet-200 bg-violet-50 px-4 py-2 text-sm font-medium text-violet-700 transition hover:bg-violet-100"
            >进入续住/换房流程</router-link>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p class="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">订单处理</p>
          <div class="flex flex-wrap gap-3">
            <button
              v-if="canCancelOrder"
              class="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="actionLoading"
              @click="openCancel"
            >
              {{ actionLoading ? '处理中…' : '取消订单' }}
            </button>
            <button
              v-if="order.status === 'paid'"
              class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="actionLoading"
              @click="confirmOrder"
            >
              {{ actionLoading ? '处理中…' : '确认订单' }}
            </button>
            <button
              v-if="order.status === 'confirmed' || order.status === 'paid'"
              class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="actionLoading"
              @click="openCheckIn"
            >
              {{ actionLoading ? '处理中…' : '办理入住' }}
            </button>
            <button
              v-if="order.status === 'checked_in'"
              class="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="actionLoading"
              @click="doCheckOut"
            >
              {{ actionLoading ? '处理中…' : '办理退房' }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="text-center py-20 text-slate-400">订单未找到</div>
  </section>

  <!-- Cancel Modal -->
  <ModalDialog :visible="showCancelModal" title="取消订单" size="sm" @close="showCancelModal = false">
    <div class="space-y-4">
      <p class="text-sm text-slate-500">请输入取消原因，便于后续追踪。</p>
      <div>
        <label class="mb-1 block text-sm font-medium">取消原因</label>
        <textarea v-model="cancelReason" rows="3" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-rose-500" placeholder="例如：客户临时改期 / 重复下单 / 联系不上客户" />
      </div>
    </div>
    <template #footer>
      <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCancelModal = false">取消</button>
      <button
        class="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="actionLoading"
        @click="submitCancel"
      >
        {{ actionLoading ? '取消中…' : '确认取消' }}
      </button>
    </template>
  </ModalDialog>

  <!-- Check-in Modal -->
  <ModalDialog :visible="showCheckInModal" title="办理入住" size="sm" @close="showCheckInModal = false">
    <div class="space-y-4">
      <p class="text-sm text-slate-500">请确认并输入该客户分配的房间号。</p>
      <div>
        <label class="mb-1 block text-sm font-medium">房间号</label>
        <RoomSuggestInput v-model="checkInRoomNo" :available="roomSuggestions" :occupied="occupiedRooms" placeholder="如 301" />
      </div>
    </div>
    <template #footer>
      <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCheckInModal = false">取消</button>
      <button
        class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="actionLoading"
        @click="submitCheckIn"
      >
        {{ actionLoading ? '办理中…' : '确认入住' }}
      </button>
    </template>
  </ModalDialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { orderApi } from '@hotelink/api'
import { formatMoney, formatDateTime, ORDER_STATUS_MAP, PAYMENT_STATUS_MAP, PAYMENT_METHOD_MAP } from '@hotelink/utils'
import { PageHeader, StatusBadge, ModalDialog, OrderStepBar, RoomSuggestInput, useToast, useConfirm } from '@hotelink/ui'
import { emitOrderSync, onOrderSync } from '../utils/order-sync'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

interface PaymentItem {
  id: number
  payment_no: string
  method: string
  paid_at?: string
  created_at?: string
  amount: number
}

const route = useRoute()

const showCheckInModal = ref(false)
const checkInRoomNo = ref('')
const roomSuggestions = ref<string[]>([])
const occupiedRooms = ref<string[]>([])
const showCancelModal = ref(false)
const cancelReason = ref('')
const actionLoading = ref(false)

const loading = ref(true)
const refreshing = ref(false)
const order = ref<Record<string, unknown> | null>(null)
const payments = ref<PaymentItem[]>([])
let stopOrderSync: (() => void) | null = null

// 用于订单进度条的时间戳映射
const orderTimestamps = computed<Record<string, string | undefined>>(() => ({
  pending_payment: order.value?.created_at as string | undefined,
  paid:            order.value?.paid_at as string | undefined,
  confirmed:       order.value?.confirmed_at as string | undefined,
  checked_in:      order.value?.checked_in_at as string | undefined,
  completed:       order.value?.completed_at as string | undefined,
  cancelled:       order.value?.cancelled_at as string | undefined,
}))

const lifecycleWarningText = computed(() => {
  const warning = String(order.value?.lifecycle_warning || '').trim()
  return warning
})

const operatorRemarkItems = computed(() => {
  const remark = String(order.value?.operator_remark || '').trim()
  if (!remark) return []
  return remark
    .split(/[；;\n]+/)
    .map((item) => item.trim())
    .filter(Boolean)
})

// 根据状态值返回对应展示信息。
function statusType(status: string) {
  if (status === 'checked_in' || status === 'completed') return 'success' as const
  if (status === 'cancelled' || status === 'refunded') return 'danger' as const
  if (status === 'pending_payment' || status === 'refunding') return 'warning' as const
  return 'info' as const
}

const canCancelOrder = computed(() => !!order.value && !['checked_in', 'completed', 'cancelled', 'refunded'].includes(String(order.value.status)))

// 加载 Detail 相关数据。
async function loadDetail(silent = false) {
  const shouldShowSkeleton = !silent || !order.value
  if (shouldShowSkeleton) {
    loading.value = true
  } else {
    refreshing.value = true
  }
  const id = Number(route.params.id)
  try {
    const res = await orderApi.detail(id)
    if (res.code === 0 && res.data) {
      const detail = res.data as Record<string, unknown>
      order.value = detail
      payments.value = Array.isArray((detail as { payments?: unknown[] }).payments)
        ? ((detail as { payments?: PaymentItem[] }).payments || [])
        : []
    } else if (!silent || !order.value) {
      order.value = null
      payments.value = []
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 处理 confirmOrder 业务流程。
async function confirmOrder() {
  if (actionLoading.value) return
  if (!await confirmDialog('确认此订单？', { type: 'warning' })) return
  actionLoading.value = true
  try {
    const res = await orderApi.changeStatus({ order_id: order.value!.id as number, target_status: 'confirmed' })
    if (res.code === 0) {
      showToast('订单已确认', 'success')
      emitOrderSync({ action: 'change-status', orderId: Number(order.value!.id), source: 'admin-order-detail' })
      loadDetail(true)
    } else {
      showToast(res.message || '确认失败', 'error')
    }
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

function openCancel() {
  cancelReason.value = ''
  showCancelModal.value = true
}

async function submitCancel() {
  if (actionLoading.value) return
  actionLoading.value = true
  try {
    const res = await orderApi.changeStatus({
      order_id: order.value!.id as number,
      target_status: 'cancelled',
      operator_remark: cancelReason.value.trim(),
    })
    if (res.code === 0) {
      showToast('订单已取消', 'success')
      emitOrderSync({ action: 'change-status', orderId: Number(order.value!.id), source: 'admin-order-detail' })
      showCancelModal.value = false
      loadDetail(true)
    } else {
      showToast(res.message || '取消失败', 'error')
    }
  } catch {
    showToast('取消失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

// 打开办理入住弹窗。
function openCheckIn() {
  checkInRoomNo.value = ''
  showCheckInModal.value = true
  fetchRoomSuggestions()
}

async function fetchRoomSuggestions() {
  if (!order.value) return
  const hotelId = Number(order.value.hotel_id || order.value.hotel || 0)
  if (!hotelId) return
  try {
    const res = await orderApi.roomSuggestions({
      hotel_id: hotelId,
      check_in: String(order.value.check_in_date || ''),
      check_out: String(order.value.check_out_date || ''),
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

// 提交入住并办理。
async function submitCheckIn() {
  if (actionLoading.value) return
  if (!checkInRoomNo.value.trim()) {
    showToast('请输入房间号', 'warning')
    return
  }
  actionLoading.value = true
  try {
    const res = await orderApi.checkIn({ order_id: order.value!.id as number, room_no: checkInRoomNo.value.trim() })
    if (res.code === 0) {
      showToast('入住办理成功', 'success')
      showCheckInModal.value = false
      emitOrderSync({ action: 'check-in', orderId: Number(order.value!.id), source: 'admin-order-detail' })
      loadDetail(true)
    } else {
      showToast(res.message || '办理入住失败', 'error')
    }
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

// 处理 doCheckOut 业务流程。
async function doCheckOut() {
  if (actionLoading.value) return
  if (!await confirmDialog('确认办理退房？', { type: 'warning' })) return
  actionLoading.value = true
  try {
    const res = await orderApi.checkOut({ order_id: order.value!.id as number })
    if (res.code === 0) {
      showToast('退房办理成功', 'success')
      emitOrderSync({ action: 'check-out', orderId: Number(order.value!.id), source: 'admin-order-detail' })
      loadDetail(true)
    } else {
      showToast(res.message || '办理退房失败', 'error')
    }
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

onMounted(loadDetail)

onMounted(() => {
  stopOrderSync = onOrderSync((payload) => {
    if (payload.orderId && Number(payload.orderId) === Number(route.params.id)) {
      loadDetail(true)
    }
  })
})

onBeforeUnmount(() => {
  if (stopOrderSync) {
    stopOrderSync()
    stopOrderSync = null
  }
})
</script>

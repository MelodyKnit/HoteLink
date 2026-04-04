<template>
  <section>
    <div class="mb-4">
      <router-link to="/admin/orders" class="text-sm text-teal-600 hover:underline">&larr; 返回订单列表</router-link>
    </div>

    <div v-if="loading" class="text-center py-20 text-slate-400">加载中…</div>

    <template v-else-if="order">
      <PageHeader :title="`订单 ${order.order_no}`">
        <template #actions>
          <StatusBadge :label="ORDER_STATUS_MAP[order.status as string]?.label || String(order.status)" :type="statusType(order.status as string)" />
        </template>
      </PageHeader>

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
            <div class="flex justify-between"><dt class="text-slate-400">操作备注</dt><dd>{{ order.operator_remark || '-' }}</dd></div>
          </dl>
        </div>

        <!-- 费用明细 -->
        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-4 text-sm font-semibold text-slate-500">费用明细</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">原价</dt><dd>¥{{ formatMoney(order.original_amount as number) }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">优惠</dt><dd class="text-red-500">-¥{{ formatMoney(order.discount_amount as number) }}</dd></div>
            <div class="flex justify-between font-semibold"><dt class="text-slate-600">实付</dt><dd class="text-teal-700">¥{{ formatMoney(order.pay_amount as number) }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">支付状态</dt><dd><StatusBadge :label="PAYMENT_STATUS_MAP[order.payment_status as string] || String(order.payment_status)" :type="order.payment_status === 'paid' ? 'success' : 'warning'" /></dd></div>
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
      <div class="mt-6 flex flex-wrap gap-3">
        <button v-if="order.status === 'paid'" class="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700" @click="confirmOrder">确认订单</button>
        <button v-if="order.status === 'confirmed' || order.status === 'paid'" class="rounded-lg bg-green-600 px-5 py-2 text-sm font-medium text-white hover:bg-green-700" @click="doCheckIn">办理入住</button>
        <button v-if="order.status === 'checked_in'" class="rounded-lg bg-orange-600 px-5 py-2 text-sm font-medium text-white hover:bg-orange-700" @click="doCheckOut">办理退房</button>
      </div>
    </template>

    <div v-else class="text-center py-20 text-slate-400">订单未找到</div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { orderApi } from '@hotelink/api'
import { formatMoney, formatDateTime, ORDER_STATUS_MAP, PAYMENT_STATUS_MAP, PAYMENT_METHOD_MAP } from '@hotelink/utils'
import { PageHeader, StatusBadge } from '@hotelink/ui'

const route = useRoute()

const loading = ref(true)
const order = ref<Record<string, unknown> | null>(null)
const payments = ref<Record<string, unknown>[]>([])

function statusType(status: string) {
  if (status === 'checked_in' || status === 'completed') return 'success' as const
  if (status === 'cancelled') return 'danger' as const
  if (status === 'pending_payment') return 'warning' as const
  return 'info' as const
}

async function loadDetail() {
  loading.value = true
  const id = Number(route.params.id)
  const res = await orderApi.detail(id)
  if (res.code === 0 && res.data) {
    order.value = res.data as Record<string, unknown>
  }
  loading.value = false
}

async function confirmOrder() {
  if (!confirm('确认此订单？')) return
  await orderApi.changeStatus({ order_id: order.value!.id as number, target_status: 'confirmed' })
  loadDetail()
}

async function doCheckIn() {
  const roomNo = prompt('请输入房间号')
  if (!roomNo) return
  await orderApi.checkIn({ order_id: order.value!.id as number, room_no: roomNo })
  loadDetail()
}

async function doCheckOut() {
  await orderApi.checkOut({ order_id: order.value!.id as number })
  loadDetail()
}

onMounted(loadDetail)
</script>

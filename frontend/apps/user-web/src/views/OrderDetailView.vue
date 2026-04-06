<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">订单详情</h1>
    </header>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
    </div>

    <div v-else class="mx-auto max-w-2xl px-4 py-6">
      <!-- Status -->
      <div class="rounded-2xl bg-gradient-to-r from-brand to-teal-500 p-5 text-white">
        <p class="text-sm text-teal-100">订单状态</p>
        <h2 class="mt-1 text-xl font-bold">{{ statusLabel(order.status) }}</h2>
        <p class="mt-1 text-xs text-teal-200">订单号：{{ order.order_no }}</p>
      </div>

      <!-- Hotel & Room -->
      <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h3 class="font-semibold text-gray-800">{{ order.hotel_name }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ order.room_type_name }}</p>
        <div class="mt-3 grid grid-cols-2 gap-3 text-sm text-gray-600">
          <div>
            <p class="text-xs text-gray-400">入住日期</p>
            <p class="font-medium">{{ order.check_in_date }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400">离店日期</p>
            <p class="font-medium">{{ order.check_out_date }}</p>
          </div>
        </div>
        <div v-if="order.room_no" class="mt-2 text-sm text-gray-600">
          <span class="text-xs text-gray-400">房间号：</span>{{ order.room_no }}
        </div>
      </div>

      <!-- Guest Info -->
      <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h4 class="mb-2 font-semibold text-gray-800">入住人信息</h4>
        <div class="space-y-1 text-sm text-gray-600">
          <p>姓名：{{ order.guest_name }}</p>
          <p>手机：{{ order.guest_mobile }}</p>
          <p v-if="order.guest_count">人数：{{ order.guest_count }}人</p>
          <p v-if="order.remark">备注：{{ order.remark }}</p>
        </div>
      </div>

      <!-- Payment -->
      <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h4 class="mb-2 font-semibold text-gray-800">费用信息</h4>
        <div class="flex items-end justify-between">
          <div class="text-sm text-gray-600">
            <p>支付方式：{{ paymentMethodMap[order.payment_method] || order.payment_method || '待支付' }}</p>
            <p>支付状态：{{ paymentStatusMap[order.payment_status] || order.payment_status || '-' }}</p>
          </div>
          <span class="text-xl font-bold text-orange-600">¥{{ order.total_amount || '0.00' }}</span>
        </div>
      </div>

      <!-- Timeline -->
      <div v-if="order.timeline?.length" class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h4 class="mb-3 font-semibold text-gray-800">订单时间线</h4>
        <div class="space-y-3">
          <div v-for="(item, i) in order.timeline" :key="i" class="flex gap-3">
            <div class="flex flex-col items-center">
              <div class="h-2.5 w-2.5 rounded-full" :class="i === 0 ? 'bg-brand' : 'bg-gray-300'" />
              <div v-if="i < order.timeline.length - 1" class="h-full w-px bg-gray-200" />
            </div>
            <div class="pb-3">
              <p class="text-sm font-medium text-gray-800">{{ item.title }}</p>
              <p class="text-xs text-gray-400">{{ item.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="sticky bottom-16 mt-6 flex gap-3 md:bottom-0">
        <button v-if="order.status === 'pending_payment'" @click="goToPay"
          class="flex-1 rounded-2xl bg-brand py-3 text-center text-sm font-semibold text-white hover:bg-brand-dark">去支付</button>
        <button v-if="canCancel" @click="showCancelModal = true"
          class="flex-1 rounded-2xl border border-red-200 py-3 text-center text-sm font-medium text-red-500 hover:bg-red-50">取消订单</button>
        <button v-if="order.status === 'completed' && !order.has_review" @click="showReviewModal = true"
          class="flex-1 rounded-2xl bg-brand py-3 text-center text-sm font-semibold text-white hover:bg-brand-dark">评价</button>
        <router-link v-if="order.hotel_id" :to="`/hotels/${order.hotel_id}`"
          class="flex-1 rounded-2xl border border-gray-200 py-3 text-center text-sm font-medium text-gray-600 hover:bg-gray-50">再次预订</router-link>
      </div>
    </div>

    <!-- Cancel modal -->
    <Teleport to="body">
      <div v-if="showCancelModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showCancelModal = false">
        <div class="w-full max-w-sm rounded-2xl bg-white p-6">
          <h3 class="text-lg font-bold text-gray-900">取消订单</h3>
          <textarea v-model="cancelReason" rows="3" placeholder="请输入取消原因" class="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <div class="mt-4 flex gap-3">
            <button @click="showCancelModal = false" class="flex-1 rounded-xl border py-2.5 text-sm text-gray-600 hover:bg-gray-50">取消</button>
            <button @click="handleCancel" :disabled="cancelling" class="flex-1 rounded-xl bg-red-500 py-2.5 text-sm text-white hover:bg-red-600 disabled:opacity-50">确认取消</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Review modal -->
    <Teleport to="body">
      <div v-if="showReviewModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showReviewModal = false">
        <div class="w-full max-w-sm rounded-2xl bg-white p-6">
          <h3 class="text-lg font-bold text-gray-900">评价订单</h3>
          <div class="mt-3">
            <p class="mb-1 text-sm text-gray-500">评分</p>
            <div class="flex gap-2">
              <button v-for="s in 5" :key="s" @click="reviewScore = s"
                class="text-2xl transition" :class="s <= reviewScore ? 'text-yellow-500' : 'text-gray-300'">★</button>
            </div>
          </div>
          <textarea v-model="reviewContent" rows="3" placeholder="分享您的入住体验..." class="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <div class="mt-4 flex gap-3">
            <button @click="showReviewModal = false" class="flex-1 rounded-xl border py-2.5 text-sm text-gray-600">取消</button>
            <button @click="handleReview" :disabled="reviewing" class="flex-1 rounded-xl bg-brand py-2.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50">提交评价</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi, userReviewApi } from '@hotelink/api'
import { ORDER_STATUS_MAP, PAYMENT_METHOD_MAP, PAYMENT_STATUS_MAP } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.id)
const loading = ref(true)
const order = ref<any>({})

const showCancelModal = ref(false)
const cancelReason = ref('')
const cancelling = ref(false)

const showReviewModal = ref(false)
const reviewScore = ref(5)
const reviewContent = ref('')
const reviewing = ref(false)

const paymentMethodMap = PAYMENT_METHOD_MAP
const paymentStatusMap = PAYMENT_STATUS_MAP

// 根据状态值返回对应展示信息。
function statusLabel(s: string): string { return ORDER_STATUS_MAP[s]?.label || s || '未知' }
const canCancel = computed(() => ['pending_payment', 'paid', 'confirmed'].includes(order.value.status))

// 处理 goToPay 业务流程。
function goToPay() { router.push(`/payment/${orderId}`) }

// 处理 Cancel 交互逻辑。
async function handleCancel() {
  cancelling.value = true
  try {
    const res = await userOrderApi.cancel({ order_id: orderId, reason: cancelReason.value || '用户取消' })
    if (res.code === 0) {
      order.value.status = 'cancelled'
      showCancelModal.value = false
    }
  } catch { /* ignore */ }
  cancelling.value = false
}

// 处理 Review 交互逻辑。
async function handleReview() {
  if (!reviewContent.value.trim()) return
  reviewing.value = true
  try {
    const res = await userReviewApi.create({ order_id: orderId, score: reviewScore.value, content: reviewContent.value })
    if (res.code === 0) {
      order.value.has_review = true
      showReviewModal.value = false
    }
  } catch { /* ignore */ }
  reviewing.value = false
}

onMounted(async () => {
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) order.value = res.data
  } catch {
    order.value = {
      id: orderId, order_no: `ORD${orderId}`, status: 'confirmed',
      hotel_name: '示例酒店', hotel_id: 1, room_type_name: '豪华大床房',
      check_in_date: '2026-04-10', check_out_date: '2026-04-12',
      guest_name: '张三', guest_mobile: '138****0000', guest_count: 2,
      total_amount: '1376.00', payment_method: 'mock', payment_status: 'paid',
      timeline: [
        { title: '订单已确认', time: '2026-04-08 16:30' },
        { title: '支付成功', time: '2026-04-08 16:25' },
        { title: '订单已创建', time: '2026-04-08 16:20' },
      ],
    }
  } finally {
    loading.value = false
  }
})
</script>

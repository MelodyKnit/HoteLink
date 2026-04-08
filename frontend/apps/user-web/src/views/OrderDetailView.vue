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
      <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

      <!-- Status -->
      <div class="rounded-2xl bg-gradient-to-r from-brand to-teal-500 p-5 text-white">
        <p class="text-sm text-teal-100">订单状态</p>
        <h2 class="mt-1 text-xl font-bold">{{ statusLabel(order.status) }}</h2>
        <p class="mt-1 text-xs text-teal-200">订单号：{{ order.order_no }}</p>
      </div>

      <!-- 订单进度条 -->
      <div class="mt-3 rounded-2xl bg-white p-5 shadow-sm">
        <OrderStepBar :status="order.status" :timestamps="{
          pending_payment: order.created_at,
          paid: order.paid_at,
          confirmed: order.confirmed_at,
          checked_in: order.checked_in_at,
          completed: order.completed_at,
          cancelled: order.cancelled_at,
        }" />
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
          <span class="text-xl font-bold text-orange-600">¥{{ formatMoney(order.pay_amount || order.total_amount || order.original_amount || 0) }}</span>
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
        <router-link v-if="order.hotel_id || order.hotel" :to="`/hotels/${order.hotel_id || order.hotel}`"
          class="flex-1 rounded-2xl border border-gray-200 py-3 text-center text-sm font-medium text-gray-600 hover:bg-gray-50">再次预订</router-link>
      </div>
    </div>

    <!-- 评价成功积分提示 -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-300" enter-from-class="opacity-0 translate-y-2" leave-active-class="transition duration-300" leave-to-class="opacity-0 translate-y-2">
        <div v-if="reviewSuccessMsg" class="fixed bottom-24 left-1/2 z-[60] -translate-x-1/2 rounded-full bg-green-600 px-5 py-2 text-sm text-white shadow-lg">
          {{ reviewSuccessMsg }}
        </div>
      </Transition>
    </Teleport>

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
        <div class="w-full max-w-md rounded-2xl bg-white p-6 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-bold text-gray-900">评价入住体验</h3>
          <p class="mt-0.5 text-xs text-gray-400">{{ order.hotel_name }}</p>

          <!-- 星级评分 -->
          <div class="mt-4">
            <p class="mb-1.5 text-sm font-medium text-gray-700">总体评分</p>
            <div class="flex gap-1">
              <button v-for="s in 5" :key="s" type="button" @click="reviewScore = s"
                class="text-3xl leading-none transition-transform hover:scale-110"
                :class="s <= reviewScore ? 'text-yellow-400' : 'text-gray-200'">&#9733;</button>
              <span class="ml-2 self-center text-sm text-gray-500">{{ ['','很差','较差','一般','不错','很好'][reviewScore] }}</span>
            </div>
          </div>

          <!-- 评价内容 -->
          <div class="mt-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-700">评价内容</p>
              <span class="text-xs" :class="reviewCharCount >= 100 ? 'text-green-600 font-medium' : reviewCharCount >= 50 ? 'text-brand font-medium' : 'text-gray-400'">
                {{ reviewCharCount }}字
                <span v-if="reviewCharCount < 50">（50字起）</span>
              </span>
            </div>
            <textarea v-model="reviewContent" rows="4" maxlength="500"
              placeholder="分享您的入住体验，50字以上可获得积分奖励…"
              class="mt-1.5 w-full resize-none rounded-xl border border-gray-200 px-3 py-2.5 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
            <div class="mt-1 flex items-center justify-between">
              <div class="h-1 flex-1 overflow-hidden rounded-full bg-gray-100">
                <div class="h-full rounded-full transition-all duration-300"
                  :class="reviewCharCount >= 100 ? 'bg-green-500' : reviewCharCount >= 50 ? 'bg-brand' : 'bg-gray-300'"
                  :style="{ width: Math.min(reviewCharCount / 500 * 100, 100) + '%' }" />
              </div>
              <span class="ml-2 text-xs text-gray-400">{{ reviewCharCount }}/500</span>
            </div>
          </div>

          <!-- 图片上传 -->
          <div class="mt-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-700">上传图片 <span class="font-normal text-gray-400">（选填）</span></p>
              <span class="text-xs text-gray-400">{{ reviewImages.length }}/9</span>
            </div>
            <div class="mt-2 flex flex-wrap gap-2">
              <div v-for="(img, idx) in reviewImages" :key="idx" class="group relative h-20 w-20 overflow-hidden rounded-xl">
                <img :src="img" class="h-full w-full object-cover" />
                <button type="button" @click="removeReviewImage(idx)"
                  class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition group-hover:opacity-100">
                  <span class="text-xl text-white">×</span>
                </button>
              </div>
              <label v-if="reviewImages.length < 9"
                class="flex h-20 w-20 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-gray-200 text-gray-400 transition hover:border-brand hover:text-brand"
                :class="uploadingImage ? 'opacity-50 pointer-events-none' : ''">
                <span class="text-2xl">{{ uploadingImage ? '…' : '+' }}</span>
                <span class="text-xs">添加图片</span>
                <input type="file" accept="image/*" multiple class="hidden" :disabled="uploadingImage" @change="handleReviewImageUpload" />
              </label>
            </div>
          </div>

          <!-- 积分预览 -->
          <div class="mt-4 rounded-xl bg-teal-50 px-3 py-2.5 text-xs text-teal-700">
            <p class="font-medium">可获积分：<span class="text-base font-bold text-brand">+{{ reviewPointsPreview }}</span> 分</p>
            <p class="mt-0.5 text-teal-600/70">50字→5分 · +图片→7分 · 100字+图片→10分（首次评价可奖励）</p>
          </div>

          <div class="mt-5 flex gap-3">
            <button type="button" @click="showReviewModal = false" class="flex-1 rounded-xl border border-gray-200 py-2.5 text-sm text-gray-600 hover:bg-gray-50">取消</button>
            <button type="button" @click="handleReview" :disabled="reviewing || !reviewContent.trim()"
              class="flex-1 rounded-xl bg-brand py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-40">
              {{ reviewing ? '提交中…' : '提交评价' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi, userReviewApi, commonApi } from '@hotelink/api'
import { ORDER_STATUS_MAP, PAYMENT_METHOD_MAP, PAYMENT_STATUS_MAP, formatMoney } from '@hotelink/utils'
import { OrderStepBar } from '@hotelink/ui'

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.id)
const loading = ref(true)
const order = ref<any>({})
const error = ref('')

const showCancelModal = ref(false)
const cancelReason = ref('')
const cancelling = ref(false)

const showReviewModal = ref(false)
const reviewScore = ref(5)
const reviewContent = ref('')
const reviewImages = ref<string[]>([])
const reviewing = ref(false)
const uploadingImage = ref(false)
const reviewSuccessMsg = ref('')

const reviewCharCount = computed(() => reviewContent.value.trim().length)
const reviewPointsPreview = computed(() => {
  const len = reviewCharCount.value
  const hasImg = reviewImages.value.length > 0
  if (len >= 100 && hasImg) return 10
  if (len >= 50 && hasImg) return 7
  if (len >= 50) return 5
  return 0
})

const paymentMethodMap = PAYMENT_METHOD_MAP
const paymentStatusMap = PAYMENT_STATUS_MAP

// 根据状态值返回对应展示信息。
function statusLabel(s: string): string { return ORDER_STATUS_MAP[s]?.label || s || '未知' }
const canCancel = computed(() => ['pending_payment', 'paid', 'confirmed'].includes(order.value.status))

// 处理 goToPay 业务流程。
function goToPay() { router.push(`/payment/${orderId}`) }

async function handleReviewImageUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length) return
  uploadingImage.value = true
  try {
    for (const file of Array.from(files)) {
      if (reviewImages.value.length >= 9) break
      const res = await commonApi.upload(file, 'review')
      if (res.code === 0 && res.data) reviewImages.value.push((res.data as any).file_url as string)
    }
  } catch { /* ignore */ }
  uploadingImage.value = false
  ;(e.target as HTMLInputElement).value = ''
}

function removeReviewImage(idx: number) { reviewImages.value.splice(idx, 1) }

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
    const res = await userReviewApi.create({
      order_id: orderId,
      score: reviewScore.value,
      content: reviewContent.value,
      images: reviewImages.value,
    })
    if (res.code === 0) {
      order.value.has_review = true
      showReviewModal.value = false
      reviewImages.value = []
      const pts = (res.data as any)?.points_awarded ?? 0
      if (pts > 0) {
        reviewSuccessMsg.value = `评价成功！奖励 +${pts} 积分`
        setTimeout(() => { reviewSuccessMsg.value = '' }, 4000)
      }
    }
  } catch { /* ignore */ }
  reviewing.value = false
}

onMounted(async () => {
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) {
      order.value = res.data
    } else {
      order.value = {}
      error.value = res.message || '订单详情加载失败，请稍后重试'
    }
  } catch {
    order.value = {}
    error.value = '订单详情加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
})
</script>

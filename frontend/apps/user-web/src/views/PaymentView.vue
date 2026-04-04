<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">订单支付</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6">
      <div v-if="loading" class="flex justify-center py-20">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
      </div>

      <template v-else>
        <!-- Order summary -->
        <div class="rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="font-semibold text-gray-800">订单信息</h3>
          <div class="mt-3 space-y-2 text-sm text-gray-600">
            <p>订单号：{{ order.order_no || orderId }}</p>
            <p>酒店：{{ order.hotel_name || '-' }}</p>
            <p>房型：{{ order.room_type_name || '-' }}</p>
            <p>入住：{{ order.check_in_date }} — {{ order.check_out_date }}</p>
            <p>入住人：{{ order.guest_name }}</p>
          </div>
        </div>

        <!-- Payment method -->
        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-800">支付方式</h3>
          <div class="space-y-2">
            <label v-for="m in methods" :key="m.value"
              class="flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition"
              :class="payMethod === m.value ? 'border-brand bg-brand/5' : 'border-gray-200'"
            >
              <input type="radio" :value="m.value" v-model="payMethod" class="accent-brand" />
              <span class="text-xl">{{ m.icon }}</span>
              <span class="text-sm">{{ m.label }}</span>
            </label>
          </div>
        </div>

        <!-- Amount -->
        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <div class="flex items-end justify-between">
            <span class="text-sm text-gray-500">应付金额</span>
            <span class="text-2xl font-bold text-orange-600">¥{{ order.total_amount || '0.00' }}</span>
          </div>
        </div>

        <!-- Countdown -->
        <p v-if="countdown > 0" class="mt-3 text-center text-xs text-gray-400">
          请在 <span class="font-semibold text-orange-600">{{ Math.floor(countdown / 60) }}:{{ String(countdown % 60).padStart(2, '0') }}</span> 内完成支付
        </p>

        <!-- Pay button -->
        <div class="sticky bottom-16 mt-6 md:bottom-0">
          <button @click="handlePay" :disabled="paying" class="w-full rounded-2xl bg-brand py-3.5 text-center text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
            {{ paying ? '支付中...' : `确认支付 ¥${order.total_amount || '0.00'}` }}
          </button>
        </div>

        <p v-if="error" class="mt-3 text-center text-sm text-red-500">{{ error }}</p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi } from '@hotelink/api'

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.orderId)
const loading = ref(true)
const paying = ref(false)
const error = ref('')
const order = ref<any>({})
const payMethod = ref('mock')
const countdown = ref(900) // 15 min
let timer: ReturnType<typeof setInterval>

const methods = [
  { value: 'mock', icon: '💳', label: '模拟支付（演示）' },
  { value: 'wechat', icon: '💚', label: '微信支付' },
  { value: 'alipay', icon: '🔵', label: '支付宝' },
]

async function handlePay() {
  paying.value = true
  error.value = ''
  try {
    const res = await userOrderApi.pay({ order_id: orderId, payment_method: payMethod.value })
    if (res.code === 0) {
      router.replace(`/payment/result/${orderId}`)
    } else {
      error.value = res.message || '支付失败'
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    paying.value = false
  }
}

onMounted(async () => {
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) order.value = res.data
  } catch {
    order.value = { order_no: `ORD${orderId}`, hotel_name: '示例酒店', room_type_name: '豪华大床房', check_in_date: '2026-04-10', check_out_date: '2026-04-12', guest_name: '张三', total_amount: '1376.00' }
  } finally {
    loading.value = false
  }
  timer = setInterval(() => {
    if (countdown.value > 0) countdown.value--
  }, 1000)
})

onUnmounted(() => clearInterval(timer))
</script>

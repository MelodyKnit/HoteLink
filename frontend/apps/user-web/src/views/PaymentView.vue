<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">订单支付</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6">
      <p v-if="error && !loading" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

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
            <span class="text-2xl font-bold text-orange-600">¥{{ payableAmount }}</span>
          </div>
        </div>

        <!-- Countdown -->
        <p v-if="countdown > 0 && !isPaid" class="mt-3 text-center text-xs text-gray-400">
          请在 <span class="font-semibold text-orange-600">{{ Math.floor(countdown / 60) }}:{{ String(countdown % 60).padStart(2, '0') }}</span> 内完成支付
        </p>
        <p v-else-if="countdown <= 0 && !isPaid && !loading" class="mt-3 text-center text-xs text-red-500">
          支付时间已过期，订单可能已被自动取消，请返回订单列表查看
        </p>
        <div v-if="countdown <= 0 && !isPaid && !loading" class="mt-3 text-center">
          <router-link to="/my/orders" class="inline-block rounded-full bg-brand px-5 py-2 text-sm text-white hover:bg-brand-dark">返回订单列表</router-link>
        </div>

        <!-- Pay button -->
        <div class="sticky bottom-16 mt-6 md:bottom-0">
          <button @click="handlePay" :disabled="paying || isPaid || countdown <= 0" class="w-full rounded-2xl bg-brand py-3.5 text-center text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
            {{ paying ? '支付中...' : isPaid ? '订单已支付' : countdown <= 0 ? '支付已过期' : `确认支付 ¥${payableAmount}` }}
          </button>
        </div>

        <p v-if="error" class="mt-3 text-center text-sm text-red-500">{{ error }}</p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi } from '@hotelink/api'
import { formatMoney } from '@hotelink/utils'
import { useToast } from '@hotelink/ui'

const { showToast } = useToast()

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.orderId)
const loading = ref(true)
const paying = ref(false)
const error = ref('')
const order = ref<any>({})
const payMethod = ref('mock')
const countdown = ref(0)
let timer: ReturnType<typeof setInterval>
const payableAmount = computed(() => formatMoney(order.value?.pay_amount ?? order.value?.total_amount ?? order.value?.original_amount ?? 0))
const isPaid = computed(() => order.value?.payment_status === 'paid')

function buildFallbackOrderFromRoute() {
  return {
    order_no: (route.query.order_no as string) || '',
    hotel_name: (route.query.hotel_name as string) || '',
    room_type_name: (route.query.room_name as string) || '',
    check_in_date: (route.query.check_in_date as string) || '',
    check_out_date: (route.query.check_out_date as string) || '',
    guest_name: (route.query.guest_name as string) || '',
    pay_amount: (route.query.pay_amount as string) || '0.00',
    total_amount: (route.query.pay_amount as string) || '0.00',
    payment_status: 'unpaid',
  }
}

const methods = [
  { value: 'mock', icon: '💳', label: '模拟支付（演示）' },
  { value: 'wechat', icon: '💚', label: '微信支付' },
  { value: 'alipay', icon: '🔵', label: '支付宝' },
]

// 处理 Pay 交互逻辑。
async function handlePay() {
  if (isPaid.value) return
  paying.value = true
  error.value = ''
  try {
    const res = await userOrderApi.pay({ order_id: orderId, payment_method: payMethod.value })
    if (res.code === 0) {
      showToast('支付成功，正在跳转结果页', 'success')
      router.replace(`/payment/result/${orderId}`)
    } else {
      error.value = res.message || '支付失败'
      showToast(error.value, 'error')
    }
  } catch {
    error.value = '网络错误，请重试'
    showToast(error.value, 'error')
  } finally {
    paying.value = false
  }
}

onMounted(async () => {
  order.value = buildFallbackOrderFromRoute()
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) {
      order.value = res.data
      // 根据订单创建时间计算剩余支付时间（默认 30 分钟）
      const cancelMinutes = 30
      if (res.data.created_at) {
        const createdTime = new Date(res.data.created_at).getTime()
        const deadline = createdTime + cancelMinutes * 60 * 1000
        const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000))
        countdown.value = remaining
      } else {
        countdown.value = cancelMinutes * 60
      }
    } else {
      error.value = res.message || '订单信息加载失败，请稍后重试'
      showToast(error.value, 'error')
    }
  } catch {
    error.value = '订单信息加载失败，请稍后重试'
    showToast(error.value, 'error')
  } finally {
    loading.value = false
  }
  timer = setInterval(async () => {
    if (countdown.value > 0) {
      countdown.value--
      if (countdown.value <= 0) {
        // 倒计时归零，刷新订单状态确认是否已被系统取消
        try {
          const refreshRes = await userOrderApi.detail(orderId)
          if (refreshRes.code === 0 && refreshRes.data) {
            order.value = refreshRes.data
          }
        } catch { /* ignore */ }
      }
    }
  }, 1000)
})

onUnmounted(() => clearInterval(timer))
</script>

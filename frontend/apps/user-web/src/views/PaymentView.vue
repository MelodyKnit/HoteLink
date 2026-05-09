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
        <div class="rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="font-semibold text-gray-800">订单信息</h3>
          <div class="mt-3 space-y-2 text-sm text-gray-600">
            <p>订单号：{{ order.order_no || orderId }}</p>
            <p>酒店：{{ order.hotel_name || '-' }}</p>
            <p>房型：{{ order.room_type_name || '-' }}</p>
            <p>入住：{{ order.check_in_date }} — {{ order.check_out_date }}</p>
            <p>入住人：{{ order.guest_name || '-' }}</p>
            <p v-if="order.payment_gateway_label">最近支付网关：{{ order.payment_gateway_label }}</p>
          </div>
        </div>

        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <div class="mb-3 flex items-center justify-between gap-3">
            <h3 class="font-semibold text-gray-800">支付方式</h3>
            <span class="text-xs text-gray-400">{{ methods.length }} 种可用</span>
          </div>

          <div v-if="methods.length" class="space-y-2">
            <label
              v-for="option in methods"
              :key="optionKey(option)"
              class="flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition"
              :class="selectedOptionKey === optionKey(option) ? 'border-brand bg-brand/5' : 'border-gray-200'"
            >
              <input v-model="selectedOptionKey" type="radio" :value="optionKey(option)" class="mt-1 accent-brand" />
              <span class="mt-0.5 text-xl">{{ option.icon }}</span>
              <span class="min-w-0 flex-1">
                <span class="flex flex-wrap items-center gap-2">
                  <span class="text-sm font-medium text-gray-800">{{ option.label }}</span>
                  <span v-if="option.sandbox" class="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] text-amber-700">沙箱/联调</span>
                  <span v-if="option.is_mock" class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">演示</span>
                </span>
                <span class="mt-1 block text-xs leading-5 text-gray-500">{{ option.description }}</span>
              </span>
            </label>
          </div>

          <div v-else class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
            暂无可用支付方式。请联系平台管理员开通支付网关，或稍后重试。
          </div>
        </div>

        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <div class="flex items-end justify-between">
            <span class="text-sm text-gray-500">应付金额</span>
            <span class="text-2xl font-bold text-orange-600">¥{{ payableAmount }}</span>
          </div>
        </div>

        <div v-if="selectedOption && !selectedOption.is_mock" class="mt-4 rounded-2xl bg-emerald-50/80 p-4 text-sm text-emerald-800 ring-1 ring-emerald-100">
          <p class="font-medium">真实支付接入提示</p>
          <p class="mt-1 leading-6">当前页面会消费后端下发的统一支付动作协议。若网关未配置托管收银台，支付结果页会展示该协议与下一步接入提示。</p>
        </div>

        <p v-if="countdown > 0 && !isPaid" class="mt-3 text-center text-xs text-gray-400">
          请在 <span class="font-semibold text-orange-600">{{ Math.floor(countdown / 60) }}:{{ String(countdown % 60).padStart(2, '0') }}</span> 内完成支付
        </p>
        <p v-else-if="countdown <= 0 && !isPaid && !loading" class="mt-3 text-center text-xs text-red-500">
          支付时间已过期，订单可能已被自动取消，请返回订单列表查看
        </p>

        <div v-if="countdown <= 0 && !isPaid && !loading" class="mt-3 text-center">
          <router-link to="/my/orders" class="inline-block rounded-full bg-brand px-5 py-2 text-sm text-white hover:bg-brand-dark">返回订单列表</router-link>
        </div>

        <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h3 class="font-semibold text-gray-800">帮助与联系</h3>
          <div class="mt-3 space-y-2 text-sm text-gray-600">
            <p v-if="supportPhone">客服电话：{{ supportPhone }}</p>
            <p v-if="supportEmail">客服邮箱：{{ supportEmail }}</p>
            <p class="text-xs text-gray-400">如果第三方支付页已打开但结果未返回，可以先完成付款，再到订单详情或支付结果页查看状态。</p>
          </div>
        </div>

        <div class="sticky bottom-16 mt-6 md:bottom-0">
          <button
            @click="handlePay"
            :disabled="paying || isPaid || countdown <= 0 || !selectedOption"
            class="w-full rounded-2xl bg-brand py-3.5 text-center text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
          >
            {{ buttonText }}
          </button>
        </div>

        <p v-if="error" class="mt-3 text-center text-sm text-red-500">{{ error }}</p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi, type PaymentAction, type UserPaymentMethodOption } from '@hotelink/api'
import { formatMoney } from '@hotelink/utils'
import { useToast } from '@hotelink/ui'

const { showToast } = useToast()

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.orderId)
const loading = ref(true)
const paying = ref(false)
const error = ref('')
const order = ref<Record<string, unknown>>({})
const methods = ref<UserPaymentMethodOption[]>([])
const selectedOptionKey = ref('')
const countdown = ref(0)
const supportPhone = ref('')
const supportEmail = ref('')
let timer: ReturnType<typeof setInterval> | null = null

const payableAmount = computed(() =>
  formatMoney((order.value?.pay_amount ?? order.value?.total_amount ?? order.value?.original_amount ?? 0) as number | string),
)
const isPaid = computed(() => order.value?.payment_status === 'paid')
const selectedOption = computed(() => methods.value.find(item => optionKey(item) === selectedOptionKey.value) || null)
const buttonText = computed(() => {
  if (paying.value) return '支付处理中...'
  if (isPaid.value) return '订单已支付'
  if (countdown.value <= 0) return '支付已过期'
  if (!selectedOption.value) return '暂无可用支付方式'
  return `确认支付 ¥${payableAmount.value}`
})

function optionKey(option: UserPaymentMethodOption): string {
  return `${option.value}:${option.gateway_name || option.value}`
}

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

function persistPaymentAction(action: PaymentAction) {
  sessionStorage.setItem(`hotelink_payment_action_${orderId}`, JSON.stringify(action))
}

async function handlePay() {
  if (!selectedOption.value || isPaid.value) return
  paying.value = true
  error.value = ''
  try {
    const res = await userOrderApi.pay({
      order_id: orderId,
      payment_method: selectedOption.value.value,
      gateway_name: selectedOption.value.gateway_name || undefined,
      payment_scene: selectedOption.value.scene || undefined,
    })
    if (res.code === 0 && res.data) {
      const action = res.data.payment_action
      persistPaymentAction(action)
      if (action.status === 'paid') {
        showToast(action.message || '支付成功，正在跳转结果页', 'success')
        router.replace(`/payment/result/${orderId}`)
        return
      }
      showToast(action.message || '支付请求已创建', 'success')
      if (action.type === 'redirect_url' && action.redirect_url) {
        window.location.href = action.redirect_url
        return
      }
      router.replace({ path: `/payment/result/${orderId}`, query: { phase: 'pending' } })
      return
    }
    error.value = res.message || '支付失败'
    showToast(error.value, 'error')
  } catch {
    error.value = '网络错误，请重试'
    showToast(error.value, 'error')
  } finally {
    paying.value = false
  }
}

async function loadPaymentContext() {
  order.value = buildFallbackOrderFromRoute()
  try {
    const res = await userOrderApi.paymentOptions(orderId)
    if (res.code === 0 && res.data) {
      order.value = res.data.order
      methods.value = res.data.available_methods
      supportPhone.value = res.data.support_phone
      supportEmail.value = res.data.support_email
      countdown.value = Math.max(0, Number(res.data.remaining_seconds || 0))
      if (methods.value.length) {
        selectedOptionKey.value = optionKey(methods.value[0])
      }
      if ((res.data.order as Record<string, unknown>)?.payment_status === 'paid') {
        sessionStorage.removeItem(`hotelink_payment_action_${orderId}`)
      }
      return
    }

    const detail = await userOrderApi.detail(orderId)
    if (detail.code === 0 && detail.data) {
      order.value = detail.data as Record<string, unknown>
    }
    error.value = res.message || '订单支付信息加载失败，请稍后重试'
    showToast(error.value, 'error')
  } catch {
    error.value = '订单支付信息加载失败，请稍后重试'
    showToast(error.value, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadPaymentContext()
  timer = setInterval(async () => {
    if (countdown.value > 0) {
      countdown.value -= 1
      if (countdown.value <= 0 && !isPaid.value) {
        try {
          const refreshRes = await userOrderApi.detail(orderId)
          if (refreshRes.code === 0 && refreshRes.data) {
            order.value = refreshRes.data as Record<string, unknown>
          }
        } catch {
          // ignore refresh failures at countdown boundary
        }
      }
    }
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

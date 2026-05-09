<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <h1 class="text-sm font-semibold text-gray-800">支付结果</h1>
    </header>

    <div class="mx-auto max-w-md px-4 py-16 text-center">
      <div v-if="loading" class="py-12 text-sm text-gray-400">正在查询支付结果…</div>

      <template v-else>
        <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

        <div class="text-6xl">{{ phaseIcon }}</div>
        <h2 class="mt-4 text-xl font-bold" :class="phaseColorClass">
          {{ phaseTitle }}
        </h2>
        <p class="mt-2 text-sm text-gray-500">{{ phaseDescription }}</p>

        <div class="mt-6 rounded-2xl bg-white p-5 text-left shadow-sm">
          <div class="space-y-2 text-sm text-gray-600">
            <p>订单号：{{ order.order_no || orderId }}</p>
            <p>酒店：{{ order.hotel_name || '-' }}</p>
            <p>房型：{{ order.room_type_name || '-' }}</p>
            <p>入住日期：{{ order.check_in_date || '-' }}</p>
            <p>离店日期：{{ order.check_out_date || '-' }}</p>
            <p>支付金额：<span class="font-semibold text-orange-600">¥{{ payableAmount }}</span></p>
          </div>
        </div>

        <div v-if="phase === 'pending' && action" class="mt-4 rounded-2xl bg-white p-5 text-left shadow-sm">
          <div class="mb-3 flex items-center justify-between gap-3">
            <h3 class="font-semibold text-gray-800">支付动作协议</h3>
            <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{{ action.type }}</span>
          </div>
          <div class="space-y-2 text-sm text-gray-600">
            <p v-for="(item, index) in action.instructions" :key="index">{{ item }}</p>
            <p v-if="action.client_payload?.gateway_label">支付网关：{{ action.client_payload.gateway_label }}</p>
            <p v-if="action.client_payload?.scene">支付场景：{{ action.client_payload.scene }}</p>
            <p v-if="action.client_payload?.payment_no">支付单号：{{ action.client_payload.payment_no }}</p>
          </div>
          <button
            v-if="action.type === 'redirect_url' && action.redirect_url"
            type="button"
            class="mt-4 w-full rounded-2xl bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark"
            @click="continueToGateway"
          >
            继续前往支付
          </button>
        </div>

        <div class="mt-8 flex flex-col gap-3">
          <router-link :to="`/my/orders/${orderId}`" class="rounded-2xl bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark">查看订单</router-link>
          <router-link to="/" class="rounded-2xl border border-gray-200 px-6 py-3 text-sm font-medium text-gray-600 transition hover:bg-gray-50">返回首页</router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { userOrderApi, type PaymentAction } from '@hotelink/api'
import { formatMoney } from '@hotelink/utils'

const route = useRoute()
const orderId = Number(route.params.orderId)
const loading = ref(true)
const error = ref('')
const order = ref<Record<string, unknown>>({})
const action = ref<PaymentAction | null>(null)
const phase = ref<'success' | 'pending' | 'failed'>('failed')
let poller: ReturnType<typeof setInterval> | null = null

const payableAmount = computed(() =>
  formatMoney((order.value?.pay_amount ?? order.value?.total_amount ?? order.value?.original_amount ?? 0) as number | string),
)
const phaseIcon = computed(() => {
  if (phase.value === 'success') return '✅'
  if (phase.value === 'pending') return '⏳'
  return '❌'
})
const phaseTitle = computed(() => {
  if (phase.value === 'success') return '支付成功'
  if (phase.value === 'pending') return '支付处理中'
  return '支付失败'
})
const phaseDescription = computed(() => {
  if (phase.value === 'success') return '您的预订已确认，祝您入住愉快！'
  if (phase.value === 'pending') return '支付请求已经生成，请按照支付网关提示继续完成，或稍后返回查看状态。'
  return '支付未完成，请重试或联系客服。'
})
const phaseColorClass = computed(() => {
  if (phase.value === 'success') return 'text-green-600'
  if (phase.value === 'pending') return 'text-amber-600'
  return 'text-red-600'
})

function loadStoredAction() {
  const raw = sessionStorage.getItem(`hotelink_payment_action_${orderId}`)
  if (!raw) return
  try {
    action.value = JSON.parse(raw) as PaymentAction
  } catch {
    action.value = null
  }
}

function continueToGateway() {
  if (action.value?.redirect_url) {
    window.location.href = action.value.redirect_url
  }
}

async function fetchResult() {
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) {
      order.value = res.data as Record<string, unknown>
      if ((res.data as Record<string, unknown>).payment_status === 'paid') {
        phase.value = 'success'
        sessionStorage.removeItem(`hotelink_payment_action_${orderId}`)
      } else if (route.query.phase === 'pending' || action.value?.status === 'pending') {
        phase.value = 'pending'
      } else {
        phase.value = 'failed'
      }
      return
    }
    error.value = res.message || '支付结果读取失败，请稍后在订单页查看'
    phase.value = action.value?.status === 'pending' ? 'pending' : 'failed'
  } catch {
    error.value = '支付结果读取失败，请稍后在订单页查看'
    phase.value = action.value?.status === 'pending' ? 'pending' : 'failed'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loadStoredAction()
  await fetchResult()
  if (phase.value === 'pending') {
    poller = setInterval(async () => {
      await fetchResult()
      if (phase.value === 'success' && poller) {
        clearInterval(poller)
        poller = null
      }
    }, 5000)
  }
})

onUnmounted(() => {
  if (poller) clearInterval(poller)
})
</script>

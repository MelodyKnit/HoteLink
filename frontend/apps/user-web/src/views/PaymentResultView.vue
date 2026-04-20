<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <h1 class="text-sm font-semibold text-gray-800">支付结果</h1>
    </header>

    <div class="mx-auto max-w-md px-4 py-16 text-center">
      <div v-if="loading" class="py-12 text-sm text-gray-400">正在查询支付结果…</div>
      <template v-else>
      <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

      <div class="text-6xl">{{ success ? '✅' : '❌' }}</div>
      <h2 class="mt-4 text-xl font-bold" :class="success ? 'text-green-600' : 'text-red-600'">
        {{ success ? '支付成功' : '支付失败' }}
      </h2>
      <p class="mt-2 text-sm text-gray-500">{{ success ? '您的预订已确认，祝您入住愉快！' : '支付未完成，请重试或联系客服。' }}</p>

      <div v-if="success" class="mt-6 rounded-2xl bg-white p-5 text-left shadow-sm">
        <div class="space-y-2 text-sm text-gray-600">
          <p>订单号：{{ order.order_no || orderId }}</p>
          <p>酒店：{{ order.hotel_name || '-' }}</p>
          <p>房型：{{ order.room_type_name || '-' }}</p>
          <p>入住日期：{{ order.check_in_date }}</p>
          <p>离店日期：{{ order.check_out_date }}</p>
          <p>支付金额：<span class="font-semibold text-orange-600">¥{{ payableAmount }}</span></p>
        </div>
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
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { userOrderApi } from '@hotelink/api'
import { formatMoney } from '@hotelink/utils'

const route = useRoute()
const orderId = Number(route.params.orderId)
const loading = ref(true)
const success = ref(false)
const order = ref<any>({})
const error = ref('')
const payableAmount = computed(() => formatMoney(order.value?.pay_amount ?? order.value?.total_amount ?? order.value?.original_amount ?? 0))

onMounted(async () => {
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) {
      order.value = res.data
      success.value = (res.data as any).payment_status === 'paid'
    } else {
      error.value = res.message || '支付结果读取失败，请稍后在订单页查看'
      success.value = false
    }
  } catch {
    order.value = {}
    error.value = '支付结果读取失败，请稍后在订单页查看'
    success.value = false
  } finally {
    loading.value = false
  }
})
</script>

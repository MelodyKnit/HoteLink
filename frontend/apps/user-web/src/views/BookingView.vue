<template>
  <div class="booking-page min-h-screen">
    <header class="site-header sticky top-0 z-40 flex h-14 items-center px-4">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">填写订单</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6">
      <!-- Room Summary -->
      <div class="surface-card rounded-2xl p-5">
        <h3 class="font-semibold text-gray-800">{{ hotelName }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ roomName }}</p>
        <div class="mt-3 flex items-center gap-4 text-sm text-gray-600">
          <div>
            <p class="text-xs text-gray-400">入住</p>
            <p class="font-medium">{{ checkInDate }}</p>
          </div>
          <span class="text-gray-300">→</span>
          <div>
            <p class="text-xs text-gray-400">离店</p>
            <p class="font-medium">{{ checkOutDate }}</p>
          </div>
          <div class="ml-auto text-right">
            <p class="text-xs text-gray-400">共{{ nights }}晚</p>
            <p class="text-lg font-bold text-orange-600">¥{{ totalPrice }}</p>
          </div>
        </div>
      </div>

      <!-- Dates -->
      <div class="surface-card mt-4 rounded-2xl p-5">
        <h4 class="mb-3 font-semibold text-gray-800">入住日期</h4>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs text-gray-400">入住日期</label>
            <input v-model="checkInDate" type="date" :min="today" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          </div>
          <div>
            <label class="mb-1 block text-xs text-gray-400">离店日期</label>
            <input v-model="checkOutDate" type="date" :min="checkInDate || today" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          </div>
        </div>
      </div>

      <!-- Guest Info -->
      <div class="surface-card mt-4 rounded-2xl p-5">
        <h4 class="mb-3 font-semibold text-gray-800">入住人信息</h4>
        <div class="space-y-3">
          <div>
            <label class="mb-1 block text-xs text-gray-400">入住人姓名 *</label>
            <input
              v-model="form.guest_name"
              type="text"
              placeholder="请输入入住人真实姓名"
              class="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition"
              :class="fieldErrors.guest_name ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-gray-200 focus:border-brand'"
            />
            <p v-if="fieldErrors.guest_name" class="mt-1 text-xs text-red-500">{{ fieldErrors.guest_name }}</p>
          </div>
          <div>
            <label class="mb-1 block text-xs text-gray-400">手机号码 *</label>
            <input
              v-model="form.guest_mobile"
              type="tel"
              placeholder="请输入手机号"
              maxlength="11"
              class="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition"
              :class="fieldErrors.guest_mobile ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-gray-200 focus:border-brand'"
            />
            <p v-if="fieldErrors.guest_mobile" class="mt-1 text-xs text-red-500">{{ fieldErrors.guest_mobile }}</p>
          </div>
          <div>
            <label class="mb-1 block text-xs text-gray-400">入住人数</label>
            <select v-model.number="form.guest_count" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-brand">
              <option v-for="n in 4" :key="n" :value="n">{{ n }}人</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Remark -->
      <div class="surface-card mt-4 rounded-2xl p-5">
        <h4 class="mb-3 font-semibold text-gray-800">备注</h4>
        <textarea v-model="form.remark" rows="2" placeholder="如有特殊需求请备注（选填）" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-brand" />
      </div>

      <!-- Price Breakdown -->
      <div class="surface-card mt-4 rounded-2xl p-5">
        <h4 class="mb-3 font-semibold text-gray-800">费用明细</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between text-gray-600">
            <span>房费 (¥{{ unitPrice }} × {{ nights }}晚)</span>
            <span>¥{{ totalPrice }}</span>
          </div>
          <div class="border-t border-dashed border-gray-200 pt-2">
            <div class="flex justify-between font-semibold text-gray-900">
              <span>合计</span>
              <span class="text-orange-600">¥{{ totalPrice }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="sticky bottom-16 z-30 mt-6 space-y-3 md:bottom-0">
        <div v-if="error" class="feedback-error-card flex items-start gap-2 rounded-xl px-3 py-2.5 text-sm text-red-700">
          <span class="mt-0.5 text-base">⚠</span>
          <div>
            <p class="font-semibold">提交失败</p>
            <p class="text-xs text-red-600">{{ error }}</p>
          </div>
        </div>
        <button @click="handleSubmit" :disabled="submitting" class="w-full rounded-2xl bg-brand py-3.5 text-center text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
          {{ submitting ? '提交中...' : '提交订单' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi } from '@hotelink/api'
import { formatDate } from '@hotelink/utils'

const route = useRoute()
const router = useRouter()
const hotelId = Number(route.query.hotel_id)
const roomTypeId = Number(route.query.room_type_id)
const hotelName = (route.query.hotel_name as string) || ''
const roomName = (route.query.room_name as string) || ''
const unitPrice = Number(route.query.price) || 0

const today = formatDate(new Date())
const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1)
const checkInDate = ref(today)
const checkOutDate = ref(formatDate(tomorrow))
const submitting = ref(false)
const error = ref('')
const fieldErrors = ref<{ guest_name?: string; guest_mobile?: string }>({})

const form = ref({
  guest_name: '',
  guest_mobile: '',
  guest_count: 2,
  remark: '',
})

const nights = computed(() => {
  const d1 = new Date(checkInDate.value)
  const d2 = new Date(checkOutDate.value)
  const diff = Math.ceil((d2.getTime() - d1.getTime()) / 86400000)
  return diff > 0 ? diff : 1
})

const totalPrice = computed(() => (unitPrice * nights.value).toFixed(2))

function validateForm(): boolean {
  const nextErrors: { guest_name?: string; guest_mobile?: string } = {}
  if (!form.value.guest_name.trim()) {
    nextErrors.guest_name = '请输入入住人姓名'
  }
  if (!form.value.guest_mobile.trim()) {
    nextErrors.guest_mobile = '请输入手机号'
  } else if (!/^1\d{10}$/.test(form.value.guest_mobile.trim())) {
    nextErrors.guest_mobile = '手机号格式不正确'
  }
  fieldErrors.value = nextErrors
  if (nextErrors.guest_name) {
    error.value = nextErrors.guest_name
    return false
  }
  if (nextErrors.guest_mobile) {
    error.value = nextErrors.guest_mobile
    return false
  }
  return true
}

// 处理 Submit 交互逻辑。
async function handleSubmit() {
  if (!validateForm()) return
  error.value = ''
  submitting.value = true
  try {
    const res = await userOrderApi.create({
      hotel_id: hotelId,
      room_type_id: roomTypeId,
      check_in_date: checkInDate.value,
      check_out_date: checkOutDate.value,
      guest_name: form.value.guest_name,
      guest_mobile: form.value.guest_mobile,
      guest_count: form.value.guest_count,
      remark: form.value.remark,
    })
    if (res.code === 0 && res.data) {
      router.replace(`/payment/${(res.data as any).order_id || (res.data as any).id}`)
    } else {
      error.value = res.message || '提交失败'
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.booking-page {
  background: radial-gradient(120% 40% at 50% -5%, rgba(20, 184, 166, 0.12), rgba(255, 255, 255, 0));
}
</style>

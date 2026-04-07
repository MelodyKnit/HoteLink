<template>
  <div class="booking-page min-h-screen">
    <header class="site-header sticky top-0 z-40 flex h-14 items-center px-4">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">填写订单</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6 pb-28 md:pb-8">
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
          <div class="relative">
            <label class="mb-1 block text-xs text-gray-400">入住人姓名 *</label>
            <input
              v-model="form.guest_name"
              type="text"
              placeholder="请输入入住人真实姓名"
              class="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition"
              :class="fieldErrors.guest_name ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-gray-200 focus:border-brand'"
              @focus="handleGuestNameFocus"
              @input="handleGuestNameInput"
              @blur="handleGuestNameBlur"
            />
            <div v-if="showGuestSuggestions" class="absolute left-0 right-0 top-[calc(100%+8px)] z-20 rounded-2xl border border-brand/10 bg-white p-2 shadow-lg ring-1 ring-slate-100">
              <p class="px-2 pb-1 text-[11px] font-medium text-gray-400">常用入住人</p>
              <button
                v-for="item in filteredGuestHistory"
                :key="`${item.guest_name}-${item.guest_mobile}`"
                type="button"
                class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left transition hover:bg-brand/5"
                @mousedown.prevent="applyGuestHistory(item)"
              >
                <span class="truncate text-sm text-gray-800">{{ item.guest_name }}</span>
                <span class="ml-3 shrink-0 text-xs text-gray-400">{{ item.masked_mobile }}</span>
              </button>
            </div>
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

      <!-- Coupon Selection -->
      <div class="surface-card mt-4 rounded-2xl p-5">
        <h4 class="mb-3 font-semibold text-gray-800">优惠券</h4>
        <div v-if="availableCoupons.length === 0" class="text-sm text-gray-400">暂无可用优惠券</div>
        <div v-else class="space-y-2">
          <label class="flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2.5 transition"
            :class="selectedCouponId === null ? 'border-brand bg-brand/5' : 'border-gray-200 hover:bg-gray-50'"
            @click="selectedCouponId = null">
            <span class="flex h-5 w-5 items-center justify-center rounded-full border-2" :class="selectedCouponId === null ? 'border-brand bg-brand' : 'border-gray-300'">
              <span v-if="selectedCouponId === null" class="h-2 w-2 rounded-full bg-white" />
            </span>
            <span class="text-sm text-gray-600">不使用优惠券</span>
          </label>
          <label v-for="c in availableCoupons" :key="c.id"
            class="flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2.5 transition"
            :class="selectedCouponId === c.id ? 'border-brand bg-brand/5' : 'border-gray-200 hover:bg-gray-50'"
            @click="selectedCouponId = c.id">
            <span class="flex h-5 w-5 items-center justify-center rounded-full border-2" :class="selectedCouponId === c.id ? 'border-brand bg-brand' : 'border-gray-300'">
              <span v-if="selectedCouponId === c.id" class="h-2 w-2 rounded-full bg-white" />
            </span>
            <span class="flex-1">
              <span class="text-sm font-medium" :class="c.coupon_type === 'cash' ? 'text-brand' : 'text-orange-600'">
                {{ c.coupon_type === 'cash' ? `¥${c.amount}` : `${c.discount}折` }}
              </span>
              <span class="ml-2 text-sm text-gray-600">{{ c.name }}</span>
              <span class="ml-2 text-xs text-gray-400">{{ c.condition }}</span>
            </span>
          </label>
        </div>
      </div>

      <!-- Price Breakdown -->
      <div class="surface-card mt-4 rounded-2xl p-5">
        <h4 class="mb-3 font-semibold text-gray-800">费用明细</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between text-gray-600">
            <span>房费 (¥{{ unitPrice }} × {{ nights }}晚)</span>
            <span>¥{{ totalPrice }}</span>
          </div>
          <div v-if="memberDiscountAmount > 0" class="flex justify-between text-green-600">
            <span>{{ memberDiscountLabels[memberLevel] || '会员折扣' }}</span>
            <span>-¥{{ memberDiscountAmount.toFixed(2) }}</span>
          </div>
          <div v-if="couponDiscountAmount > 0" class="flex justify-between text-orange-500">
            <span>优惠券抵扣</span>
            <span>-¥{{ couponDiscountAmount.toFixed(2) }}</span>
          </div>
          <div class="border-t border-dashed border-gray-200 pt-2">
            <div class="flex justify-between font-semibold text-gray-900">
              <span>合计</span>
              <span class="text-orange-600">¥{{ finalPrice }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="mt-6 space-y-3 pb-[calc(env(safe-area-inset-bottom)+8px)]">
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userOrderApi, userCouponApi, userProfileApi } from '@hotelink/api'
import { formatDate } from '@hotelink/utils'

const GUEST_HISTORY_KEY = 'hotelink_guest_history'

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
const guestHistory = ref<Array<{ guest_name: string; guest_mobile: string; masked_mobile: string }>>([])
const guestSuggestionOpen = ref(false)
let guestSuggestionCloseTimer: number | null = null

const form = ref({
  guest_name: '',
  guest_mobile: '',
  guest_count: 2,
  remark: '',
})

// 会员折扣与优惠券
const memberLevel = ref('normal')
const memberDiscountRate = ref(1.0)
const availableCoupons = ref<any[]>([])
const selectedCouponId = ref<number | null>(null)

const memberDiscountLabels: Record<string, string> = {
  normal: '', silver: '银卡98折', gold: '金卡95折', platinum: '铂金92折', diamond: '钻石88折',
}

const selectedCoupon = computed(() => availableCoupons.value.find(c => c.id === selectedCouponId.value))

const memberDiscountAmount = computed(() => {
  const orig = unitPrice * nights.value
  return +(orig * (1 - memberDiscountRate.value)).toFixed(2)
})

const couponDiscountAmount = computed(() => {
  const c = selectedCoupon.value
  if (!c) return 0
  const afterMember = unitPrice * nights.value - memberDiscountAmount.value
  if (c.coupon_type === 'cash') return Math.min(+c.amount, afterMember)
  if (c.coupon_type === 'discount') return +(afterMember * (1 - c.discount / 10)).toFixed(2)
  return 0
})

const totalDiscount = computed(() => memberDiscountAmount.value + couponDiscountAmount.value)
const finalPrice = computed(() => Math.max(0, unitPrice * nights.value - totalDiscount.value).toFixed(2))

const nights = computed(() => {
  const d1 = new Date(checkInDate.value)
  const d2 = new Date(checkOutDate.value)
  const diff = Math.ceil((d2.getTime() - d1.getTime()) / 86400000)
  return diff > 0 ? diff : 1
})

const totalPrice = computed(() => (unitPrice * nights.value).toFixed(2))
const filteredGuestHistory = computed(() => {
  const keyword = form.value.guest_name.trim().toLowerCase()
  if (!keyword) return guestHistory.value
  return guestHistory.value.filter((item) => item.guest_name.toLowerCase().includes(keyword))
})

const showGuestSuggestions = computed(() => {
  if (!guestSuggestionOpen.value || !guestHistory.value.length) return false
  const name = form.value.guest_name.trim()
  const mobile = form.value.guest_mobile.trim()
  if (!name && !mobile) return true
  return !!name && filteredGuestHistory.value.length > 0
})

function maskMobile(mobile: string): string {
  const value = (mobile || '').trim()
  if (value.length < 7) return value
  return `${value.slice(0, 3)}***${value.slice(-3)}`
}

function normalizeGuestHistory(items: Array<{ guest_name: string; guest_mobile: string; masked_mobile?: string }>) {
  const seen = new Set<string>()
  return items
    .map((item) => ({
      guest_name: (item.guest_name || '').trim(),
      guest_mobile: (item.guest_mobile || '').trim(),
      masked_mobile: item.masked_mobile || maskMobile(item.guest_mobile || ''),
    }))
    .filter((item) => item.guest_name && item.guest_mobile)
    .filter((item) => {
      const key = `${item.guest_name}::${item.guest_mobile}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .slice(0, 6)
}

function loadLocalGuestHistory() {
  try {
    const raw = localStorage.getItem(GUEST_HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Array<{ guest_name: string; guest_mobile: string; masked_mobile?: string }>
    return normalizeGuestHistory(Array.isArray(parsed) ? parsed : [])
  } catch {
    return []
  }
}

function saveLocalGuestHistory() {
  localStorage.setItem(GUEST_HISTORY_KEY, JSON.stringify(guestHistory.value))
}

function rememberGuestHistory(name: string, mobile: string) {
  const merged = normalizeGuestHistory([
    { guest_name: name, guest_mobile: mobile, masked_mobile: maskMobile(mobile) },
    ...guestHistory.value,
  ])
  guestHistory.value = merged
  saveLocalGuestHistory()
}

async function loadGuestHistory() {
  guestHistory.value = loadLocalGuestHistory()
  if (guestHistory.value.length && !form.value.guest_name && !form.value.guest_mobile) {
    applyGuestHistory(guestHistory.value[0])
  }
  try {
    const res = await userOrderApi.guestHistory({ limit: 6 })
    if (res.code === 0 && res.data) {
      guestHistory.value = normalizeGuestHistory([
        ...((res.data as { items: Array<{ guest_name: string; guest_mobile: string; masked_mobile: string }> }).items || []),
        ...guestHistory.value,
      ])
      saveLocalGuestHistory()
      if (guestHistory.value.length && !form.value.guest_name && !form.value.guest_mobile) {
        applyGuestHistory(guestHistory.value[0])
      }
    }
  } catch {
    // ignore history load failure to avoid blocking order creation
  }
}

function applyGuestHistory(item: { guest_name: string; guest_mobile: string; masked_mobile: string }) {
  form.value.guest_name = item.guest_name
  form.value.guest_mobile = item.guest_mobile
  fieldErrors.value = { ...fieldErrors.value, guest_name: undefined, guest_mobile: undefined }
  error.value = ''
  guestSuggestionOpen.value = false
}

function handleGuestNameFocus() {
  if (guestSuggestionCloseTimer) {
    window.clearTimeout(guestSuggestionCloseTimer)
    guestSuggestionCloseTimer = null
  }
  guestSuggestionOpen.value = true
}

function handleGuestNameInput() {
  guestSuggestionOpen.value = true
}

function handleGuestNameBlur() {
  guestSuggestionCloseTimer = window.setTimeout(() => {
    guestSuggestionOpen.value = false
  }, 120)
}

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
      ...(selectedCouponId.value ? { coupon_id: selectedCouponId.value } : {}),
    })
    if (res.code === 0 && res.data) {
      rememberGuestHistory(form.value.guest_name.trim(), form.value.guest_mobile.trim())
      const orderData = res.data as any
      router.replace({
        path: `/payment/${orderData.order_id || orderData.id}`,
        query: {
          order_no: String(orderData.order_no || ''),
          hotel_name: hotelName,
          room_name: roomName,
          check_in_date: checkInDate.value,
          check_out_date: checkOutDate.value,
          guest_name: form.value.guest_name,
          pay_amount: String(orderData.pay_amount || totalPrice.value),
        },
      })
    } else {
      error.value = res.message || '提交失败'
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  loadGuestHistory()
  try {
    const profileRes = await userProfileApi.get()
    if (profileRes.code === 0 && profileRes.data) {
      const p = profileRes.data as any
      memberLevel.value = p.member_level || 'normal'
      const rates: Record<string, number> = { normal: 1.0, silver: 0.98, gold: 0.95, platinum: 0.92, diamond: 0.88 }
      memberDiscountRate.value = rates[memberLevel.value] ?? 1.0
    }
  } catch { /* ignore */ }
})

// 当总价变化时重新加载可用优惠券
watch(totalPrice, async (val) => {
  if (+val > 0) {
    try {
      const couponRes = await userCouponApi.forOrder(+val)
      if (couponRes.code === 0 && couponRes.data) {
        availableCoupons.value = (couponRes.data as any).items || couponRes.data || []
      }
    } catch { /* ignore */ }
  }
}, { immediate: true })
</script>

<style scoped>
.booking-page {
  background: radial-gradient(120% 40% at 50% -5%, rgba(20, 184, 166, 0.12), rgba(255, 255, 255, 0));
}
</style>

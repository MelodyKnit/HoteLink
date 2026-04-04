<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">帮助中心</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6 pb-24 md:pb-6">
      <!-- Search -->
      <div class="relative">
        <input v-model="search" placeholder="搜索常见问题..." class="w-full rounded-2xl border border-gray-200 bg-white py-3 pl-10 pr-4 text-sm outline-none focus:border-brand" />
        <span class="absolute left-3 top-3.5 text-gray-400">🔍</span>
      </div>

      <!-- Quick Contacts -->
      <div class="mt-6 grid grid-cols-2 gap-3">
        <a href="tel:4001234567" class="flex items-center gap-3 rounded-2xl bg-white p-4 shadow-sm hover:shadow">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-brand/10 text-xl">📞</span>
          <div>
            <p class="text-sm font-semibold text-gray-800">电话客服</p>
            <p class="text-xs text-gray-400">400-123-4567</p>
          </div>
        </a>
        <router-link to="/ai-chat" class="flex items-center gap-3 rounded-2xl bg-white p-4 shadow-sm hover:shadow">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-purple-50 text-xl">🤖</span>
          <div>
            <p class="text-sm font-semibold text-gray-800">AI 客服</p>
            <p class="text-xs text-gray-400">24小时在线</p>
          </div>
        </router-link>
      </div>

      <!-- FAQ -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">常见问题</h3>
        <div class="space-y-2">
          <div v-for="(q, i) in filteredFaqs" :key="i" class="rounded-2xl bg-white shadow-sm">
            <button @click="toggle(i)" class="flex w-full items-center justify-between p-4 text-left">
              <span class="text-sm font-medium text-gray-800">{{ q.question }}</span>
              <span class="text-gray-400 transition-transform" :class="expanded.has(i) ? 'rotate-180' : ''">▼</span>
            </button>
            <div v-if="expanded.has(i)" class="border-t border-gray-100 px-4 pb-4 pt-2 text-sm leading-relaxed text-gray-600">{{ q.answer }}</div>
          </div>
        </div>
      </div>

      <!-- Categories -->
      <div class="mt-6">
        <h3 class="mb-3 font-semibold text-gray-800">帮助分类</h3>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div v-for="cat in categories" :key="cat.title" class="flex flex-col items-center rounded-2xl bg-white p-4 shadow-sm">
            <span class="text-2xl">{{ cat.icon }}</span>
            <p class="mt-2 text-sm font-medium text-gray-800">{{ cat.title }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const search = ref('')
const expanded = ref(new Set<number>())

function toggle(idx: number) {
  if (expanded.value.has(idx)) expanded.value.delete(idx)
  else expanded.value.add(idx)
}

const faqs = [
  { question: '如何预订酒店？', answer: '在首页搜索或浏览酒店列表，选择心仪的酒店和房型后，填写入住信息并完成支付即可。' },
  { question: '如何取消订单？', answer: '在「我的订单」中找到需要取消的订单，点击「取消订单」按钮即可。不同订单取消规则可能不同，请注意查看取消政策。' },
  { question: '如何申请退款？', answer: '取消订单后系统将自动发起退款，退款将在1-3个工作日内原路返回。' },
  { question: '如何修改入住人信息？', answer: '在订单确认前可以修改入住人信息。已确认的订单如需修改，请联系客服。' },
  { question: '什么是会员积分？', answer: '每次成功入住后可获得积分奖励，积分可用于兑换礼品、房晚或抵扣订单金额。' },
  { question: '如何开具发票？', answer: '在「个人中心」>「发票管理」中添加抬头并提交开票申请，电子发票将在3个工作日内发送至您的邮箱。' },
  { question: '如何使用优惠券？', answer: '在预订页面选择可用优惠券即可自动抵扣。优惠券有使用条件和有效期限制，请注意查看。' },
  { question: '入住时间和退房时间是几点？', answer: '一般入住时间为14:00以后，退房时间为次日12:00前。具体时间以酒店规定为准。' },
]

const categories = [
  { icon: '🏨', title: '预订相关' },
  { icon: '💳', title: '支付退款' },
  { icon: '🎫', title: '会员权益' },
  { icon: '📄', title: '发票问题' },
  { icon: '⭐', title: '评价申诉' },
  { icon: '🔐', title: '账户安全' },
]

const filteredFaqs = computed(() => {
  if (!search.value.trim()) return faqs
  return faqs.filter(q => q.question.includes(search.value) || q.answer.includes(search.value))
})
</script>

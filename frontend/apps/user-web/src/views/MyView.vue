<template>
  <div class="mx-auto max-w-2xl px-4 py-6">
    <!-- Profile card -->
    <div class="rounded-2xl bg-gradient-to-r from-brand to-teal-500 p-6 text-white">
      <div class="flex items-center gap-4">
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 text-2xl font-bold backdrop-blur">
          {{ (auth.user?.nickname || auth.user?.username || 'U').charAt(0).toUpperCase() }}
        </div>
        <div class="flex-1">
          <h2 class="text-lg font-bold">{{ auth.user?.nickname || auth.user?.username || '用户' }}</h2>
          <p class="text-sm text-teal-100">{{ memberLevelMap[auth.user?.member_level || 'normal'] || '普通会员' }}</p>
        </div>
        <router-link to="/my/profile" class="rounded-full bg-white/20 px-3 py-1.5 text-xs backdrop-blur hover:bg-white/30">编辑资料</router-link>
      </div>
    </div>

    <!-- Order quick links -->
    <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-gray-800">我的订单</h3>
        <router-link to="/my/orders" class="text-xs text-brand hover:underline">全部 →</router-link>
      </div>
      <div class="grid grid-cols-4 gap-2 text-center">
        <router-link to="/my/orders?status=pending_payment" class="rounded-xl py-3 transition hover:bg-gray-50">
          <p class="text-xl">💰</p>
          <p class="mt-1 text-xs text-gray-500">待支付</p>
        </router-link>
        <router-link to="/my/orders?status=confirmed" class="rounded-xl py-3 transition hover:bg-gray-50">
          <p class="text-xl">📋</p>
          <p class="mt-1 text-xs text-gray-500">待入住</p>
        </router-link>
        <router-link to="/my/orders?status=checked_in" class="rounded-xl py-3 transition hover:bg-gray-50">
          <p class="text-xl">🏨</p>
          <p class="mt-1 text-xs text-gray-500">入住中</p>
        </router-link>
        <router-link to="/my/orders?status=completed" class="rounded-xl py-3 transition hover:bg-gray-50">
          <p class="text-xl">✅</p>
          <p class="mt-1 text-xs text-gray-500">已完成</p>
        </router-link>
      </div>
    </div>

    <!-- Menu items -->
    <div class="mt-4 rounded-2xl bg-white shadow-sm">
      <router-link v-for="item in menuItems" :key="item.path" :to="item.path"
        class="flex items-center gap-3 border-b border-gray-50 px-5 py-4 transition last:border-0 hover:bg-gray-50"
      >
        <span class="text-lg">{{ item.icon }}</span>
        <span class="flex-1 text-sm text-gray-700">{{ item.label }}</span>
        <span class="text-xs text-gray-300">›</span>
      </router-link>
    </div>

    <!-- Logout -->
    <button @click="handleLogout" class="mt-6 w-full rounded-2xl border border-red-200 py-3 text-sm font-medium text-red-500 transition hover:bg-red-50">退出登录</button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'

const auth = useUserAuthStore()
const router = useRouter()

const memberLevelMap: Record<string, string> = {
  normal: '普通会员',
  silver: '银卡会员',
  gold: '金卡会员',
  platinum: '白金会员',
}

const menuItems = [
  { path: '/ai-booking', icon: '🧭', label: 'AI 订房助手' },
  { path: '/ai-chat', icon: '💬', label: 'AI 智能客服' },
  { path: '/my/favorites', icon: '❤️', label: '我的收藏' },
  { path: '/my/coupons', icon: '🎫', label: '优惠券' },
  { path: '/my/membership', icon: '👑', label: '会员中心' },
  { path: '/my/reviews', icon: '⭐', label: '我的评价' },
  { path: '/my/invoices', icon: '📄', label: '发票管理' },
  { path: '/help', icon: '❓', label: '帮助中心' },
  { path: '/about', icon: '📖', label: '关于我们' },
]

// 处理 Logout 交互逻辑。
function handleLogout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-gray-50">
    <!-- Top navigation bar -->
    <header class="sticky top-0 z-40 border-b border-gray-100 bg-white/95 backdrop-blur">
      <div class="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <router-link to="/" class="flex items-center gap-2">
          <span class="text-xl font-bold text-brand">HoteLink</span>
        </router-link>
        <!-- PC nav links -->
        <nav class="hidden items-center gap-6 md:flex">
          <router-link to="/" class="text-sm font-medium text-gray-600 transition hover:text-brand">首页</router-link>
          <router-link to="/hotels" class="text-sm font-medium text-gray-600 transition hover:text-brand">酒店</router-link>
          <router-link to="/about" class="text-sm font-medium text-gray-600 transition hover:text-brand">关于</router-link>
          <router-link to="/help" class="text-sm font-medium text-gray-600 transition hover:text-brand">帮助</router-link>
        </nav>
        <div class="flex items-center gap-3">
          <template v-if="auth.isLoggedIn">
            <router-link to="/my" class="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
              {{ (auth.user?.nickname || auth.user?.username || 'U').charAt(0).toUpperCase() }}
            </router-link>
          </template>
          <template v-else>
            <router-link to="/login" class="rounded-full bg-brand px-4 py-1.5 text-sm font-medium text-white transition hover:bg-brand-dark">登录</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- Page content -->
    <main class="flex-1 pb-20 md:pb-0">
      <router-view />
    </main>

    <!-- Bottom tab bar (mobile only) -->
    <nav class="fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white md:hidden">
      <div class="flex h-16 items-stretch">
        <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path"
          class="flex flex-1 flex-col items-center justify-center gap-0.5 text-xs transition"
          :class="isTabActive(tab.path) ? 'text-brand' : 'text-gray-400'"
        >
          <span class="text-lg">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </router-link>
      </div>
    </nav>

    <!-- Footer (PC only) -->
    <footer class="hidden border-t border-gray-200 bg-white md:block">
      <div class="mx-auto max-w-5xl px-4 py-8">
        <div class="grid grid-cols-3 gap-8 text-sm text-gray-500">
          <div>
            <p class="mb-3 font-semibold text-gray-800">HoteLink</p>
            <p>现代化酒店预订与管理平台</p>
          </div>
          <div>
            <p class="mb-3 font-semibold text-gray-800">帮助</p>
            <router-link to="/help" class="block hover:text-brand">常见问题</router-link>
            <router-link to="/contact" class="block hover:text-brand">联系我们</router-link>
          </div>
          <div>
            <p class="mb-3 font-semibold text-gray-800">关注</p>
            <router-link to="/about" class="block hover:text-brand">品牌故事</router-link>
          </div>
        </div>
        <p class="mt-6 text-center text-xs text-gray-400">&copy; {{ new Date().getFullYear() }} HoteLink. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'

const auth = useUserAuthStore()
const route = useRoute()

const tabs = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/hotels', icon: '🔍', label: '搜索' },
  { path: '/my/orders', icon: '📋', label: '订单' },
  { path: '/my', icon: '👤', label: '我的' },
]

// 判断TabActive条件是否成立。
function isTabActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

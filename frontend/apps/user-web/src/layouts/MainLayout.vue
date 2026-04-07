<template>
  <div class="app-shell flex min-h-screen flex-col">
    <!-- Top navigation bar -->
    <header class="site-header sticky top-0 z-40">
      <div class="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <router-link to="/" class="flex items-center gap-2">
          <span class="rounded-lg bg-brand/10 px-2 py-0.5 text-xl font-bold tracking-wide text-brand">HoteLink</span>
        </router-link>
        <!-- PC nav links -->
        <nav class="hidden items-center gap-6 md:flex">
          <router-link to="/" class="text-sm font-medium transition" :class="isNavActive('/') ? 'text-brand' : 'text-gray-600 hover:text-brand'">首页</router-link>
          <router-link to="/hotels" class="text-sm font-medium transition" :class="isNavActive('/hotels') ? 'text-brand' : 'text-gray-600 hover:text-brand'">酒店</router-link>
          <router-link to="/about" class="text-sm font-medium transition" :class="isNavActive('/about') ? 'text-brand' : 'text-gray-600 hover:text-brand'">关于</router-link>
          <router-link to="/help" class="text-sm font-medium transition" :class="isNavActive('/help') ? 'text-brand' : 'text-gray-600 hover:text-brand'">帮助</router-link>
        </nav>
        <div class="flex items-center gap-3">
          <template v-if="auth.isLoggedIn">
            <!-- Notification bell -->
            <router-link to="/my/notifications" class="relative flex h-8 w-8 items-center justify-center rounded-full hover:bg-gray-100 transition">
              <svg class="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span v-if="unreadCount > 0" class="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {{ unreadCount > 9 ? '9+' : unreadCount }}
              </span>
            </router-link>
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
    <nav class="mobile-tabbar fixed inset-x-0 bottom-0 z-40 md:hidden">
      <div class="relative flex h-16 items-stretch">
        <!-- Active indicator pill -->
        <div
          class="tab-indicator absolute bottom-2 h-1 w-10 rounded-full bg-brand transition-all duration-300 ease-in-out"
          :style="indicatorStyle"
        ></div>
        <router-link
          v-for="(tab, index) in tabs"
          :key="tab.path"
          :to="tab.path"
          class="mobile-tab-item relative flex flex-1 flex-col items-center justify-center gap-0.5 text-xs transition-colors duration-200"
          :class="isTabActive(tab.path) ? 'text-brand' : 'text-gray-400'"
        >
          <span
            class="transition-transform duration-200"
            :class="isTabActive(tab.path) ? 'scale-110' : 'scale-100'"
          >
            <component :is="tab.icon" class="h-5 w-5" />
          </span>
          <span class="text-[11px] font-medium">{{ tab.label }}</span>
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
import { ref, computed, onMounted, h, defineComponent, watch, provide } from 'vue'
import { useRoute } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'
import { userNoticeApi } from '@hotelink/api'

const auth = useUserAuthStore()
const route = useRoute()
const unreadCount = ref(0)

// ---- SVG icon components ----
const IconHome = defineComponent({ render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' })]) })
const IconSearch = defineComponent({ render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' })]) })
const IconOrders = defineComponent({ render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' })]) })
const IconUser = defineComponent({ render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' })]) })

const tabs = [
  { path: '/', icon: IconHome, label: '首页' },
  { path: '/hotels', icon: IconSearch, label: '搜索' },
  { path: '/my/orders', icon: IconOrders, label: '订单' },
  { path: '/my', icon: IconUser, label: '我的' },
]

// Fix: /my tab should NOT activate on /my/orders; /my/orders should activate on exact prefix only
function isTabActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  if (path === '/my') {
    // active only on /my itself or /my/sub-pages EXCEPT /my/orders (handled by its own tab)
    return route.path === '/my' || (route.path.startsWith('/my/') && !route.path.startsWith('/my/orders'))
  }
  return route.path === path || route.path.startsWith(path + '/')
}

const activeTabIndex = computed(() => {
  for (let i = tabs.length - 1; i >= 0; i--) {
    if (isTabActive(tabs[i].path)) return i
  }
  return -1
})

// Sliding indicator: left = index * 25% + (12.5% - 20px/2) centering a 40px pill in each 25%-wide column
const indicatorStyle = computed(() => {
  if (activeTabIndex.value < 0) return { opacity: '0' }
  // Each tab is 25% wide; center a 40px pill
  return {
    opacity: '1',
    left: `calc(${activeTabIndex.value * 25}% + 12.5% - 20px)`,
  }
})

function isNavActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

async function fetchUnreadCount() {
  if (!auth.isLoggedIn) return
  const res = await userNoticeApi.unreadCount()
  if (res.data) unreadCount.value = res.data.unread_count
}

// 暴露给子页面（NotificationView）直接更新角标值
provide('setUnreadCount', (n: number) => { unreadCount.value = n })
provide('fetchUnreadCount', fetchUnreadCount)

// 路由切换时刷新未读数，确保从通知页返回后角标立即消失
watch(() => route.path, (newPath, oldPath) => {
  if (oldPath === '/my/notifications' || newPath === '/my/notifications') {
    fetchUnreadCount()
  }
})

onMounted(fetchUnreadCount)
</script>


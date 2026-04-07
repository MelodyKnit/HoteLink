<template>
  <div class="h-screen overflow-hidden bg-slate-100 text-slate-900">
    <!-- Mobile overlay -->
    <Transition name="fade">
      <div v-if="sidebarOpen" class="fixed inset-0 z-40 bg-black/40 lg:hidden" @click="sidebarOpen = false" />
    </Transition>

    <div class="flex h-full">
      <!-- Sidebar -->
      <aside
        class="fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-900 text-white transition-transform duration-200 lg:static lg:translate-x-0"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      >
        <div class="flex h-16 shrink-0 items-center gap-3 px-6">
          <span class="text-xl font-bold tracking-wide text-teal-400">HoteLink</span>
          <span class="text-xs text-slate-400">管理端</span>
        </div>

        <nav class="flex-1 overflow-y-auto px-3 py-4">
          <template v-for="group in menuGroups" :key="group.label">
            <p class="mb-2 mt-4 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-500">{{ group.label }}</p>
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors"
              :class="isActive(item.path) ? 'bg-teal-600/20 text-teal-400' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
              @click="sidebarOpen = false"
            >
              <span class="w-5 text-center text-base">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </router-link>
          </template>
        </nav>

        <div class="border-t border-slate-700 px-4 py-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-teal-600 text-sm font-bold">
              {{ (auth.user?.nickname || auth.user?.username || 'A').charAt(0).toUpperCase() }}
            </div>
            <div class="flex-1 truncate">
              <p class="text-sm font-medium">{{ auth.user?.nickname || auth.user?.username }}</p>
              <p class="text-xs text-slate-400">{{ auth.user?.role === 'system_admin' ? '系统管理员' : '酒店管理员' }}</p>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main content -->
      <div class="flex min-h-0 flex-1 flex-col overflow-y-auto scroll-smooth" style="will-change: scroll-position;">
        <!-- Top bar -->
        <header class="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-8">
          <button class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" @click="sidebarOpen = !sidebarOpen">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
          </button>
          <div class="hidden lg:block" />
          <div class="flex items-center gap-4">
            <span class="text-sm text-slate-500">{{ todayStr }}</span>
            <button class="rounded-lg px-3 py-1.5 text-sm text-red-600 transition-colors hover:bg-red-50" @click="handleLogout">退出</button>
          </div>
        </header>

        <!-- Page content -->
        <main class="flex-1 px-4 py-6 lg:px-8">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@hotelink/store'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const sidebarOpen = ref(false)

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

// 判断Active条件是否成立。
function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/')
}

// 处理 Logout 交互逻辑。
function handleLogout() {
  auth.logout()
  router.push('/admin/login')
}

const menuGroups = [
  {
    label: '总览',
    items: [
      { path: '/admin', icon: '📊', label: '工作台' },
    ],
  },
  {
    label: '房态与资源',
    items: [
      { path: '/admin/hotels', icon: '🏨', label: '酒店管理' },
      { path: '/admin/room-types', icon: '🛏️', label: '房型管理' },
      { path: '/admin/inventory', icon: '📅', label: '价格库存' },
    ],
  },
  {
    label: '订单与前台',
    items: [
      { path: '/admin/orders', icon: '📋', label: '订单管理' },
    ],
  },
  {
    label: '客户与评价',
    items: [
      { path: '/admin/users', icon: '👥', label: '用户管理' },
      { path: '/admin/members', icon: '👑', label: '会员管理' },
      { path: '/admin/coupons', icon: '🎫', label: '优惠券管理' },
      { path: '/admin/reviews', icon: '⭐', label: '评价管理' },
    ],
  },
  {
    label: '财务与报表',
    items: [
      { path: '/admin/reports', icon: '📈', label: '经营报表' },
    ],
  },
  {
    label: '系统管理',
    items: [
      { path: '/admin/employees', icon: '🧑‍💼', label: '员工管理' },
      { path: '/admin/settings', icon: '⚙️', label: '系统配置' },
    ],
  },
  {
    label: 'AI 能力',
    items: [
      { path: '/admin/ai', icon: '🤖', label: 'AI 助手' },
      { path: '/admin/ai-settings', icon: '🔧', label: 'AI 配置' },
    ],
  },
]
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

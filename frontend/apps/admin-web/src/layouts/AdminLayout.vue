<template>
  <div class="h-[100dvh] overflow-hidden bg-slate-100 text-slate-900">
    <!-- Mobile overlay -->
    <Transition name="fade">
      <div v-if="sidebarOpen" class="fixed inset-0 z-40 bg-black/40 lg:hidden" @click="sidebarOpen = false" />
    </Transition>

    <div class="flex h-full min-h-0">
      <!-- Sidebar -->
      <aside
        class="admin-sidebar fixed inset-y-0 left-0 z-50 flex h-[100dvh] w-64 flex-col overflow-y-auto overscroll-contain bg-slate-900 text-white transition-transform duration-200 lg:static lg:translate-x-0"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      >
        <div class="flex h-16 shrink-0 items-center gap-3 px-6">
          <span class="text-xl font-bold tracking-wide text-teal-400">HoteLink</span>
          <span class="text-xs text-slate-400">管理端</span>
        </div>

        <nav class="flex-1 px-3 py-4">
          <template v-for="group in menuGroups" :key="group.label">
            <p class="mb-2 mt-4 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-500">{{ group.label }}</p>
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors duration-200"
              :class="isActive(item.path) ? 'bg-teal-500/20 text-teal-100 shadow-[inset_0_0_0_1px_rgba(45,212,191,0.25)]' : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'"
              @click="sidebarOpen = false"
            >
              <span class="w-5 text-center text-base">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </router-link>
          </template>
        </nav>

        <div class="border-t border-slate-700 px-4 py-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 shrink-0 overflow-hidden rounded-full bg-teal-600 text-sm font-bold">
              <img v-if="auth.user?.avatar && !sidebarAvatarError" :src="auth.user.avatar" class="h-full w-full object-cover" @error="sidebarAvatarError = true" />
              <span v-else class="flex h-full w-full items-center justify-center">{{ (auth.user?.nickname || auth.user?.username || 'A').charAt(0).toUpperCase() }}</span>
            </div>
            <div class="flex-1 truncate">
              <p class="text-sm font-medium">{{ auth.user?.nickname || auth.user?.username }}</p>
              <p class="text-xs text-slate-400">{{ auth.user?.role === 'system_admin' ? '系统管理员' : '酒店管理员' }}</p>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main content -->
      <div class="flex h-[100dvh] min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain scroll-smooth">
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
const sidebarAvatarError = ref(false)

const isSystemAdmin = computed(() => auth.user?.role === 'system_admin')

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

// 判断菜单项是否处于 active 状态。
function isActive(path: string): boolean {
  if (route.path === path) return true
  if (path === '/admin/orders' && route.path.startsWith('/admin/orders/')) return true
  return false
}

// 处理 Logout 交互逻辑。
function handleLogout() {
  auth.logout()
  router.push('/admin/login')
}

const ALL_MENU_GROUPS = [
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
      { path: '/admin/users', icon: '👥', label: '用户管理', systemOnly: true },
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
      { path: '/admin/settings', icon: '⚙️', label: '系统配置', systemOnly: true },
      { path: '/admin/system-status', icon: '📡', label: '系统状态', systemOnly: true },
    ],
  },
  {
    label: 'AI 能力',
    items: [
      { path: '/admin/ai', icon: '🤖', label: 'AI 助手' },
      { path: '/admin/ai-logs', icon: '📋', label: '调用日志' },
      { path: '/admin/ai-settings', icon: '🔧', label: 'AI 配置', systemOnly: true },
    ],
  },
]

// 根据角色过滤菜单。
const menuGroups = computed(() => {
  return ALL_MENU_GROUPS
    .map(group => ({
      ...group,
      items: group.items.filter(item => isSystemAdmin.value || !('systemOnly' in item && item.systemOnly)),
    }))
    .filter(group => group.items.length > 0)
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.admin-sidebar {
  scrollbar-width: thin;
  scrollbar-color: rgba(100, 116, 139, 0.7) rgba(15, 23, 42, 0.65);
  scrollbar-gutter: stable;
}

.admin-sidebar::-webkit-scrollbar {
  width: 8px;
}

.admin-sidebar::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.65);
}

.admin-sidebar::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.7);
  border-radius: 999px;
  border: 2px solid rgba(15, 23, 42, 0.65);
}

.admin-sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.85);
}
</style>

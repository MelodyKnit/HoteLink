import { createRouter, createWebHistory } from 'vue-router'
import { getToken, systemApi } from '@hotelink/api'
import { useAuthStore } from '@hotelink/store'
import AdminLayout from '../layouts/AdminLayout.vue'

let systemInitialized: boolean | null = null

// 检查 Initialized 条件是否满足。
async function checkInitialized(): Promise<boolean> {
  if (systemInitialized !== null) return systemInitialized
  try {
    const res = await systemApi.initCheck()
    systemInitialized = res.code === 0 && res.data?.initialized === true
  } catch {
    systemInitialized = true
  }
  return systemInitialized
}

// 重置 InitCache 状态。
export function resetInitCache() {
  systemInitialized = null
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/admin/setup',
      name: 'setup',
      component: () => import('../views/InitSetupView.vue'),
      meta: { setup: true },
    },
    {
      path: '/admin/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/admin',
      component: AdminLayout,
      children: [
        { path: '', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'hotels', name: 'hotels', component: () => import('../views/HotelListView.vue') },
        { path: 'room-types', name: 'room-types', component: () => import('../views/RoomTypeListView.vue') },
        { path: 'inventory', name: 'inventory', component: () => import('../views/InventoryView.vue') },
        { path: 'orders', name: 'orders', component: () => import('../views/OrderListView.vue') },
        { path: 'orders/:id', name: 'order-detail', component: () => import('../views/OrderDetailView.vue') },
        { path: 'users', name: 'users', component: () => import('../views/UserListView.vue') },
        { path: 'members', name: 'members', component: () => import('../views/MemberManageView.vue') },
        { path: 'coupons', name: 'coupons', component: () => import('../views/CouponManageView.vue') },
        { path: 'reviews', name: 'reviews', component: () => import('../views/ReviewListView.vue') },
        { path: 'reports', name: 'reports', component: () => import('../views/ReportView.vue') },
        { path: 'employees', name: 'employees', component: () => import('../views/EmployeeListView.vue') },
        { path: 'settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
        { path: 'ai', name: 'ai', component: () => import('../views/AIAssistantView.vue') },
        { path: 'ai-settings', name: 'ai-settings', component: () => import('../views/AISettingsView.vue') },
        { path: '404', name: 'admin-not-found', component: () => import('../views/NotFoundView.vue') },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/admin/404',
    },
  ],
})

router.beforeEach(async (to) => {
  const initialized = await checkInitialized()

  // 系统未初始化：只允许访问 setup 页面
  if (!initialized) {
    if (!to.meta.setup) return { name: 'setup' }
    return
  }

  // 系统已初始化：不允许再访问 setup 页面
  if (to.meta.setup) {
    return { name: 'login' }
  }

  const token = getToken()
  if (!to.meta.guest && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guest && token) {
    return { name: 'dashboard' }
  }

  // 刷新后恢复用户数据
  if (token) {
    const auth = useAuthStore()
    if (!auth.user) {
      await auth.fetchMe()
      // 验证管理员角色
      if (auth.user && !auth.isAdmin) {
        auth.logout()
        return { name: 'login' }
      }
    }
  }
})

export default router

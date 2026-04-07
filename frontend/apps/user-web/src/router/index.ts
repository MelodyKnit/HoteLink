import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@hotelink/api'
import { useUserAuthStore } from '@hotelink/store'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition || { top: 0 }
  },
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'home', component: () => import('../views/HomeView.vue') },
        { path: 'hotels', name: 'hotels', component: () => import('../views/HotelListView.vue') },
        { path: 'my', name: 'my', component: () => import('../views/MyView.vue'), meta: { auth: true } },
        { path: 'my/orders', name: 'orders', component: () => import('../views/OrderListView.vue'), meta: { auth: true } },
      ],
    },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
    { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
    { path: '/hotels/:id', name: 'hotel-detail', component: () => import('../views/HotelDetailView.vue') },
    { path: '/booking', name: 'booking', component: () => import('../views/BookingView.vue'), meta: { auth: true } },
    { path: '/payment/:orderId', name: 'payment', component: () => import('../views/PaymentView.vue'), meta: { auth: true } },
    { path: '/payment/result/:orderId', name: 'payment-result', component: () => import('../views/PaymentResultView.vue'), meta: { auth: true } },
    { path: '/my/orders/:id', name: 'order-detail', component: () => import('../views/OrderDetailView.vue'), meta: { auth: true } },
    { path: '/my/profile', name: 'profile', component: () => import('../views/ProfileView.vue'), meta: { auth: true } },
    { path: '/my/membership', name: 'membership', component: () => import('../views/MembershipView.vue'), meta: { auth: true } },
    { path: '/my/coupons', name: 'coupons', component: () => import('../views/CouponListView.vue'), meta: { auth: true } },
    { path: '/my/favorites', name: 'favorites', component: () => import('../views/FavoriteListView.vue'), meta: { auth: true } },
    { path: '/my/reviews', name: 'reviews', component: () => import('../views/ReviewListView.vue'), meta: { auth: true } },
    { path: '/my/invoices', name: 'invoices', component: () => import('../views/InvoiceView.vue'), meta: { auth: true } },
    { path: '/my/notifications', name: 'notifications', component: () => import('../views/NotificationView.vue'), meta: { auth: true } },
    { path: '/help', name: 'help', component: () => import('../views/HelpView.vue') },
    { path: '/ai-chat', name: 'ai-chat', component: () => import('../views/AIChatView.vue'), meta: { auth: true } },
    { path: '/ai-booking', name: 'ai-booking', component: () => import('../views/AIChatView.vue'), meta: { auth: true } },
    { path: '/about', name: 'about', component: () => import('../views/AboutView.vue') },
    { path: '/contact', name: 'contact', component: () => import('../views/ContactView.vue') },
    { path: '/404', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/404' },
  ],
})

router.beforeEach(async (to) => {
  const token = getToken()
  if (to.meta.auth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guest && token) {
    return { name: 'home' }
  }
  // 页面刷新后 token 存在但 user 数据丢失，自动恢复
  if (token) {
    const auth = useUserAuthStore()
    if (!auth.user) {
      await auth.fetchMe()
    }
  }
})

export default router

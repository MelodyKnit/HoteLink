import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, userAuthApi, getToken, setTokens, clearTokens, getRefreshToken } from '@hotelink/api'

const USER_LOCAL_STORAGE_KEYS = [
  'hotelink_guest_history',
  'hotelink_user_security_prefs',
  'hotelink_ai_booking_history',
  'hotelink_ai_customer_history',
]

const USER_SESSION_STORAGE_KEYS = [
  'hotelink_ai_booking_chat_state',
  'hotelink_ai_customer_chat_state',
]

function clearUserClientCache() {
  if (typeof window === 'undefined') return
  for (const key of USER_LOCAL_STORAGE_KEYS) {
    window.localStorage.removeItem(key)
  }
  for (const key of USER_SESSION_STORAGE_KEYS) {
    window.sessionStorage.removeItem(key)
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ id: number; username: string; role: string; nickname?: string; avatar?: string } | null>(null)
  const token = ref<string | null>(getToken())
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'hotel_admin' || user.value?.role === 'system_admin')

  // 执行login流程并同步登录态。
  async function login(username: string, password: string) {
    const normalizedUsername = username.trim()
    const res = await authApi.adminLogin({ username: normalizedUsername, password })
    if (res.code === 0 && res.data) {
      token.value = res.data.access_token
      setTokens(res.data.access_token, res.data.refresh_token)
      user.value = res.data.user
    }
    return res
  }

  // 加载 fetchMe 相关数据。
  async function fetchMe() {
    if (!token.value) return
    const res = await authApi.me()
    if (res.code === 0 && res.data) {
      user.value = {
        id: res.data.id,
        username: res.data.username,
        role: res.data.role,
        nickname: res.data.nickname,
        avatar: res.data.avatar,
      }
    }
  }

  // 执行logout流程并同步登录态。
  function logout() {
    const refresh = getRefreshToken()
    if (refresh) authApi.logout(refresh).catch(() => {})
    token.value = null
    user.value = null
    clearTokens()
  }

  return { user, token, isLoggedIn, isAdmin, login, fetchMe, logout }
})

export const useUserAuthStore = defineStore('userAuth', () => {
  const user = ref<{
    id: number; username: string; role: string; nickname?: string
    member_level?: string; mobile?: string; email?: string; avatar?: string
    gender?: string; birthday?: string; points?: number
  } | null>(null)
  const token = ref<string | null>(getToken())
  const isLoggedIn = computed(() => !!token.value)

  // 执行login流程并同步登录态。
  async function login(username: string, password: string) {
    const normalizedUsername = username.trim()
    const res = await userAuthApi.login({ username: normalizedUsername, password })
    if (res.code === 0 && res.data) {
      // 登录成功后先清理用户侧历史缓存，阻断跨账号串用。
      clearUserClientCache()
      token.value = res.data.access_token
      setTokens(res.data.access_token, res.data.refresh_token)
      const u = res.data.user
      user.value = {
        id: u.id, username: u.username, role: u.role,
        nickname: u.nickname, member_level: u.member_level,
        avatar: u.avatar, points: u.points,
      }
      // 登录后立即拉取完整用户信息（含 mobile、email 等）
      fetchMe().catch(() => {})
    }
    return res
  }

  // 执行register流程并同步登录态。
  async function register(data: { username: string; password: string; confirm_password: string; mobile: string; email?: string }) {
    return await userAuthApi.register(data)
  }

  // 加载 fetchMe 相关数据。
  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await userAuthApi.me()
      if (res.code === 0 && res.data) {
        user.value = {
          id: res.data.id, username: res.data.username, role: res.data.role,
          nickname: res.data.nickname, member_level: res.data.member_level,
          mobile: res.data.mobile, email: res.data.email, avatar: res.data.avatar,
          gender: res.data.gender, birthday: res.data.birthday,
        }
      }
    } catch { /* ignore */ }
  }

  // 执行logout流程并同步登录态。
  function logout() {
    const refresh = getRefreshToken()
    if (refresh) userAuthApi.logout(refresh).catch(() => {})
    clearUserClientCache()
    token.value = null
    user.value = null
    clearTokens()
  }

  return { user, token, isLoggedIn, login, register, fetchMe, logout }
})

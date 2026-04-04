import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, userAuthApi, getToken, setTokens, clearTokens, getRefreshToken } from '@hotelink/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ id: number; username: string; role: string; nickname?: string } | null>(null)
  const token = ref<string | null>(getToken())
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'hotel_admin' || user.value?.role === 'system_admin')

  async function login(username: string, password: string) {
    const res = await authApi.adminLogin({ username, password })
    if (res.code === 0 && res.data) {
      token.value = res.data.access_token
      setTokens(res.data.access_token, res.data.refresh_token)
      user.value = res.data.user
    }
    return res
  }

  async function fetchMe() {
    if (!token.value) return
    const res = await authApi.me()
    if (res.code === 0 && res.data) {
      user.value = {
        id: res.data.id,
        username: res.data.username,
        role: res.data.role,
        nickname: res.data.nickname,
      }
    }
  }

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

  async function login(username: string, password: string) {
    const res = await userAuthApi.login({ username, password })
    if (res.code === 0 && res.data) {
      token.value = res.data.access_token
      setTokens(res.data.access_token, res.data.refresh_token)
      user.value = { id: res.data.user.id, username: res.data.user.username, role: res.data.user.role, nickname: res.data.user.nickname, member_level: res.data.user.member_level }
    }
    return res
  }

  async function register(data: { username: string; password: string; confirm_password: string; mobile: string; email?: string }) {
    return await userAuthApi.register(data)
  }

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

  function logout() {
    const refresh = getRefreshToken()
    if (refresh) userAuthApi.logout(refresh).catch(() => {})
    token.value = null
    user.value = null
    clearTokens()
  }

  return { user, token, isLoggedIn, login, register, fetchMe, logout }
})

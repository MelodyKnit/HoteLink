import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, getToken, setTokens, clearTokens, getRefreshToken } from '@hotelink/api'

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

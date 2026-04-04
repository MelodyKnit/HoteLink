<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-dark to-brand px-4 py-10">
    <div class="w-full max-w-sm">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-white">HoteLink</h1>
        <p class="mt-1 text-sm text-teal-200">登录您的账户</p>
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-xl">
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">用户名</label>
            <input v-model="form.username" type="text" placeholder="请输入用户名" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none transition focus:border-brand focus:ring-1 focus:ring-brand" @keyup.enter="handleLogin" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">密码</label>
            <input v-model="form.password" type="password" placeholder="请输入密码" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none transition focus:border-brand focus:ring-1 focus:ring-brand" @keyup.enter="handleLogin" />
          </div>
        </div>

        <button @click="handleLogin" :disabled="loading" class="mt-6 w-full rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <p v-if="error" class="mt-3 text-center text-sm text-red-500">{{ error }}</p>

        <div class="mt-6 text-center">
          <router-link to="/register" class="text-sm text-brand hover:underline">还没有账号？立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'

const router = useRouter()
const route = useRoute()
const auth = useUserAuthStore()
const loading = ref(false)
const error = ref('')

const form = ref({ username: '', password: '' })

async function handleLogin() {
  if (!form.value.username || !form.value.password) { error.value = '请输入用户名和密码'; return }
  loading.value = true
  error.value = ''
  try {
    const res = await auth.login(form.value.username, form.value.password)
    if (res.code === 0) {
      await auth.fetchMe()
      const redirect = (route.query.redirect as string) || '/'
      router.replace(redirect)
    } else {
      error.value = res.message || '登录失败'
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-900 px-4">
    <div class="w-full max-w-md">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-teal-400">HoteLink</h1>
        <p class="mt-2 text-sm text-slate-400">酒店管理系统 · 管理端登录</p>
      </div>

      <form class="rounded-2xl bg-white p-8 shadow-xl" @submit.prevent="handleLogin">
        <div class="mb-5">
          <label class="mb-1.5 block text-sm font-medium text-slate-700">用户名</label>
          <input
            v-model="form.username"
            type="text"
            required
            autocomplete="username"
            class="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            placeholder="请输入管理员账号"
          />
        </div>
        <div class="mb-6">
          <label class="mb-1.5 block text-sm font-medium text-slate-700">密码</label>
          <input
            v-model="form.password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            placeholder="请输入密码"
          />
        </div>

        <p v-if="errorMsg" class="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">{{ errorMsg }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-teal-700 disabled:opacity-60"
        >
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <p class="mt-6 text-center text-xs text-slate-500">© 2026 HoteLink 酒店管理系统</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@hotelink/store'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await auth.login(form.username, form.password)
    if (res.code === 0) {
      const redirect = (route.query.redirect as string) || '/admin'
      router.push(redirect)
    } else {
      errorMsg.value = res.message || '登录失败'
    }
  } catch {
    errorMsg.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

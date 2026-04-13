<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-dark to-brand px-4 py-10">
    <div class="w-full max-w-sm">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-white">HoteLink</h1>
        <p class="mt-1 text-sm text-teal-200">登录您的账户</p>
      </div>

      <form class="rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="handleLogin">
        <div class="space-y-4">
          <div>
            <div class="mb-1 flex items-center justify-between">
              <label class="block text-xs font-medium text-gray-500">用户名</label>
              <span class="text-[11px] text-gray-400">请输入注册时使用的账号</span>
            </div>
            <input
              v-model="form.username"
              type="text"
              autocomplete="username"
              placeholder="请输入用户名"
              class="w-full rounded-xl border px-4 py-3 text-sm outline-none transition"
              :class="fieldErrors.username ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="clearFieldError('username')"
              @blur="validateUsernameField"
            />
            <p v-if="fieldErrors.username" class="mt-1 text-xs text-red-500">{{ fieldErrors.username }}</p>
          </div>

          <div>
            <div class="mb-1 flex items-center justify-between">
              <label class="block text-xs font-medium text-gray-500">密码</label>
              <span class="text-[11px] text-gray-400">区分大小写</span>
            </div>
            <input
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="请输入密码"
              class="w-full rounded-xl border px-4 py-3 text-sm outline-none transition"
              :class="fieldErrors.password ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="clearFieldError('password')"
              @blur="validatePasswordField"
            />
            <p v-if="fieldErrors.password" class="mt-1 text-xs text-red-500">{{ fieldErrors.password }}</p>
            <p v-else class="mt-1 text-xs text-gray-400">若连续输错，请先检查输入法和键盘大写状态。</p>
          </div>
        </div>

        <div v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <p class="font-medium">登录未成功</p>
          <p class="mt-1 text-xs text-red-500">{{ error }}</p>
        </div>

        <button type="submit" :disabled="loading" class="mt-6 w-full rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <div class="mt-6 text-center">
          <router-link to="/register" class="text-sm text-brand hover:underline">还没有账号？立即注册</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'
import { extractApiError } from '@hotelink/utils'

const router = useRouter()
const route = useRoute()
const auth = useUserAuthStore()
const loading = ref(false)
const error = ref('')

const form = ref({ username: '', password: '' })
const fieldErrors = ref<{ username?: string; password?: string }>({})

function clearFieldError(field: 'username' | 'password') {
  if (fieldErrors.value[field]) {
    fieldErrors.value = { ...fieldErrors.value, [field]: undefined }
  }
  if (error.value) {
    error.value = ''
  }
}

function validateUsernameField() {
  const username = form.value.username.trim()
  fieldErrors.value = {
    ...fieldErrors.value,
    username: username ? undefined : '请输入用户名',
  }
}

function validatePasswordField() {
  fieldErrors.value = {
    ...fieldErrors.value,
    password: form.value.password ? undefined : '请输入密码',
  }
}

function validateForm(): boolean {
  const nextErrors: { username?: string; password?: string } = {}
  const username = form.value.username.trim()

  if (!username) {
    nextErrors.username = '请输入用户名'
  }
  if (!form.value.password) {
    nextErrors.password = '请输入密码'
  }

  form.value.username = username
  fieldErrors.value = nextErrors
  return !nextErrors.username && !nextErrors.password
}

// 处理 Login 交互逻辑。
async function handleLogin() {
  if (!validateForm()) {
    error.value = fieldErrors.value.username || fieldErrors.value.password || ''
    return
  }

  loading.value = true
  error.value = ''
  try {
    const res = await auth.login(form.value.username, form.value.password)
    if (res.code === 0) {
      await auth.fetchMe()
      const redirect = (route.query.redirect as string) || '/'
      router.replace(redirect)
    } else {
      error.value = extractApiError(res, '登录失败，请稍后重试')
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

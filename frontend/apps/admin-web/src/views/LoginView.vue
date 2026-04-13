<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-900 px-4">
    <div class="w-full max-w-md">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-teal-400">HoteLink</h1>
        <p class="mt-2 text-sm text-slate-400">酒店管理系统 · 管理端登录</p>
      </div>

      <form class="rounded-2xl bg-white p-8 shadow-xl" @submit.prevent="handleLogin">
        <div class="space-y-5">
          <div>
            <div class="mb-1.5 flex items-center justify-between">
              <label class="block text-sm font-medium text-slate-700">用户名</label>
              <span class="text-[11px] text-slate-400">请输入管理员账号</span>
            </div>
            <input
              v-model="form.username"
              type="text"
              autocomplete="username"
              class="w-full rounded-lg border px-4 py-2.5 text-sm outline-none transition-colors"
              :class="fieldErrors.username ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-2 focus:ring-red-200' : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'"
              placeholder="请输入管理员账号"
              @input="clearFieldError('username')"
              @blur="validateField('username')"
            />
            <p v-if="fieldErrors.username" class="mt-1 text-xs text-red-500">{{ fieldErrors.username }}</p>
          </div>

          <div>
            <div class="mb-1.5 flex items-center justify-between">
              <label class="block text-sm font-medium text-slate-700">密码</label>
              <span class="text-[11px] text-slate-400">注意大小写</span>
            </div>
            <input
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-lg border px-4 py-2.5 text-sm outline-none transition-colors"
              :class="fieldErrors.password ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-2 focus:ring-red-200' : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'"
              placeholder="请输入密码"
              @input="clearFieldError('password')"
              @blur="validateField('password')"
            />
            <p v-if="fieldErrors.password" class="mt-1 text-xs text-red-500">{{ fieldErrors.password }}</p>
            <p v-else class="mt-1 text-xs text-slate-400">若登录失败，请先确认账号角色和键盘状态。</p>
          </div>
        </div>

        <div v-if="errorMsg" class="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <p class="font-medium">登录未成功</p>
          <p class="mt-1 text-xs text-red-500">{{ errorMsg }}</p>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="mt-6 w-full rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-teal-700 disabled:opacity-60"
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
import { extractApiError } from '@hotelink/utils'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<{ username?: string; password?: string }>({})

function clearFieldError(field: 'username' | 'password') {
  if (fieldErrors.value[field]) {
    fieldErrors.value = { ...fieldErrors.value, [field]: undefined }
  }
  if (errorMsg.value) {
    errorMsg.value = ''
  }
}

function validateField(field: 'username' | 'password') {
  if (field === 'username') {
    fieldErrors.value = {
      ...fieldErrors.value,
      username: form.username.trim() ? undefined : '请输入用户名',
    }
    return
  }

  fieldErrors.value = {
    ...fieldErrors.value,
    password: form.password ? undefined : '请输入密码',
  }
}

function validateForm(): boolean {
  const username = form.username.trim()
  const nextErrors: { username?: string; password?: string } = {}

  if (!username) nextErrors.username = '请输入用户名'
  if (!form.password) nextErrors.password = '请输入密码'

  form.username = username
  fieldErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 Login 交互逻辑。
async function handleLogin() {
  if (!validateForm()) {
    errorMsg.value = fieldErrors.value.username || fieldErrors.value.password || ''
    return
  }

  errorMsg.value = ''
  loading.value = true
  try {
    const res = await auth.login(form.username, form.password)
    if (res.code === 0) {
      const redirect = (route.query.redirect as string) || '/admin'
      router.push(redirect)
    } else {
      errorMsg.value = extractApiError(res, '登录失败，请稍后重试')
    }
  } catch {
    errorMsg.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

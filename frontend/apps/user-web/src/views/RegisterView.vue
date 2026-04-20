<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-dark to-brand px-4 py-10">
    <div class="w-full max-w-sm">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-white">HoteLink</h1>
        <p class="mt-1 text-sm text-teal-200">创建新账户</p>
      </div>

      <form class="rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="handleRegister">
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">用户名 *</label>
            <input
              v-model="form.username"
              type="text"
              autocomplete="username"
              placeholder="4-30位，支持中文、英文和数字"
              class="w-full rounded-xl border px-4 py-3 text-sm outline-none transition"
              :class="fieldErrors.username ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="clearFieldError('username')"
              @blur="validateField('username')"
            />
            <p v-if="fieldErrors.username" class="mt-1 text-xs text-red-500">{{ fieldErrors.username }}</p>
            <p v-else class="mt-1 text-xs text-gray-400">建议使用便于记忆的用户名，后续登录会更方便。</p>
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">手机号 *</label>
            <input
              v-model="form.mobile"
              type="tel"
              inputmode="numeric"
              autocomplete="tel"
              placeholder="请输入11位手机号"
              maxlength="11"
              class="w-full rounded-xl border px-4 py-3 text-sm outline-none transition"
              :class="fieldErrors.mobile ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="handleMobileInput"
              @blur="validateField('mobile')"
            />
            <p v-if="fieldErrors.mobile" class="mt-1 text-xs text-red-500">{{ fieldErrors.mobile }}</p>
            <p v-else class="mt-1 text-xs text-gray-400">用于接收订单提醒和重要通知，不会公开展示。</p>
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">密码 *</label>
            <div class="relative">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="至少8位"
              class="w-full rounded-xl border px-4 py-3 pr-10 text-sm outline-none transition"
              :class="fieldErrors.password ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="clearFieldError('password')"
              @blur="validateField('password')"
            />
            <button type="button" @click="showPassword = !showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" tabindex="-1">
              <span v-if="showPassword" class="text-sm">🙈</span>
              <span v-else class="text-sm">👁</span>
            </button>
            </div>
            <div class="mt-2">
              <div class="h-2 overflow-hidden rounded-full bg-gray-100">
                <div
                  class="h-full rounded-full transition-all"
                  :class="passwordStrengthBarClass"
                  :style="{ width: `${passwordStrength.percentage}%` }"
                />
              </div>
              <p class="mt-1 text-xs" :class="passwordStrengthTextClass">
                密码强度：{{ passwordStrength.label }}，{{ passwordStrength.hint }}
              </p>
            </div>
            <p v-if="fieldErrors.password" class="mt-1 text-xs text-red-500">{{ fieldErrors.password }}</p>
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">确认密码 *</label>
            <div class="relative">
            <input
              v-model="form.confirm_password"
              :type="showConfirmPassword ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="再次输入密码"
              class="w-full rounded-xl border px-4 py-3 pr-10 text-sm outline-none transition"
              :class="fieldErrors.confirm_password ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="clearFieldError('confirm_password')"
              @blur="validateField('confirm_password')"
            />
            <button type="button" @click="showConfirmPassword = !showConfirmPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" tabindex="-1">
              <span v-if="showConfirmPassword" class="text-sm">🙈</span>
              <span v-else class="text-sm">👁</span>
            </button>
            </div>
            <p v-if="fieldErrors.confirm_password" class="mt-1 text-xs text-red-500">{{ fieldErrors.confirm_password }}</p>
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              autocomplete="email"
              placeholder="选填，用于接收电子账单"
              class="w-full rounded-xl border px-4 py-3 text-sm outline-none transition"
              :class="fieldErrors.email ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-1 focus:ring-red-200' : 'border-gray-200 focus:border-brand focus:ring-1 focus:ring-brand'"
              @input="clearFieldError('email')"
              @blur="validateField('email')"
            />
            <p v-if="fieldErrors.email" class="mt-1 text-xs text-red-500">{{ fieldErrors.email }}</p>
            <p v-else class="mt-1 text-xs text-gray-400">填写后可用于找回通知和接收发票。</p>
          </div>
        </div>

        <div v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <p class="font-medium">注册未完成</p>
          <p class="mt-1 text-xs text-red-500">{{ error }}</p>
        </div>

        <button type="submit" :disabled="loading" class="mt-6 w-full rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
          {{ loading ? '注册中...' : '注册' }}
        </button>

        <div class="mt-6 text-center">
          <router-link to="/login" class="text-sm text-brand hover:underline">已有账号？去登录</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'
import {
  extractApiError,
  extractApiFieldErrors,
  getPasswordStrength,
  isValidChineseMobile,
  isValidEmailAddress,
  validatePassword,
  validateUsername,
} from '@hotelink/utils'

type RegisterField = 'username' | 'mobile' | 'password' | 'confirm_password' | 'email'

const router = useRouter()
const auth = useUserAuthStore()
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const form = ref({
  username: '',
  mobile: '',
  password: '',
  confirm_password: '',
  email: '',
})

const fieldErrors = ref<Partial<Record<RegisterField, string>>>({})

const passwordStrength = computed(() => getPasswordStrength(form.value.password, 8))
const passwordStrengthBarClass = computed(() => {
  switch (passwordStrength.value.level) {
    case 'weak':
      return 'bg-red-400'
    case 'fair':
      return 'bg-amber-400'
    case 'good':
      return 'bg-emerald-400'
    case 'strong':
      return 'bg-emerald-500'
    default:
      return 'bg-gray-200'
  }
})
const passwordStrengthTextClass = computed(() => {
  switch (passwordStrength.value.level) {
    case 'weak':
      return 'text-red-500'
    case 'fair':
      return 'text-amber-600'
    case 'good':
    case 'strong':
      return 'text-emerald-600'
    default:
      return 'text-gray-400'
  }
})

function clearFieldError(field: RegisterField) {
  if (fieldErrors.value[field]) {
    fieldErrors.value = { ...fieldErrors.value, [field]: undefined }
  }
  if (error.value) {
    error.value = ''
  }
}

function handleMobileInput() {
  form.value.mobile = form.value.mobile.replace(/\D/g, '').slice(0, 11)
  clearFieldError('mobile')
}

function getFieldError(field: RegisterField): string {
  switch (field) {
    case 'username':
      return validateUsername(form.value.username)
    case 'mobile':
      if (!form.value.mobile.trim()) return '请输入手机号'
      return isValidChineseMobile(form.value.mobile) ? '' : '请输入11位大陆手机号'
    case 'password':
      return validatePassword(form.value.password, { minLength: 8 })
    case 'confirm_password':
      if (!form.value.confirm_password) return '请再次输入密码'
      return form.value.password === form.value.confirm_password ? '' : '两次输入的密码不一致'
    case 'email':
      if (!form.value.email.trim()) return ''
      return isValidEmailAddress(form.value.email) ? '' : '邮箱格式不正确'
    default:
      return ''
  }
}

function validateField(field: RegisterField) {
  fieldErrors.value = {
    ...fieldErrors.value,
    [field]: getFieldError(field) || undefined,
  }
}

function validateForm(): boolean {
  const nextErrors: Partial<Record<RegisterField, string>> = {}
  form.value.username = form.value.username.trim()
  form.value.email = form.value.email.trim()

  ;(['username', 'mobile', 'password', 'confirm_password', 'email'] as RegisterField[]).forEach((field) => {
    const message = getFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  fieldErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 Register 交互逻辑。
async function handleRegister() {
  if (!validateForm()) {
    error.value = Object.values(fieldErrors.value).find(Boolean) || ''
    return
  }

  loading.value = true
  error.value = ''
  try {
    const res = await auth.register({
      username: form.value.username,
      password: form.value.password,
      confirm_password: form.value.confirm_password,
      mobile: form.value.mobile,
      email: form.value.email || undefined,
    })
    if (res.code === 0) {
      const loginRes = await auth.login(form.value.username, form.value.password)
      if (loginRes.code === 0) {
        router.replace('/')
      } else {
        router.replace('/login')
      }
    } else {
      const apiFieldErrors = extractApiFieldErrors(res, {
        confirm_password: '确认密码',
        email: '邮箱',
        mobile: '手机号',
        password: '密码',
        username: '用户名',
      })
      fieldErrors.value = { ...fieldErrors.value, ...apiFieldErrors }
      error.value = extractApiError(res, '注册失败，请稍后重试')
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

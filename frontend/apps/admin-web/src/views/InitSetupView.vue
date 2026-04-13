<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-teal-50 px-4">
    <div class="w-full max-w-md">
      <div class="mb-8 text-center">
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-600 text-2xl font-bold text-white shadow-lg">H</div>
        <h1 class="text-2xl font-bold text-slate-800">欢迎使用 HoteLink</h1>
        <p class="mt-2 text-sm text-slate-500">系统尚未初始化，请先创建管理员账户</p>
      </div>

      <form class="rounded-2xl bg-white p-8 shadow-lg ring-1 ring-slate-200" @submit.prevent="handleSubmit">
        <div class="space-y-5">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">管理员用户名</label>
            <input
              v-model="form.username"
              type="text"
              autocomplete="username"
              placeholder="至少 3 个字符"
              class="w-full rounded-lg border px-4 py-2.5 text-sm outline-none transition"
              :class="fieldErrors.username ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-2 focus:ring-red-200' : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'"
              @input="clearFieldError('username')"
              @blur="validateField('username')"
            />
            <p v-if="fieldErrors.username" class="mt-1 text-xs text-red-500">{{ fieldErrors.username }}</p>
            <p v-else class="mt-1 text-xs text-slate-400">建议使用清晰可识别的管理员账号，后续团队协作会更方便。</p>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">密码</label>
            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              placeholder="至少 8 个字符"
              class="w-full rounded-lg border px-4 py-2.5 text-sm outline-none transition"
              :class="fieldErrors.password ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-2 focus:ring-red-200' : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'"
              @input="clearFieldError('password')"
              @blur="validateField('password')"
            />
            <div class="mt-2">
              <div class="h-2 overflow-hidden rounded-full bg-slate-100">
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
            <label class="mb-1 block text-sm font-medium text-slate-700">确认密码</label>
            <input
              v-model="form.confirm_password"
              type="password"
              autocomplete="new-password"
              placeholder="再次输入密码"
              class="w-full rounded-lg border px-4 py-2.5 text-sm outline-none transition"
              :class="fieldErrors.confirm_password ? 'border-red-300 bg-red-50/70 focus:border-red-400 focus:ring-2 focus:ring-red-200' : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'"
              @input="clearFieldError('confirm_password')"
              @blur="validateField('confirm_password')"
            />
            <p v-if="fieldErrors.confirm_password" class="mt-1 text-xs text-red-500">{{ fieldErrors.confirm_password }}</p>
          </div>
        </div>

        <div v-if="errorMsg" class="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <p class="font-medium">创建管理员失败</p>
          <p class="mt-1 text-xs text-red-500">{{ errorMsg }}</p>
        </div>

        <button
          type="submit"
          :disabled="submitting"
          class="mt-6 w-full rounded-lg bg-teal-600 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:opacity-50"
        >
          {{ submitting ? '创建中…' : '创建管理员并进入系统' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { systemApi, setTokens } from '@hotelink/api'
import { useAuthStore } from '@hotelink/store'
import { extractApiError, extractApiFieldErrors, getPasswordStrength, validatePassword, validateUsername } from '@hotelink/utils'
import { resetInitCache } from '../router'

type InitField = 'username' | 'password' | 'confirm_password'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ username: '', password: '', confirm_password: '' })
const submitting = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<Partial<Record<InitField, string>>>({})

const passwordStrength = computed(() => getPasswordStrength(form.password, 8))
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
      return 'bg-slate-200'
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
      return 'text-slate-400'
  }
})

function clearFieldError(field: InitField) {
  if (fieldErrors.value[field]) {
    fieldErrors.value = { ...fieldErrors.value, [field]: undefined }
  }
  if (errorMsg.value) {
    errorMsg.value = ''
  }
}

function getFieldError(field: InitField): string {
  switch (field) {
    case 'username':
      return validateUsername(form.username, { label: '管理员用户名', minLength: 3, maxLength: 150 })
    case 'password':
      return validatePassword(form.password, { minLength: 8 })
    case 'confirm_password':
      if (!form.confirm_password) return '请再次输入密码'
      return form.password === form.confirm_password ? '' : '两次输入的密码不一致'
    default:
      return ''
  }
}

function validateField(field: InitField) {
  fieldErrors.value = {
    ...fieldErrors.value,
    [field]: getFieldError(field) || undefined,
  }
}

function validateForm(): boolean {
  const nextErrors: Partial<Record<InitField, string>> = {}
  form.username = form.username.trim()

  ;(['username', 'password', 'confirm_password'] as InitField[]).forEach((field) => {
    const message = getFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  fieldErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 Submit 交互逻辑。
async function handleSubmit() {
  if (!validateForm()) {
    errorMsg.value = Object.values(fieldErrors.value).find(Boolean) || ''
    return
  }

  errorMsg.value = ''
  submitting.value = true
  try {
    const res = await systemApi.initSetup(form)
    if (res.code === 0 && res.data) {
      setTokens(res.data.access_token, res.data.refresh_token)
      await auth.fetchMe()
      resetInitCache()
      router.replace('/admin')
    } else {
      fieldErrors.value = {
        ...fieldErrors.value,
        ...extractApiFieldErrors(res, {
          confirm_password: '确认密码',
          password: '密码',
          username: '管理员用户名',
        }),
      }
      if (res.code === 4030) {
        errorMsg.value = '系统已初始化，请直接前往登录页，或使用现有系统管理员账号登录。'
      } else {
        errorMsg.value = extractApiError(res, '创建失败，请重试')
      }
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

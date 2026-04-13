<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">个人资料</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6">
      <div class="flex flex-col items-center">
        <div class="relative">
          <img :src="form.avatar || '/default-avatar.svg'" class="h-24 w-24 rounded-full border-4 border-white object-cover shadow" />
          <label class="absolute bottom-0 right-0 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-brand text-white shadow">
            <span class="text-xs">📷</span>
            <input type="file" accept="image/*" class="hidden" @change="handleAvatar" />
          </label>
        </div>
        <p class="mt-3 text-xs text-gray-400">支持 JPG、PNG 等常见图片格式，建议控制在 5MB 内。</p>
      </div>

      <div class="mt-6 space-y-4">
        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">昵称</label>
          <input
            v-model="form.nickname"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="profileErrors.nickname ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
            placeholder="选填，最多100个字符"
            @input="clearProfileError('nickname')"
            @blur="validateProfileField('nickname')"
          />
          <p v-if="profileErrors.nickname" class="mt-1 text-xs text-red-500">{{ profileErrors.nickname }}</p>
          <p v-else class="mt-1 text-xs text-gray-400">昵称会展示在个人中心和部分互动场景中。</p>
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">手机号</label>
          <input
            v-model="form.mobile"
            inputmode="numeric"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="profileErrors.mobile ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
            placeholder="请输入11位手机号"
            @input="handleMobileInput"
            @blur="validateProfileField('mobile')"
          />
          <p v-if="profileErrors.mobile" class="mt-1 text-xs text-red-500">{{ profileErrors.mobile }}</p>
          <p v-else class="mt-1 text-xs text-gray-400">用于接收订单提醒、入住通知等重要信息。</p>
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">邮箱</label>
          <input
            v-model="form.email"
            type="email"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="profileErrors.email ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
            placeholder="选填，用于接收账单或通知"
            @input="clearProfileError('email')"
            @blur="validateProfileField('email')"
          />
          <p v-if="profileErrors.email" class="mt-1 text-xs text-red-500">{{ profileErrors.email }}</p>
          <p v-else class="mt-1 text-xs text-gray-400">填写有效邮箱后，可接收电子发票和服务通知。</p>
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">性别</label>
          <div class="mt-1 flex gap-4">
            <label v-for="opt in genderOpts" :key="opt.value" class="flex items-center gap-1 text-sm">
              <input type="radio" v-model="form.gender" :value="opt.value" class="accent-brand" /> {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">生日</label>
          <input
            v-model="form.birthday"
            :max="today"
            type="date"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="profileErrors.birthday ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
            @input="clearProfileError('birthday')"
            @blur="validateProfileField('birthday')"
          />
          <p v-if="profileErrors.birthday" class="mt-1 text-xs text-red-500">{{ profileErrors.birthday }}</p>
          <p v-else class="mt-1 text-xs text-gray-400">填写后可用于生日权益和个性化服务推荐。</p>
        </div>

        <button
          @click="handleSave"
          :disabled="saving"
          class="w-full rounded-2xl bg-brand py-3 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存修改' }}
        </button>
      </div>

      <div class="mt-8">
        <h3 class="mb-3 font-semibold text-gray-800">修改密码</h3>
        <div class="space-y-3 rounded-2xl bg-white p-4 shadow-sm">
          <input
            v-model="pw.old_password"
            type="password"
            placeholder="当前密码"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="passwordErrors.old_password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
            @input="clearPasswordError('old_password')"
            @blur="validatePasswordField('old_password')"
          />
          <p v-if="passwordErrors.old_password" class="text-xs text-red-500">{{ passwordErrors.old_password }}</p>

          <div>
            <input
              v-model="pw.new_password"
              type="password"
              placeholder="新密码（至少8位）"
              class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
              :class="passwordErrors.new_password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="clearPasswordError('new_password')"
              @blur="validatePasswordField('new_password')"
            />
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
            <p v-if="passwordErrors.new_password" class="mt-1 text-xs text-red-500">{{ passwordErrors.new_password }}</p>
          </div>

          <input
            v-model="pw.confirm_password"
            type="password"
            placeholder="确认新密码"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="passwordErrors.confirm_password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
            @input="clearPasswordError('confirm_password')"
            @blur="validatePasswordField('confirm_password')"
          />
          <p v-if="passwordErrors.confirm_password" class="text-xs text-red-500">{{ passwordErrors.confirm_password }}</p>

          <button
            @click="handleChangePw"
            :disabled="changingPw"
            class="w-full rounded-xl border border-brand py-2.5 text-sm font-medium text-brand hover:bg-teal-50 disabled:opacity-50"
          >
            {{ changingPw ? '修改中...' : '修改密码' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { userProfileApi } from '@hotelink/api'
import { useUserAuthStore } from '@hotelink/store'
import { useToast } from '@hotelink/ui'
import {
  extractApiError,
  extractApiFieldErrors,
  formatDate,
  getPasswordStrength,
  isValidChineseMobile,
  isValidEmailAddress,
  validatePassword,
} from '@hotelink/utils'

type ProfileField = 'nickname' | 'mobile' | 'email' | 'birthday'
type PasswordField = 'old_password' | 'new_password' | 'confirm_password'

const { showToast } = useToast()

const authStore = useUserAuthStore()
const saving = ref(false)
const changingPw = ref(false)
const today = formatDate(new Date())
const genderOpts = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' },
  { label: '保密', value: 'unknown' },
]

const form = ref({
  avatar: '',
  nickname: '',
  mobile: '',
  email: '',
  gender: 'unknown',
  birthday: '',
})

const pw = ref({ old_password: '', new_password: '', confirm_password: '' })
const profileErrors = ref<Partial<Record<ProfileField, string>>>({})
const passwordErrors = ref<Partial<Record<PasswordField, string>>>({})

const passwordStrength = computed(() => getPasswordStrength(pw.value.new_password, 8))
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

function clearProfileError(field: ProfileField) {
  if (profileErrors.value[field]) {
    profileErrors.value = { ...profileErrors.value, [field]: undefined }
  }
}

function clearPasswordError(field: PasswordField) {
  if (passwordErrors.value[field]) {
    passwordErrors.value = { ...passwordErrors.value, [field]: undefined }
  }
}

function handleMobileInput() {
  form.value.mobile = form.value.mobile.replace(/\D/g, '').slice(0, 11)
  clearProfileError('mobile')
}

function getProfileFieldError(field: ProfileField): string {
  switch (field) {
    case 'nickname':
      return form.value.nickname.trim().length > 100 ? '昵称不能超过 100 个字符' : ''
    case 'mobile':
      if (!form.value.mobile.trim()) return ''
      return isValidChineseMobile(form.value.mobile) ? '' : '请输入有效的 11 位手机号'
    case 'email':
      if (!form.value.email.trim()) return ''
      return isValidEmailAddress(form.value.email) ? '' : '邮箱格式不正确'
    case 'birthday':
      if (!form.value.birthday) return ''
      return form.value.birthday > today ? '生日不能晚于今天' : ''
    default:
      return ''
  }
}

function validateProfileField(field: ProfileField) {
  profileErrors.value = {
    ...profileErrors.value,
    [field]: getProfileFieldError(field) || undefined,
  }
}

function validateProfileForm(): boolean {
  const nextErrors: Partial<Record<ProfileField, string>> = {}
  form.value.nickname = form.value.nickname.trim()
  form.value.email = form.value.email.trim()

  ;(['nickname', 'mobile', 'email', 'birthday'] as ProfileField[]).forEach((field) => {
    const message = getProfileFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  profileErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

function getPasswordFieldError(field: PasswordField): string {
  switch (field) {
    case 'old_password':
      return pw.value.old_password ? '' : '请输入当前密码'
    case 'new_password':
      if (pw.value.new_password === pw.value.old_password && pw.value.new_password) {
        return '新密码不能与当前密码相同'
      }
      return validatePassword(pw.value.new_password, { label: '新密码', minLength: 8 })
    case 'confirm_password':
      if (!pw.value.confirm_password) return '请再次输入新密码'
      return pw.value.new_password === pw.value.confirm_password ? '' : '两次输入的新密码不一致'
    default:
      return ''
  }
}

function validatePasswordField(field: PasswordField) {
  passwordErrors.value = {
    ...passwordErrors.value,
    [field]: getPasswordFieldError(field) || undefined,
  }
}

function validatePasswordForm(): boolean {
  const nextErrors: Partial<Record<PasswordField, string>> = {}
  ;(['old_password', 'new_password', 'confirm_password'] as PasswordField[]).forEach((field) => {
    const message = getPasswordFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })
  passwordErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 Avatar 交互逻辑。
async function handleAvatar(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    showToast('请上传图片格式的头像文件', 'warning')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('头像大小请控制在 5MB 以内', 'warning')
    return
  }

  try {
    const res = await userProfileApi.uploadAvatar(file)
    if (res.code === 0 && (res.data as any)?.avatar) {
      form.value.avatar = (res.data as any).avatar
      showToast('头像已更新', 'success')
    } else {
      showToast(extractApiError(res, '头像上传失败，请稍后重试'), 'error')
    }
  } catch {
    showToast('头像上传失败，请稍后重试', 'error')
  }
}

// 处理 Save 交互逻辑。
async function handleSave() {
  if (!validateProfileForm()) {
    showToast(Object.values(profileErrors.value).find(Boolean) || '请检查填写内容', 'warning')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form.value,
      nickname: form.value.nickname.trim(),
      email: form.value.email.trim(),
      mobile: form.value.mobile.trim(),
    }
    const res = await userProfileApi.update(payload)
    if (res.code === 0) {
      await authStore.fetchMe()
      showToast('保存成功', 'success')
    } else {
      profileErrors.value = {
        ...profileErrors.value,
        ...extractApiFieldErrors(res, {
          birthday: '生日',
          email: '邮箱',
          mobile: '手机号',
          nickname: '昵称',
        }),
      }
      showToast(extractApiError(res, '保存失败，请检查填写内容'), 'error')
    }
  } catch {
    showToast('保存失败，请稍后重试', 'error')
  } finally {
    saving.value = false
  }
}

// 处理 ChangePw 交互逻辑。
async function handleChangePw() {
  if (!validatePasswordForm()) {
    showToast(Object.values(passwordErrors.value).find(Boolean) || '请检查密码填写', 'warning')
    return
  }

  changingPw.value = true
  try {
    const res = await userProfileApi.changePassword(pw.value)
    if (res.code === 0) {
      showToast('密码修改成功', 'success')
      pw.value = { old_password: '', new_password: '', confirm_password: '' }
      passwordErrors.value = {}
    } else {
      const apiErrors = extractApiFieldErrors(res, {
        confirm_password: '确认密码',
        new_password: '新密码',
        old_password: '当前密码',
      })
      passwordErrors.value = { ...passwordErrors.value, ...apiErrors }
      if (res.message === '旧密码不正确') {
        passwordErrors.value.old_password = '当前密码不正确'
      }
      showToast(extractApiError(res, '密码修改失败，请检查填写内容'), 'error')
    }
  } catch {
    showToast('密码修改失败，请稍后重试', 'error')
  } finally {
    changingPw.value = false
  }
}

onMounted(async () => {
  try {
    const res = await userProfileApi.get()
    if (res.code === 0 && res.data) {
      Object.assign(form.value, res.data)
    }
  } catch {
    form.value = {
      avatar: '',
      nickname: authStore.user?.username || '',
      mobile: '',
      email: '',
      gender: 'unknown',
      birthday: '',
    }
  }
})
</script>

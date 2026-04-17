<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">账号与安全</h1>
    </header>

    <div class="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <section class="rounded-2xl bg-gradient-to-r from-brand to-teal-500 p-4 text-white shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold">账号安全指数</p>
            <p class="mt-1 text-xs text-white/80">{{ securityLevel.description }}</p>
          </div>
          <span class="rounded-full bg-white/20 px-2.5 py-1 text-xs font-semibold">{{ securityLevel.label }}等级</span>
        </div>
        <div class="mt-3 h-2 overflow-hidden rounded-full bg-white/25">
          <div class="h-full rounded-full bg-white transition-all" :style="{ width: `${securityProgress}%` }" />
        </div>
        <p class="mt-2 text-xs text-white/80">账号：{{ authStore.user?.username || '-' }}</p>
      </section>

      <section class="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
        <div class="px-4 py-3 text-sm font-semibold text-gray-800">联系方式</div>
        <button type="button" class="group flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-gray-50" @click="openSheet('mobile')">
          <span class="text-sm text-gray-700">手机号</span>
          <span class="ml-auto text-sm text-gray-400">{{ maskedMobile }}</span>
          <span class="text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
        <button type="button" class="group flex w-full items-center gap-3 border-t border-gray-100 px-4 py-3 text-left transition hover:bg-gray-50" @click="openSheet('email')">
          <span class="text-sm text-gray-700">邮箱</span>
          <span class="ml-auto text-sm text-gray-400">{{ maskedEmail }}</span>
          <span class="text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
      </section>

      <section class="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
        <div class="px-4 py-3 text-sm font-semibold text-gray-800">账号保护</div>
        <button type="button" class="group flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-gray-50" @click="openSheet('password')">
          <span class="text-sm text-gray-700">登录密码</span>
          <span class="ml-auto text-sm text-gray-400">建议定期更新</span>
          <span class="text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
        <button type="button" class="group flex w-full items-center gap-3 border-t border-gray-100 px-4 py-3 text-left transition hover:bg-gray-50" @click="showPlannedHint('登录方式')">
          <span class="text-sm text-gray-700">登录方式</span>
          <span class="ml-auto text-sm text-gray-400">密码登录</span>
          <span class="text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
        <button type="button" class="group flex w-full items-center gap-3 border-t border-gray-100 px-4 py-3 text-left transition hover:bg-gray-50" @click="openSheet('protection')">
          <span class="text-sm text-gray-700">高安全防护</span>
          <span class="ml-auto text-sm text-gray-400">{{ protectionSummary }}</span>
          <span class="text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
      </section>

      <section class="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
        <div class="px-4 py-3 text-sm font-semibold text-gray-800">身份与账号</div>
        <button type="button" class="group flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-gray-50" @click="showPlannedHint('身份信息')">
          <span class="text-sm text-gray-700">身份信息</span>
          <span class="ml-auto text-sm text-gray-400">已绑定基础资料</span>
          <span class="text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
        <button type="button" class="group flex w-full items-center gap-3 border-t border-gray-100 px-4 py-3 text-left transition hover:bg-gray-50" @click="showPlannedHint('名下其他账号')">
          <div>
            <p class="text-sm text-gray-700">名下其他账号</p>
            <p class="mt-1 text-xs text-gray-400">查看同身份已认证账号</p>
          </div>
          <span class="ml-auto text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
      </section>

      <section class="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
        <button type="button" class="group flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-gray-50" @click="showPlannedHint('安全中心')">
          <div>
            <p class="text-sm font-medium text-gray-700">安全中心</p>
            <p class="mt-1 text-xs text-gray-400">账号挂失、解限、举报等安全服务</p>
          </div>
          <span class="ml-auto text-xl leading-none text-gray-300 transition group-hover:text-brand">›</span>
        </button>
      </section>

      <section class="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
        <button type="button" class="group flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-red-50/60" @click="showPlannedHint('账号注销')">
          <div>
            <p class="text-sm font-medium text-red-500">账号注销</p>
            <p class="mt-1 text-xs text-red-300">删除账号所有数据，注销后不可恢复</p>
          </div>
          <span class="ml-auto text-xl leading-none text-red-200 transition group-hover:text-red-400">›</span>
        </button>
      </section>
    </div>

    <Transition name="sheet-fade">
      <div v-if="activeSheet" class="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
        <button type="button" class="absolute inset-0 bg-black/30" @click="closeSheet" aria-label="关闭面板"></button>

        <div class="relative z-10 w-full rounded-t-3xl bg-white p-4 shadow-2xl sm:max-w-md sm:rounded-2xl">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-gray-800">{{ sheetTitle }}</h3>
            <button type="button" class="rounded-lg px-2 py-1 text-xs text-gray-500 transition hover:bg-gray-100" @click="closeSheet">关闭</button>
          </div>

          <div v-if="activeSheet === 'mobile' || activeSheet === 'email'" class="space-y-3">
            <label class="block text-xs text-gray-500">{{ activeSheet === 'mobile' ? '手机号' : '邮箱' }}</label>
            <input
              v-model="editDraft"
              :type="activeSheet === 'mobile' ? 'text' : 'email'"
              :inputmode="activeSheet === 'mobile' ? 'numeric' : undefined"
              :placeholder="activeSheet === 'mobile' ? '请输入11位手机号' : '请输入常用邮箱'"
              class="w-full rounded-xl border px-3 py-2 text-sm outline-none transition"
              :class="editError ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="handleEditableInput"
            />
            <p v-if="editError" class="text-xs text-red-500">{{ editError }}</p>
            <p v-else class="text-xs text-gray-400">联系方式仅用于登录校验、安全提醒与订单通知。</p>

            <button
              type="button"
              class="w-full rounded-xl bg-brand py-2.5 text-sm font-medium text-white transition hover:bg-brand-dark disabled:opacity-50"
              :disabled="contactSubmitting"
              @click="saveEditableField"
            >
              {{ contactSubmitting ? '保存中...' : '保存' }}
            </button>
          </div>

          <div v-else-if="activeSheet === 'password'" class="space-y-3">
            <input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="当前密码"
              class="w-full rounded-xl border px-3 py-2 text-sm outline-none transition"
              :class="passwordErrors.old_password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="clearPasswordError('old_password')"
              @blur="validatePasswordField('old_password')"
            />
            <p v-if="passwordErrors.old_password" class="text-xs text-red-500">{{ passwordErrors.old_password }}</p>

            <div>
              <input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="新密码（至少8位）"
                class="w-full rounded-xl border px-3 py-2 text-sm outline-none transition"
                :class="passwordErrors.new_password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="clearPasswordError('new_password')"
                @blur="validatePasswordField('new_password')"
              />
              <div class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
                <div class="h-full rounded-full transition-all" :class="passwordStrengthBarClass" :style="{ width: `${passwordStrength.percentage}%` }" />
              </div>
              <p class="mt-1 text-xs" :class="passwordStrengthTextClass">密码强度：{{ passwordStrength.label }}，{{ passwordStrength.hint }}</p>
              <p v-if="passwordErrors.new_password" class="mt-1 text-xs text-red-500">{{ passwordErrors.new_password }}</p>
            </div>

            <input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="确认新密码"
              class="w-full rounded-xl border px-3 py-2 text-sm outline-none transition"
              :class="passwordErrors.confirm_password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="clearPasswordError('confirm_password')"
              @blur="validatePasswordField('confirm_password')"
            />
            <p v-if="passwordErrors.confirm_password" class="text-xs text-red-500">{{ passwordErrors.confirm_password }}</p>

            <button
              type="button"
              class="w-full rounded-xl bg-brand py-2.5 text-sm font-medium text-white transition hover:bg-brand-dark disabled:opacity-50"
              :disabled="changingPassword"
              @click="changePassword"
            >
              {{ changingPassword ? '修改中...' : '修改密码' }}
            </button>
          </div>

          <div v-else-if="activeSheet === 'protection'" class="space-y-3 text-sm">
            <label class="flex items-center justify-between rounded-xl border border-gray-100 px-3 py-2">
              <div>
                <p class="font-medium text-gray-700">新设备登录提醒</p>
                <p class="text-xs text-gray-400">检测到新设备登录时发送提醒</p>
              </div>
              <input v-model="securityPrefs.newDeviceAlert" type="checkbox" class="h-4 w-4 accent-brand" />
            </label>

            <label class="flex items-center justify-between rounded-xl border border-gray-100 px-3 py-2">
              <div>
                <p class="font-medium text-gray-700">敏感操作二次确认</p>
                <p class="text-xs text-gray-400">修改密码、支付等操作需额外确认</p>
              </div>
              <input v-model="securityPrefs.sensitiveActionConfirm" type="checkbox" class="h-4 w-4 accent-brand" />
            </label>

            <label class="flex items-center justify-between rounded-xl border border-gray-100 px-3 py-2">
              <div>
                <p class="font-medium text-gray-700">异地登录高风险拦截</p>
                <p class="text-xs text-gray-400">对异常地区登录进行额外校验</p>
              </div>
              <input v-model="securityPrefs.riskBlock" type="checkbox" class="h-4 w-4 accent-brand" />
            </label>

            <p class="text-xs text-gray-400">以上设置会保存到当前账号安全偏好中。</p>
            <button type="button" class="w-full rounded-xl border border-brand/30 bg-brand/5 py-2.5 text-sm font-medium text-brand transition hover:bg-brand/10" @click="closeSheet">
              完成
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { userProfileApi } from '@hotelink/api'
import { useUserAuthStore } from '@hotelink/store'
import { useToast } from '@hotelink/ui'
import {
  extractApiError,
  extractApiFieldErrors,
  getPasswordStrength,
  isValidChineseMobile,
  isValidEmailAddress,
  validatePassword,
} from '@hotelink/utils'

type ActiveSheet = 'mobile' | 'email' | 'password' | 'protection' | null
type PasswordField = 'old_password' | 'new_password' | 'confirm_password'

const SECURITY_PREFS_KEY = 'hotelink_user_security_prefs'

const { showToast } = useToast()
const authStore = useUserAuthStore()

const activeSheet = ref<ActiveSheet>(null)
const securityForm = ref({
  mobile: '',
  email: '',
})

const securityPrefs = ref({
  newDeviceAlert: true,
  sensitiveActionConfirm: true,
  riskBlock: true,
})

const editDraft = ref('')
const editError = ref('')
const contactSubmitting = ref(false)
const changingPassword = ref(false)

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordErrors = ref<Partial<Record<PasswordField, string>>>({})

const enabledProtectionCount = computed(() =>
  Object.values(securityPrefs.value).filter(Boolean).length
)

const securityScore = computed(() => {
  let score = enabledProtectionCount.value
  if (securityForm.value.mobile.trim()) score += 1
  if (securityForm.value.email.trim()) score += 1
  return score
})

const securityProgress = computed(() => Math.min(100, Math.round((securityScore.value / 5) * 100)))

const securityLevel = computed(() => {
  const score = securityScore.value
  if (score >= 4) {
    return { label: '高', description: '防护配置完善，账号安全性较高。' }
  }
  if (score >= 2) {
    return { label: '中', description: '建议补充联系方式并开启更多高安全项。' }
  }
  return { label: '低', description: '建议尽快完成联系方式与高风险防护配置。' }
})

const protectionSummary = computed(() => {
  if (enabledProtectionCount.value <= 0) return '未开启'
  if (enabledProtectionCount.value >= 3) return '全部开启'
  return `已开启${enabledProtectionCount.value}/3项`
})

const maskedMobile = computed(() => {
  const mobile = securityForm.value.mobile.trim()
  if (!mobile) return '待添加'
  if (mobile.length < 7) return mobile
  return `${mobile.slice(0, 3)}****${mobile.slice(-2)}`
})

const maskedEmail = computed(() => {
  const email = securityForm.value.email.trim()
  if (!email) return '待添加'
  const parts = email.split('@')
  if (parts.length !== 2) return email
  const [name, domain] = parts
  if (!name) return `*@${domain}`
  if (name.length === 1) return `${name}*@${domain}`
  return `${name.slice(0, 1)}***@${domain}`
})

const sheetTitle = computed(() => {
  if (activeSheet.value === 'mobile') return '修改手机号'
  if (activeSheet.value === 'email') return '修改邮箱'
  if (activeSheet.value === 'password') return '修改登录密码'
  if (activeSheet.value === 'protection') return '高安全防护设置'
  return '账号与安全'
})

const passwordStrength = computed(() => getPasswordStrength(passwordForm.value.new_password, 8))

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

function openSheet(type: Exclude<ActiveSheet, null>) {
  activeSheet.value = type
  editError.value = ''
  if (type === 'mobile') {
    editDraft.value = securityForm.value.mobile
  }
  if (type === 'email') {
    editDraft.value = securityForm.value.email
  }
}

function closeSheet() {
  activeSheet.value = null
  editError.value = ''
}

function showPlannedHint(label: string) {
  showToast(`${label}能力正在规划中`, 'warning')
}

function handleEditableInput() {
  if (activeSheet.value === 'mobile') {
    editDraft.value = editDraft.value.replace(/\D/g, '').slice(0, 11)
  }
  if (editError.value) {
    editError.value = ''
  }
}

function getEditableError(): string {
  if (activeSheet.value === 'mobile') {
    const value = editDraft.value.trim()
    if (!value) return ''
    return isValidChineseMobile(value) ? '' : '请输入有效的 11 位手机号'
  }
  if (activeSheet.value === 'email') {
    const value = editDraft.value.trim()
    if (!value) return ''
    return isValidEmailAddress(value) ? '' : '邮箱格式不正确'
  }
  return ''
}

async function saveEditableField() {
  if (activeSheet.value !== 'mobile' && activeSheet.value !== 'email') return

  const field = activeSheet.value
  const value = field === 'mobile'
    ? editDraft.value.replace(/\D/g, '').slice(0, 11).trim()
    : editDraft.value.trim()

  const message = getEditableError()
  if (message) {
    editError.value = message
    showToast(message, 'warning')
    return
  }

  contactSubmitting.value = true
  try {
    const res = await userProfileApi.update({ [field]: value })
    if (res.code === 0) {
      securityForm.value[field] = value
      await authStore.fetchMe()
      showToast(field === 'mobile' ? '手机号已更新' : '邮箱已更新', 'success')
      closeSheet()
    } else {
      const apiErrors = extractApiFieldErrors(res, {
        email: '邮箱',
        mobile: '手机号',
      })
      editError.value = apiErrors[field] || extractApiError(res, '保存失败，请检查填写内容')
      showToast(extractApiError(res, '保存失败，请检查填写内容'), 'error')
    }
  } catch {
    showToast('保存失败，请稍后重试', 'error')
  } finally {
    contactSubmitting.value = false
  }
}

function clearPasswordError(field: PasswordField) {
  if (passwordErrors.value[field]) {
    passwordErrors.value = { ...passwordErrors.value, [field]: undefined }
  }
}

function getPasswordFieldError(field: PasswordField): string {
  switch (field) {
    case 'old_password':
      return passwordForm.value.old_password ? '' : '请输入当前密码'
    case 'new_password':
      if (passwordForm.value.new_password === passwordForm.value.old_password && passwordForm.value.new_password) {
        return '新密码不能与当前密码相同'
      }
      return validatePassword(passwordForm.value.new_password, { label: '新密码', minLength: 8 })
    case 'confirm_password':
      if (!passwordForm.value.confirm_password) return '请再次输入新密码'
      return passwordForm.value.new_password === passwordForm.value.confirm_password ? '' : '两次输入的新密码不一致'
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

async function changePassword() {
  if (!validatePasswordForm()) {
    showToast(Object.values(passwordErrors.value).find(Boolean) || '请检查密码填写', 'warning')
    return
  }

  changingPassword.value = true
  try {
    const res = await userProfileApi.changePassword(passwordForm.value)
    if (res.code === 0) {
      showToast('密码修改成功', 'success')
      passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
      passwordErrors.value = {}
      closeSheet()
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
    changingPassword.value = false
  }
}

function loadSecurityPrefs() {
  try {
    const raw = localStorage.getItem(SECURITY_PREFS_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw) as Partial<typeof securityPrefs.value>
    securityPrefs.value = {
      ...securityPrefs.value,
      ...parsed,
    }
  } catch {
    // ignore invalid local cache
  }
}

async function loadSecurityProfile() {
  try {
    const res = await userProfileApi.get()
    if (res.code === 0 && res.data) {
      securityForm.value.mobile = (res.data as any).mobile || ''
      securityForm.value.email = (res.data as any).email || ''
    }
  } catch {
    securityForm.value.mobile = authStore.user?.mobile || ''
    securityForm.value.email = authStore.user?.email || ''
  }
}

watch(
  securityPrefs,
  (value) => {
    localStorage.setItem(SECURITY_PREFS_KEY, JSON.stringify(value))
  },
  { deep: true }
)

onMounted(() => {
  loadSecurityPrefs()
  void loadSecurityProfile()
})
</script>

<style scoped>
.sheet-fade-enter-active,
.sheet-fade-leave-active {
  transition: opacity 180ms ease;
}

.sheet-fade-enter-from,
.sheet-fade-leave-to {
  opacity: 0;
}
</style>

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

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userProfileApi } from '@hotelink/api'
import { useUserAuthStore } from '@hotelink/store'
import { useToast } from '@hotelink/ui'
import { extractApiError, extractApiFieldErrors, formatDate } from '@hotelink/utils'

type ProfileField = 'nickname' | 'birthday'

const { showToast } = useToast()
const authStore = useUserAuthStore()
const saving = ref(false)
const today = formatDate(new Date())
const genderOpts = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' },
  { label: '保密', value: 'unknown' },
]

const form = ref({
  avatar: '',
  nickname: '',
  gender: 'unknown',
  birthday: '',
})

const profileErrors = ref<Partial<Record<ProfileField, string>>>({})

function clearProfileError(field: ProfileField) {
  if (profileErrors.value[field]) {
    profileErrors.value = { ...profileErrors.value, [field]: undefined }
  }
}

function getProfileFieldError(field: ProfileField): string {
  switch (field) {
    case 'nickname':
      return form.value.nickname.trim().length > 100 ? '昵称不能超过 100 个字符' : ''
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

  ;(['nickname', 'birthday'] as ProfileField[]).forEach((field) => {
    const message = getProfileFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  profileErrors.value = nextErrors
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
      nickname: form.value.nickname.trim(),
      gender: form.value.gender,
      birthday: form.value.birthday || null,
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

onMounted(async () => {
  try {
    const res = await userProfileApi.get()
    if (res.code === 0 && res.data) {
      form.value.avatar = (res.data as any).avatar || ''
      form.value.nickname = (res.data as any).nickname || ''
      form.value.gender = (res.data as any).gender || 'unknown'
      form.value.birthday = (res.data as any).birthday || ''
    }
  } catch {
    form.value = {
      avatar: '',
      nickname: authStore.user?.username || '',
      gender: 'unknown',
      birthday: '',
    }
  }
})
</script>

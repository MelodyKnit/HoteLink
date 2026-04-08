<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">个人资料</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6">
      <!-- Avatar -->
      <div class="flex flex-col items-center">
        <div class="relative">
          <img :src="form.avatar || '/default-avatar.svg'" class="h-24 w-24 rounded-full border-4 border-white object-cover shadow" />
          <label class="absolute bottom-0 right-0 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-brand text-white shadow">
            <span class="text-xs">📷</span>
            <input type="file" accept="image/*" class="hidden" @change="handleAvatar" />
          </label>
        </div>
      </div>

      <!-- Form -->
      <div class="mt-6 space-y-4">
        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">昵称</label>
          <input v-model="form.nickname" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">手机号</label>
          <input v-model="form.mobile" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm">
          <label class="mb-1 block text-xs text-gray-400">邮箱</label>
          <input v-model="form.email" type="email" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
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
          <input v-model="form.birthday" type="date" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
        </div>

        <button @click="handleSave" :disabled="saving"
          class="w-full rounded-2xl bg-brand py-3 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50">
          {{ saving ? '保存中...' : '保存修改' }}
        </button>
      </div>

      <!-- Change Password -->
      <div class="mt-8">
        <h3 class="mb-3 font-semibold text-gray-800">修改密码</h3>
        <div class="space-y-3 rounded-2xl bg-white p-4 shadow-sm">
          <input v-model="pw.old_password" type="password" placeholder="当前密码" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <input v-model="pw.new_password" type="password" placeholder="新密码" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <input v-model="pw.confirm_password" type="password" placeholder="确认新密码" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <button @click="handleChangePw" :disabled="changingPw"
            class="w-full rounded-xl border border-brand py-2.5 text-sm font-medium text-brand hover:bg-teal-50 disabled:opacity-50">
            {{ changingPw ? '修改中...' : '修改密码' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userProfileApi } from '@hotelink/api'
import { useUserAuthStore } from '@hotelink/store'
import { useToast } from '@hotelink/ui'

const { showToast } = useToast()

const authStore = useUserAuthStore()
const saving = ref(false)
const changingPw = ref(false)
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

// 处理 Avatar 交互逻辑。
async function handleAvatar(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    const res = await userProfileApi.uploadAvatar(file)
    if (res.code === 0 && (res.data as any)?.avatar) { form.value.avatar = (res.data as any).avatar }
  } catch {
    form.value.avatar = URL.createObjectURL(file)
  }
}

// 处理 Save 交互逻辑。
async function handleSave() {
  saving.value = true
  try {
    const res = await userProfileApi.update(form.value)
    if (res.code === 0) {
      await authStore.fetchMe()
      showToast('保存成功', 'success')
    } else {
      showToast((res as any).message || '保存失败', 'error')
    }
  } catch { /* ignore */ }
  saving.value = false
}

// 处理 ChangePw 交互逻辑。
async function handleChangePw() {
  if (pw.value.new_password !== pw.value.confirm_password) { showToast('两次密码不一致', 'error'); return }
  if (pw.value.new_password.length < 6) { showToast('密码至6位', 'warning'); return }
  changingPw.value = true
  try {
    const res = await userProfileApi.changePassword(pw.value)
    if (res.code === 0) {
      showToast('密码修改成功', 'success')
      pw.value = { old_password: '', new_password: '', confirm_password: '' }
    } else {
      showToast((res as any).message || '密码修改失败', 'error')
    }
  } catch { /* ignore */ }
  changingPw.value = false
}

onMounted(async () => {
  try {
    const res = await userProfileApi.get()
    if (res.code === 0 && res.data) Object.assign(form.value, res.data)
  } catch {
    form.value = { avatar: '', nickname: authStore.user?.username || '', mobile: '', email: '', gender: 'unknown', birthday: '' }
  }
})
</script>

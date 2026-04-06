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
              required
              minlength="3"
              maxlength="150"
              autocomplete="username"
              placeholder="至少 3 个字符"
              class="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">密码</label>
            <input
              v-model="form.password"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
              placeholder="至少 6 个字符"
              class="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">确认密码</label>
            <input
              v-model="form.confirm_password"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
              placeholder="再次输入密码"
              class="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            />
          </div>
        </div>

        <p v-if="errorMsg" class="mt-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">{{ errorMsg }}</p>

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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { systemApi, setTokens } from '@hotelink/api'
import { useAuthStore } from '@hotelink/store'
import { resetInitCache } from '../router'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ username: '', password: '', confirm_password: '' })
const submitting = ref(false)
const errorMsg = ref('')

// 处理 Submit 交互逻辑。
async function handleSubmit() {
  errorMsg.value = ''

  if (form.password !== form.confirm_password) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  submitting.value = true
  try {
    const res = await systemApi.initSetup(form)
    if (res.code === 0 && res.data) {
      setTokens(res.data.access_token, res.data.refresh_token)
      await auth.fetchMe()
      resetInitCache()
      router.replace('/admin')
    } else {
      errorMsg.value = res.message || '创建失败，请重试'
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

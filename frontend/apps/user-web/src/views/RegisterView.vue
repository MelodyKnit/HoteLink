<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-dark to-brand px-4 py-10">
    <div class="w-full max-w-sm">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-white">HoteLink</h1>
        <p class="mt-1 text-sm text-teal-200">创建新账户</p>
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-xl">
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">用户名 *</label>
            <input v-model="form.username" type="text" placeholder="4-30位字符" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">手机号 *</label>
            <input v-model="form.mobile" type="tel" placeholder="请输入手机号" maxlength="11" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">密码 *</label>
            <input v-model="form.password" type="password" placeholder="请设置密码" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">确认密码 *</label>
            <input v-model="form.confirm_password" type="password" placeholder="再次输入密码" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand" @keyup.enter="handleRegister" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">邮箱</label>
            <input v-model="form.email" type="email" placeholder="选填" class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand" />
          </div>
        </div>

        <button @click="handleRegister" :disabled="loading" class="mt-6 w-full rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
          {{ loading ? '注册中...' : '注册' }}
        </button>

        <p v-if="error" class="mt-3 text-center text-sm text-red-500">{{ error }}</p>

        <div class="mt-6 text-center">
          <router-link to="/login" class="text-sm text-brand hover:underline">已有账号？去登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserAuthStore } from '@hotelink/store'

const router = useRouter()
const auth = useUserAuthStore()
const loading = ref(false)
const error = ref('')

const form = ref({
  username: '',
  mobile: '',
  password: '',
  confirm_password: '',
  email: '',
})

// 处理 Register 交互逻辑。
async function handleRegister() {
  const f = form.value
  if (!f.username || !f.mobile || !f.password || !f.confirm_password) { error.value = '请填写所有必填项'; return }
  if (f.password !== f.confirm_password) { error.value = '两次密码不一致'; return }
  if (f.mobile.length !== 11) { error.value = '手机号格式不正确'; return }

  loading.value = true
  error.value = ''
  try {
    const res = await auth.register({
      username: f.username,
      password: f.password,
      confirm_password: f.confirm_password,
      mobile: f.mobile,
      email: f.email || undefined,
    })
    if (res.code === 0) {
      // Auto-login after registration
      const loginRes = await auth.login(f.username, f.password)
      if (loginRes.code === 0) {
        router.replace('/')
      } else {
        router.replace('/login')
      }
    } else {
      error.value = res.message || '注册失败'
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

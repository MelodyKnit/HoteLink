<template>
  <section>
    <PageHeader title="AI 配置" subtitle="管理多个 AI 供应商，支持一键切换" />

    <div v-if="loading" class="text-center py-20 text-slate-400">加载中…</div>

    <div v-else class="mx-auto max-w-3xl space-y-6">
      <!-- 全局开关 -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-semibold">AI 功能总开关</h3>
            <p class="text-sm text-slate-500">关闭后所有 AI 功能将使用兜底回复</p>
          </div>
          <label class="relative inline-flex cursor-pointer items-center">
            <input v-model="aiEnabled" type="checkbox" class="peer sr-only" @change="toggleEnabled" />
            <div class="peer h-6 w-11 rounded-full bg-slate-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-teal-600 peer-checked:after:translate-x-full"></div>
          </label>
        </div>
      </div>

      <!-- 供应商列表 -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-base font-semibold">AI 供应商列表</h3>
          <button class="rounded-lg bg-teal-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-teal-700" @click="openAddForm">
            + 添加供应商
          </button>
        </div>

        <div v-if="providers.length === 0" class="py-8 text-center text-sm text-slate-400">
          暂无供应商配置，请添加
        </div>

        <div v-else class="space-y-3">
          <div v-for="p in providers" :key="p.name"
               class="flex items-center justify-between rounded-xl border px-4 py-3 transition"
               :class="p.is_active ? 'border-teal-500 bg-teal-50' : 'border-slate-200 bg-slate-50'">
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-medium">{{ p.label || p.name }}</span>
                <StatusBadge v-if="p.is_active" label="当前使用" type="success" />
                <StatusBadge v-if="!p.api_key_configured" label="未配置密钥" type="warning" />
              </div>
              <p class="mt-1 text-xs text-slate-500">
                模型: {{ p.chat_model }} · {{ p.base_url }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button v-if="!p.is_active" class="rounded-lg bg-teal-100 px-3 py-1 text-xs font-medium text-teal-700 hover:bg-teal-200" @click="switchProvider(p.name)">
                切换使用
              </button>
              <button class="rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200" @click="openEditForm(p)">
                编辑
              </button>
              <button v-if="!p.is_active" class="rounded-lg bg-red-100 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-200" @click="deleteProvider(p.name)">
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 内置供应商快捷添加 -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-3 text-base font-semibold">快捷添加内置供应商</h3>
        <p class="mb-3 text-sm text-slate-500">选择后仅需填写 API Key 即可使用</p>
        <div class="flex flex-wrap gap-2">
          <button v-for="bp in builtinProviders" :key="bp"
                  class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:border-teal-500 hover:text-teal-600"
                  :class="providerNames.has(bp) ? 'opacity-50 cursor-not-allowed' : ''"
                  :disabled="providerNames.has(bp)"
                  @click="quickAdd(bp)">
            {{ bp }}
            <span v-if="providerNames.has(bp)" class="text-xs text-slate-400">(已添加)</span>
          </button>
        </div>
      </div>

      <!-- 添加/编辑供应商对话框 -->
      <div v-if="showForm" class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-base font-semibold">{{ isEditing ? '编辑供应商' : '添加供应商' }}</h3>
        <form class="space-y-4" @submit.prevent="saveProvider">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-medium">标识名称</label>
              <input v-model="form.name" :disabled="isEditing" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 disabled:bg-slate-100" placeholder="deepseek" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">显示名称</label>
              <input v-model="form.label" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="DeepSeek" />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">Base URL</label>
            <input v-model="form.base_url" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="https://api.deepseek.com" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">API Key（留空则不修改）</label>
            <input v-model="form.api_key" type="password" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="sk-..." />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-medium">Chat 模型</label>
              <input v-model="form.chat_model" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="deepseek-chat" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">Reasoning 模型</label>
              <input v-model="form.reasoning_model" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="deepseek-reasoner" />
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50" @click="showForm = false">取消</button>
            <button type="submit" class="rounded-lg bg-teal-600 px-6 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </form>
      </div>

      <p v-if="message" class="text-center text-sm" :class="messageType === 'success' ? 'text-green-600' : 'text-red-600'">{{ message }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { aiApi } from '@hotelink/api'
import { PageHeader, StatusBadge } from '@hotelink/ui'

interface ProviderInfo {
  name: string
  label: string
  base_url: string
  api_key_configured: boolean
  chat_model: string
  reasoning_model: string
  timeout: number
  is_active: boolean
}

const loading = ref(true)
const saving = ref(false)
const showForm = ref(false)
const isEditing = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const aiEnabled = ref(false)
const providers = ref<ProviderInfo[]>([])
const builtinProviders = ref<string[]>([])
const providerNames = computed(() => new Set(providers.value.map(p => p.name)))

const form = reactive({ name: '', label: '', base_url: '', api_key: '', chat_model: '', reasoning_model: '' })

// 显示操作结果提示
function showMessage(text: string, type: 'success' | 'error' = 'success') {
  message.value = text
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

// 加载 AI 配置
async function loadSettings() {
  loading.value = true
  const res = await aiApi.settings()
  if (res.code === 0 && res.data) {
    aiEnabled.value = res.data.ai_enabled
    providers.value = res.data.providers
    builtinProviders.value = res.data.builtin_providers
  }
  loading.value = false
}

// 切换 AI 功能总开关
async function toggleEnabled() {
  await aiApi.updateSettings({ ai_enabled: aiEnabled.value })
  showMessage(aiEnabled.value ? 'AI 功能已启用' : 'AI 功能已关闭')
}

// 切换活跃供应商
async function switchProvider(name: string) {
  const res = await aiApi.switchProvider(name)
  if (res.code === 0) {
    await loadSettings()
    showMessage(`已切换到 ${name}`)
  } else {
    showMessage(res.message || '切换失败', 'error')
  }
}

// 删除供应商
async function deleteProvider(name: string) {
  if (!confirm(`确认删除供应商 ${name}？`)) return
  const res = await aiApi.deleteProvider(name)
  if (res.code === 0) {
    await loadSettings()
    showMessage(`已删除 ${name}`)
  } else {
    showMessage(res.message || '删除失败', 'error')
  }
}

// 打开新增表单
function openAddForm() {
  isEditing.value = false
  showForm.value = true
  Object.assign(form, { name: '', label: '', base_url: '', api_key: '', chat_model: '', reasoning_model: '' })
}

// 打开编辑表单
function openEditForm(p: ProviderInfo) {
  isEditing.value = true
  showForm.value = true
  Object.assign(form, { name: p.name, label: p.label, base_url: p.base_url, api_key: '', chat_model: p.chat_model, reasoning_model: p.reasoning_model })
}

// 快捷添加内置供应商
function quickAdd(bp: string) {
  isEditing.value = false
  showForm.value = true
  Object.assign(form, { name: bp, label: bp.charAt(0).toUpperCase() + bp.slice(1), base_url: '', api_key: '', chat_model: '', reasoning_model: '' })
}

// 保存供应商
async function saveProvider() {
  saving.value = true
  const payload: Record<string, unknown> = { ...form }
  if (!payload.api_key) delete payload.api_key
  const res = await aiApi.addProvider(payload as Parameters<typeof aiApi.addProvider>[0])
  saving.value = false
  if (res.code === 0) {
    showForm.value = false
    await loadSettings()
    showMessage('保存成功')
  } else {
    showMessage(res.message || '保存失败', 'error')
  }
}

onMounted(loadSettings)
</script>

<template>
  <section>
    <PageHeader title="AI 配置" subtitle="查看和管理 AI 服务设置" />

    <div v-if="loading" class="text-center py-20 text-slate-400">加载中…</div>

    <div v-else class="mx-auto max-w-xl rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
      <div class="space-y-5">
        <div class="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
          <span class="text-sm text-slate-500">AI 服务状态</span>
          <StatusBadge :label="settings.ai_enabled ? '已启用' : '未启用'" :type="settings.ai_enabled ? 'success' : 'danger'" />
        </div>
        <div class="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
          <span class="text-sm text-slate-500">API Key 配置</span>
          <StatusBadge :label="settings.api_key_configured ? '已配置' : '未配置'" :type="settings.api_key_configured ? 'success' : 'warning'" />
        </div>
      </div>

      <form class="mt-6 space-y-5" @submit.prevent="handleSave">
        <div>
          <label class="mb-1 block text-sm font-medium">AI 供应商</label>
          <input v-model="form.provider" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Chat 模型</label>
          <input v-model="form.chat_model" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Reasoning 模型</label>
          <input v-model="form.reasoning_model" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Base URL</label>
          <input v-model="form.base_url" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">API Key（留空则不修改）</label>
          <input v-model="form.api_key" type="password" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="••••••••" />
        </div>
        <div class="flex items-center gap-2">
          <input id="ai_enabled" v-model="form.ai_enabled" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-teal-600" />
          <label for="ai_enabled" class="text-sm font-medium">启用 AI 功能</label>
        </div>
        <div class="flex justify-end">
          <button type="submit" class="rounded-lg bg-teal-600 px-6 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving">
            {{ saving ? '保存中…' : '保存配置' }}
          </button>
        </div>
      </form>
      <p v-if="saved" class="mt-3 text-center text-sm text-green-600">保存成功</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { aiApi } from '@hotelink/api'
import { PageHeader, StatusBadge } from '@hotelink/ui'

const loading = ref(true)
const saving = ref(false)
const saved = ref(false)

const settings = reactive({ ai_enabled: false, api_key_configured: false })
const form = reactive({ provider: '', chat_model: '', reasoning_model: '', base_url: '', api_key: '', ai_enabled: false })

async function loadSettings() {
  loading.value = true
  const res = await aiApi.settings()
  if (res.code === 0 && res.data) {
    const d = res.data as Record<string, unknown>
    settings.ai_enabled = !!d.ai_enabled
    settings.api_key_configured = !!d.api_key_configured
    form.provider = (d.provider as string) || ''
    form.chat_model = (d.chat_model as string) || ''
    form.reasoning_model = (d.reasoning_model as string) || ''
    form.base_url = (d.base_url as string) || ''
    form.ai_enabled = !!d.ai_enabled
  }
  loading.value = false
}

async function handleSave() {
  saving.value = true
  saved.value = false
  const payload: Record<string, unknown> = { ...form }
  if (!payload.api_key) delete payload.api_key
  await aiApi.updateSettings(payload)
  saving.value = false
  saved.value = true
  loadSettings()
  setTimeout(() => { saved.value = false }, 2000)
}

onMounted(loadSettings)
</script>

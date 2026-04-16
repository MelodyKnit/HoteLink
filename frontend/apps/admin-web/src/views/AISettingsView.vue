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
              <button
                v-if="!p.is_active"
                class="rounded-lg bg-teal-100 px-3 py-1 text-xs font-medium text-teal-700 hover:bg-teal-200 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="providerActionLoading"
                @click="switchProvider(p.name)"
              >
                {{ providerActionLoading ? '切换中…' : '切换使用' }}
              </button>
              <button
                class="rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="providerActionLoading"
                @click="openEditForm(p)"
              >
                编辑
              </button>
              <button
                v-if="!p.is_active"
                class="rounded-lg bg-red-100 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-200 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="providerActionLoading"
                @click="deleteProvider(p.name)"
              >
                {{ providerActionLoading ? '处理中…' : '删除' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- AI 连通性测试 -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-1 text-base font-semibold">AI 连通性测试</h3>
        <p class="mb-4 text-sm text-slate-500">管理员可在界面直接测试当前或指定供应商是否可用</p>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <label class="mb-1 block text-sm font-medium">测试供应商</label>
            <select v-model="testForm.provider_name" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500">
              <option value="">当前激活供应商</option>
              <option v-for="p in providers" :key="p.name" :value="p.name">
                {{ p.label || p.name }}
              </option>
            </select>
          </div>
          <div class="md:col-span-2">
            <label class="mb-1 block text-sm font-medium">测试消息</label>
            <input
              v-model="testForm.message"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
              placeholder="例如：请回复 AI测试成功，并简述当前供应商"
            />
          </div>
        </div>

        <div class="mt-4 flex items-center gap-3">
          <button
            class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="testLoading"
            @click="runAiTest"
          >
            {{ testLoading ? '测试中…' : '执行 AI 测试' }}
          </button>
          <span class="text-xs text-slate-500">测试结果会同步写入 AI 调用日志</span>
        </div>

        <div v-if="testResult" class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div class="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-600">
            <span class="rounded bg-slate-200 px-2 py-0.5">provider: {{ testResult.provider || '-' }}</span>
            <span class="rounded bg-slate-200 px-2 py-0.5">model: {{ testResult.model || '-' }}</span>
            <span class="rounded bg-slate-200 px-2 py-0.5">latency: {{ testResult.latency_ms }}ms</span>
          </div>
          <pre class="whitespace-pre-wrap rounded-lg bg-white p-3 text-sm text-slate-700 ring-1 ring-slate-200">{{ testResult.answer || '（无返回内容）' }}</pre>
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

      <teleport to="body">
        <div
          v-if="showForm"
          class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4 py-6 backdrop-blur-[2px]"
          @click.self="closeForm"
        >
          <div class="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200">
            <div class="mb-4 flex items-start justify-between gap-4">
              <div>
                <h3 class="text-base font-semibold">{{ isEditing ? '编辑供应商' : '添加供应商' }}</h3>
                <p class="mt-1 text-sm text-slate-500">表单以弹窗方式打开，避免拉长页面内容</p>
              </div>
              <button type="button" class="rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-700" @click="closeForm">
                关闭
              </button>
            </div>

            <form class="space-y-4" @submit.prevent="saveProvider">
              <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
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
                <div class="relative">
                  <input
                    v-model="form.api_key"
                    :type="showApiKey ? 'text' : 'password'"
                    class="w-full rounded-lg border border-slate-300 px-3 py-2 pr-16 text-sm outline-none focus:border-teal-500"
                    placeholder="sk-..."
                  />
                  <button
                    type="button"
                    class="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                    @click="showApiKey = !showApiKey"
                  >
                    {{ showApiKey ? '隐藏' : '显示' }}
                  </button>
                </div>
              </div>
              <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-1 block text-sm font-medium">Chat 模型</label>
                  <input v-model="form.chat_model" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="deepseek-chat" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium">Reasoning 模型</label>
                  <input v-model="form.reasoning_model" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="deepseek-reasoner" />
                </div>
              </div>
              <div class="flex justify-end gap-2 pt-2">
                <button type="button" class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50" @click="closeForm">取消</button>
                <button type="submit" class="rounded-lg bg-teal-600 px-6 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving">
                  {{ saving ? '保存中…' : '保存' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </teleport>

    </div>

  </section>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { aiApi } from '@hotelink/api'
import { extractApiError } from '@hotelink/utils'
import { PageHeader, StatusBadge, useToast, useConfirm } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

interface ProviderInfo {
  name: string
  label: string
  base_url: string
  api_key_configured: boolean
  api_key?: string
  chat_model: string
  reasoning_model: string
  timeout: number
  is_active: boolean
}

const loading = ref(true)
const saving = ref(false)
const showForm = ref(false)
const isEditing = ref(false)
const showApiKey = ref(false)
const providerActionLoading = ref(false)

const aiEnabled = ref(false)
const providers = ref<ProviderInfo[]>([])
const builtinProviders = ref<string[]>([])
const providerNames = computed(() => new Set(providers.value.map(p => p.name)))
const testLoading = ref(false)
const testResult = ref<{ provider: string; model: string; answer: string; latency_ms: number } | null>(null)

const form = reactive({ name: '', label: '', base_url: '', api_key: '', chat_model: '', reasoning_model: '' })
const testForm = reactive({
  provider_name: '',
  message: '请回复：AI测试成功，并说明你当前使用的模型。',
})

// 加载 AI 配置
async function loadSettings() {
  loading.value = true
  const res = await aiApi.settings()
  if (res.code === 0 && res.data) {
    aiEnabled.value = res.data.ai_enabled
    providers.value = res.data.providers
    builtinProviders.value = res.data.builtin_providers
  } else if (res.code !== 0) {
    showToast(res.message || '加载配置失败', 'error')
  }
  loading.value = false
}

// 切换 AI 功能总开关
async function toggleEnabled() {
  const res = await aiApi.updateSettings({ ai_enabled: aiEnabled.value })
  if (res.code === 0) {
    showToast(aiEnabled.value ? 'AI 功能已启用' : 'AI 功能已关闭', 'success')
  } else {
    showToast(res.message || '操作失败', 'error')
  }
}

// 切换活跃供应商
async function switchProvider(name: string) {
  if (providerActionLoading.value) return
  providerActionLoading.value = true
  try {
    const res = await aiApi.switchProvider(name)
    if (res.code === 0) {
      await loadSettings()
      showToast(`已切换到 ${name}`, 'success')
    } else {
      showToast(res.message || '切换失败', 'error')
    }
  } catch {
    showToast('切换失败，请检查网络后重试', 'error')
  } finally {
    providerActionLoading.value = false
  }
}

// 删除供应商
async function deleteProvider(name: string) {
  if (providerActionLoading.value) return
  if (!await confirmDialog(`确认删除供应商 ${name}？`, { type: 'danger' })) return
  providerActionLoading.value = true
  try {
    const res = await aiApi.deleteProvider(name)
    if (res.code === 0) {
      await loadSettings()
      showToast(`已删除 ${name}`, 'success')
    } else {
      showToast(res.message || '删除失败', 'error')
    }
  } catch {
    showToast('删除失败，请检查网络后重试', 'error')
  } finally {
    providerActionLoading.value = false
  }
}

// 打开新增表单
function openAddForm() {
  isEditing.value = false
  showApiKey.value = false
  showForm.value = true
  Object.assign(form, { name: '', label: '', base_url: '', api_key: '', chat_model: '', reasoning_model: '' })
}

function closeForm() {
  showForm.value = false
  showApiKey.value = false
}

// 打开编辑表单
function openEditForm(p: ProviderInfo) {
  isEditing.value = true
  showApiKey.value = false
  showForm.value = true
  Object.assign(form, {
    name: p.name,
    label: p.label,
    base_url: p.base_url,
    api_key: p.api_key || '',
    chat_model: p.chat_model,
    reasoning_model: p.reasoning_model,
  })
}

// 快捷添加内置供应商
function quickAdd(bp: string) {
  isEditing.value = false
  showApiKey.value = false
  showForm.value = true
  Object.assign(form, { name: bp, label: bp.charAt(0).toUpperCase() + bp.slice(1), base_url: '', api_key: '', chat_model: '', reasoning_model: '' })
}

// 保存供应商
async function saveProvider() {
  const name = form.name.trim()
  const label = form.label.trim()
  const baseUrl = form.base_url.trim()
  const chatModel = form.chat_model.trim()

  if (!name) {
    showToast('请填写标识名称', 'warning')
    return
  }
  if (!label) {
    showToast('请填写显示名称', 'warning')
    return
  }
  if (!baseUrl) {
    showToast('请填写 Base URL', 'warning')
    return
  }
  if (!chatModel) {
    showToast('请填写 Chat 模型', 'warning')
    return
  }

  form.name = name
  form.label = label
  form.base_url = baseUrl
  form.chat_model = chatModel
  form.reasoning_model = form.reasoning_model.trim()

  saving.value = true
  const payload: Record<string, unknown> = { ...form }
  if (!payload.api_key) delete payload.api_key
  const res = await aiApi.addProvider(payload as Parameters<typeof aiApi.addProvider>[0])
  saving.value = false
  if (res.code === 0) {
    closeForm()
    await loadSettings()
    showToast('保存成功', 'success')
  } else {
    showToast(extractApiError(res, '保存失败，请检查填写内容', {
      name: '标识名称',
      label: '显示名称',
      base_url: 'Base URL',
      api_key: 'API Key',
      chat_model: 'Chat 模型',
      reasoning_model: 'Reasoning 模型',
    }), 'error')
  }
}

// 执行管理端 AI 测试
async function runAiTest() {
  const message = testForm.message.trim()
  if (!message) {
    showToast('请输入测试消息', 'warning')
    return
  }
  testLoading.value = true
  const res = await aiApi.test({
    message,
    provider_name: testForm.provider_name || undefined,
  })
  testLoading.value = false

  if (res.code === 0 && res.data) {
    testResult.value = {
      provider: String(res.data.provider || ''),
      model: String(res.data.model || ''),
      answer: String(res.data.answer || ''),
      latency_ms: Number(res.data.latency_ms || 0),
    }
    showToast('AI 测试成功', 'success')
    return
  }

  testResult.value = null
  showToast(extractApiError(res, 'AI 测试失败，请检查当前供应商配置'), 'error')
}

onMounted(loadSettings)
</script>

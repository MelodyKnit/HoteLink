<template>
  <section>
    <PageHeader title="系统设置" subtitle="平台基础配置" />

    <div v-if="loading" class="text-center py-20 text-slate-400">加载中…</div>

    <div v-else class="mx-auto max-w-xl rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
      <form class="space-y-5" @submit.prevent="handleSave">
        <div>
          <label class="mb-1 block text-sm font-medium">平台名称</label>
          <input v-model="form.platform_name" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">客服电话</label>
          <input v-model="form.support_phone" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">订单自动取消时间（分钟）</label>
          <input v-model.number="form.order_auto_cancel_minutes" type="number" min="1" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div class="flex justify-end">
          <button type="submit" class="rounded-lg bg-teal-600 px-6 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving">
            {{ saving ? '保存中…' : '保存设置' }}
          </button>
        </div>
      </form>
      <p v-if="saved" class="mt-3 text-center text-sm text-green-600">保存成功</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { settingsApi } from '@hotelink/api'
import { PageHeader } from '@hotelink/ui'

const loading = ref(true)
const saving = ref(false)
const saved = ref(false)
const form = reactive({ platform_name: '', support_phone: '', order_auto_cancel_minutes: 30 })

async function loadSettings() {
  loading.value = true
  const res = await settingsApi.get()
  if (res.code === 0 && res.data) {
    const d = res.data as Record<string, unknown>
    form.platform_name = (d.platform_name as string) || ''
    form.support_phone = (d.support_phone as string) || ''
    form.order_auto_cancel_minutes = (d.order_auto_cancel_minutes as number) || 30
  }
  loading.value = false
}

async function handleSave() {
  saving.value = true
  saved.value = false
  await settingsApi.update(form)
  saving.value = false
  saved.value = true
  setTimeout(() => { saved.value = false }, 2000)
}

onMounted(loadSettings)
</script>

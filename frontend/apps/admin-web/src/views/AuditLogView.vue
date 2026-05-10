<template>
  <section>
    <PageHeader title="审计日志" subtitle="追踪发票、库存等关键后台操作" />

    <div class="mb-4 grid gap-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200 lg:grid-cols-[1.4fr_1fr_1fr_1fr_1fr_auto]">
      <input v-model="filters.keyword" placeholder="操作人 / 动作 / 目标" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="reload" />
      <input v-model="filters.action" placeholder="动作，如 invoice" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="reload" />
      <input v-model="filters.target" placeholder="目标，如 room_inventory" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="reload" />
      <input v-model="filters.start_date" type="date" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" />
      <input v-model="filters.end_date" type="date" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" />
      <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="reload">查询</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="logs" :loading="loading">
        <template #col-action_label="{ row, value }">
          <div class="space-y-1">
            <div class="font-medium text-slate-800">{{ value || row.action }}</div>
            <div class="font-mono text-[11px] text-slate-400">{{ row.action }}</div>
          </div>
        </template>
        <template #col-risk_level="{ value }">
          <StatusBadge :label="riskMeta(String(value)).label" :type="riskMeta(String(value)).type" />
        </template>
        <template #col-created_at="{ value }">{{ formatDateTime(String(value)) }}</template>
        <template #actions="{ row }">
          <button class="text-sm text-teal-600 hover:underline" @click="openDetail(row)">查看详情</button>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadLogs() }" />
    </div>

    <ModalDialog :visible="showDetail" title="审计日志详情" size="lg" @close="showDetail = false">
      <div v-if="selectedLog" class="space-y-4">
        <div class="grid gap-3 text-sm sm:grid-cols-2">
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-400">操作动作</p>
            <p class="mt-1 font-medium text-slate-800">{{ selectedLog.action_label || selectedLog.action }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-400">操作人</p>
            <p class="mt-1 font-medium text-slate-800">{{ selectedLog.username }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-400">目标</p>
            <p class="mt-1 break-all font-mono text-xs text-slate-700">{{ selectedLog.target || '-' }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-400">时间</p>
            <p class="mt-1 font-medium text-slate-800">{{ formatDateTime(selectedLog.created_at) }}</p>
          </div>
        </div>
        <div>
          <div class="mb-2 flex items-center justify-between">
            <p class="text-sm font-medium text-slate-700">操作详情</p>
            <button class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500 hover:bg-slate-200" @click="copyDetail">复制 JSON</button>
          </div>
          <pre class="max-h-[420px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-5 text-slate-100">{{ formattedDetail }}</pre>
        </div>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { adminSystemApi } from '@hotelink/api'
import type { AuditLogItem } from '@hotelink/api'
import { extractApiError, formatDateTime } from '@hotelink/utils'
import { DataTable, ModalDialog, PageHeader, Pagination, StatusBadge, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const columns = [
  { key: 'action_label', label: '操作' },
  { key: 'username', label: '操作人' },
  { key: 'target', label: '目标' },
  { key: 'risk_level', label: '风险' },
  { key: 'created_at', label: '时间' },
]

const filters = reactive({
  keyword: '',
  action: '',
  target: '',
  start_date: '',
  end_date: '',
})
const logs = ref<AuditLogItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showDetail = ref(false)
const selectedLog = ref<AuditLogItem | null>(null)

const formattedDetail = computed(() => JSON.stringify(selectedLog.value?.detail || {}, null, 2))

function riskMeta(value: string): { label: string; type: 'success' | 'warning' | 'danger' | 'default' } {
  if (value === 'high') return { label: '高风险', type: 'danger' }
  if (value === 'medium') return { label: '需关注', type: 'warning' }
  return { label: '普通', type: 'default' }
}

function buildParams(): Record<string, unknown> {
  const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params[key] = value
  })
  return params
}

async function loadLogs() {
  loading.value = true
  try {
    const res = await adminSystemApi.auditLogs(buildParams())
    if (res.code === 0 && res.data) {
      logs.value = res.data.items || []
      total.value = res.data.total || 0
    } else {
      showToast(extractApiError(res, '审计日志加载失败'), 'error')
    }
  } catch {
    showToast('审计日志加载失败，请检查网络后重试', 'error')
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadLogs()
}

function openDetail(row: Record<string, unknown>) {
  // DataTable exposes rows through a generic record slot; the source list is already AuditLogItem[].
  selectedLog.value = row as unknown as AuditLogItem
  showDetail.value = true
}

async function copyDetail() {
  try {
    await navigator.clipboard.writeText(formattedDetail.value)
    showToast('审计详情已复制', 'success')
  } catch {
    showToast('复制失败，请手动选择内容', 'warning')
  }
}

onMounted(loadLogs)
</script>

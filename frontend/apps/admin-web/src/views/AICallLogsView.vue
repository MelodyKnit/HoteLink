<template>
  <section>
    <PageHeader title="AI 调用日志" subtitle="查看 AI 功能调用记录与用量统计" />

    <!-- 用量概览卡片 -->
    <div v-if="stats" class="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      <div class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs text-slate-500 mb-1">总调用次数</p>
        <p class="text-2xl font-bold text-slate-800">{{ stats.total_calls.toLocaleString() }}</p>
      </div>
      <div class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs text-slate-500 mb-1">成功次数</p>
        <p class="text-2xl font-bold text-green-600">{{ stats.success_calls.toLocaleString() }}</p>
      </div>
      <div class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs text-slate-500 mb-1">失败次数</p>
        <p class="text-2xl font-bold text-red-500">{{ stats.failed_calls.toLocaleString() }}</p>
      </div>
      <div class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs text-slate-500 mb-1">总 Token 消耗</p>
        <p class="text-2xl font-bold text-indigo-600">{{ formatNumber(stats.total_tokens) }}</p>
      </div>
      <div class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <p class="text-xs text-slate-500 mb-1">预估费用</p>
        <p class="text-2xl font-bold text-amber-600">¥{{ stats.total_cost.toFixed(4) }}</p>
      </div>
    </div>

    <!-- 场景分布 -->
    <div v-if="stats" class="mb-6 grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-3 text-sm font-semibold text-slate-700">按场景分布</h3>
        <div class="space-y-2">
          <div v-for="(count, scene) in stats.by_scene" :key="scene" class="flex items-center gap-3">
            <span class="w-36 shrink-0 text-xs text-slate-600 truncate">{{ SCENE_LABELS[scene] || scene }}</span>
            <div class="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                class="h-full rounded-full bg-teal-500 transition-all"
                :style="{ width: `${Math.round((count / stats.total_calls) * 100)}%` }"
              />
            </div>
            <span class="w-10 text-right text-xs font-medium text-slate-700">{{ count }}</span>
          </div>
        </div>
      </div>
      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-3 text-sm font-semibold text-slate-700">按服务商分布</h3>
        <div class="space-y-2">
          <div v-for="(count, provider) in stats.by_provider" :key="provider" class="flex items-center gap-3">
            <span class="w-28 shrink-0 text-xs text-slate-600 font-mono">{{ provider }}</span>
            <div class="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                class="h-full rounded-full bg-indigo-500 transition-all"
                :style="{ width: `${Math.round((count / stats.total_calls) * 100)}%` }"
              />
            </div>
            <span class="w-10 text-right text-xs font-medium text-slate-700">{{ count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="mb-4 flex flex-wrap items-center gap-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <div class="flex items-center gap-2">
        <label class="text-xs text-slate-500">场景</label>
        <SelectField v-model="filters.scene" class="w-36">
          <option value="">全部场景</option>
          <option v-for="(label, val) in SCENE_LABELS" :key="val" :value="val">{{ label }}</option>
        </SelectField>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-xs text-slate-500">状态</label>
        <SelectField v-model="filters.status" class="w-28">
          <option value="">全部状态</option>
          <option value="success">成功</option>
          <option value="failed">失败</option>
          <option value="timeout">超时</option>
          <option value="quota_exceeded">配额超限</option>
        </SelectField>
      </div>
      <button
        class="ml-auto rounded-lg bg-teal-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-teal-700"
        @click="loadLogs(1)"
      >
        筛选
      </button>
    </div>

    <!-- 日志表格 -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 overflow-hidden">
      <div v-if="loading" class="flex h-40 items-center justify-center text-sm text-slate-400">加载中…</div>
      <div v-else-if="!logs.length" class="flex h-40 items-center justify-center text-sm text-slate-400">暂无日志记录</div>
      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th class="px-4 py-3 text-left font-medium">时间</th>
            <th class="px-4 py-3 text-left font-medium">场景</th>
            <th class="px-4 py-3 text-left font-medium">服务商</th>
            <th class="px-4 py-3 text-left font-medium">模型</th>
            <th class="px-4 py-3 text-right font-medium">Tokens</th>
            <th class="px-4 py-3 text-right font-medium">延迟 ms</th>
            <th class="px-4 py-3 text-center font-medium">状态</th>
            <th class="px-4 py-3 text-left font-medium">错误信息</th>
            <th class="px-4 py-3 text-center font-medium">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="log in logs"
            :key="log.id"
            class="cursor-pointer hover:bg-slate-50"
            @click="openLogDetail(log)"
          >
            <td class="px-4 py-2.5 text-xs text-slate-500 font-mono whitespace-nowrap">{{ formatDateTime(log.created_at) }}</td>
            <td class="px-4 py-2.5 text-xs text-slate-700">{{ SCENE_LABELS[log.scene] || log.scene }}</td>
            <td class="px-4 py-2.5 text-xs font-mono text-slate-600">{{ log.provider }}</td>
            <td class="px-4 py-2.5 text-xs font-mono text-slate-500 max-w-[120px] truncate">{{ log.model }}</td>
            <td class="px-4 py-2.5 text-right text-xs text-slate-700">{{ (log.total_tokens || 0).toLocaleString() }}</td>
            <td class="px-4 py-2.5 text-right text-xs text-slate-600">{{ log.latency_ms }}</td>
            <td class="px-4 py-2.5 text-center">
              <span
                class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                :class="statusClass(log.status)"
              >
                {{ STATUS_LABELS[log.status] || log.status }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-xs text-red-500 max-w-[200px] truncate" :title="log.error_message">{{ log.error_message || '—' }}</td>
            <td class="px-4 py-2.5 text-center">
              <button
                class="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50"
                @click.stop="openLogDetail(log)"
              >
                查看详情
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="border-t border-slate-100 px-4 py-3">
        <Pagination :page="page" :page-size="pageSize" :total="total" @change="loadLogs" />
      </div>
    </div>

    <ModalDialog
      :visible="detailVisible"
      title="AI 调用日志详情"
      size="lg"
      @close="closeLogDetail"
    >
      <div v-if="selectedLog" class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <p class="text-[11px] text-slate-500">时间</p>
            <p class="mt-1 text-xs font-mono text-slate-700">{{ formatDateTime(selectedLog.created_at) }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <p class="text-[11px] text-slate-500">调用用户</p>
            <p class="mt-1 text-xs text-slate-700">{{ selectedLog.username || '系统/匿名' }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <p class="text-[11px] text-slate-500">场景</p>
            <p class="mt-1 text-xs text-slate-700">{{ SCENE_LABELS[selectedLog.scene] || selectedLog.scene }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <p class="text-[11px] text-slate-500">状态</p>
            <p class="mt-1 text-xs">
              <span class="rounded-full px-2 py-0.5 text-[10px] font-semibold" :class="statusClass(selectedLog.status)">
                {{ STATUS_LABELS[selectedLog.status] || selectedLog.status }}
              </span>
            </p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2 sm:col-span-2">
            <p class="text-[11px] text-slate-500">服务商 / 模型</p>
            <p class="mt-1 text-xs font-mono text-slate-700 break-all">{{ selectedLog.provider }} / {{ selectedLog.model }}</p>
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-4">
          <div class="rounded-xl border border-slate-200 px-3 py-2">
            <p class="text-[11px] text-slate-500">输入 Tokens</p>
            <p class="mt-1 text-sm font-semibold text-slate-700">{{ (selectedLog.input_tokens || 0).toLocaleString() }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 px-3 py-2">
            <p class="text-[11px] text-slate-500">输出 Tokens</p>
            <p class="mt-1 text-sm font-semibold text-slate-700">{{ (selectedLog.output_tokens || 0).toLocaleString() }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 px-3 py-2">
            <p class="text-[11px] text-slate-500">总 Tokens</p>
            <p class="mt-1 text-sm font-semibold text-slate-700">{{ (selectedLog.total_tokens || 0).toLocaleString() }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 px-3 py-2">
            <p class="text-[11px] text-slate-500">延迟</p>
            <p class="mt-1 text-sm font-semibold text-slate-700">{{ selectedLog.latency_ms }} ms</p>
          </div>
        </div>

        <div class="rounded-xl border border-red-200 bg-red-50 p-3">
          <div class="mb-2 flex items-center justify-between gap-2">
            <p class="text-xs font-semibold text-red-700">错误信息</p>
            <button
              class="rounded-md border border-red-200 px-2 py-1 text-[11px] text-red-600 hover:bg-red-100"
              @click="copyErrorMessage"
            >
              复制
            </button>
          </div>
          <pre class="max-h-64 overflow-y-auto whitespace-pre-wrap break-all rounded-lg bg-white p-3 text-xs leading-5 text-red-700">{{ selectedLog.error_message || '无错误信息' }}</pre>
        </div>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { aiApi } from '@hotelink/api'
import { PageHeader, SelectField, Pagination, ModalDialog, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const SCENE_LABELS: Record<string, string> = {
  report_summary: '营收报告',
  review_summary: '评价总结',
  reply_suggestion: '回复建议',
  pricing_suggestion: '智能定价',
  business_report: '深度报告',
  marketing_copy: '营销文案',
  content_generate: '内容生成',
  review_sentiment: '情感分析',
  anomaly_report: '运营异常',
  anomaly_order: '订单异常',
  recommendations: '智能推荐',
  hotel_compare: '酒店对比',
  customer_service: '客服对话',
}
const STATUS_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  timeout: '超时',
  quota_exceeded: '配额超限',
}

interface LogItem {
  id: number
  username: string
  scene: string
  provider: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost_estimate: number
  latency_ms: number
  status: string
  error_message: string
  created_at: string
}

interface StatsData {
  total_calls: number
  success_calls: number
  failed_calls: number
  total_tokens: number
  total_cost: number
  by_scene: Record<string, number>
  by_provider: Record<string, number>
}

const loading = ref(false)
const logs = ref<LogItem[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const stats = ref<StatsData | null>(null)
const detailVisible = ref(false)
const selectedLog = ref<LogItem | null>(null)

const filters = reactive({ scene: '', status: '' })

function statusClass(status: string): string {
  if (status === 'success') return 'bg-green-100 text-green-700'
  if (status === 'failed') return 'bg-red-100 text-red-700'
  if (status === 'timeout') return 'bg-amber-100 text-amber-700'
  if (status === 'quota_exceeded') return 'bg-orange-100 text-orange-700'
  return 'bg-slate-100 text-slate-700'
}

function formatNumber(n: number): string {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function formatDateTime(dt: string): string {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function openLogDetail(log: LogItem) {
  selectedLog.value = log
  detailVisible.value = true
}

function closeLogDetail() {
  detailVisible.value = false
  selectedLog.value = null
}

async function copyErrorMessage() {
  const message = selectedLog.value?.error_message || ''
  if (!message) {
    showToast('当前日志没有错误信息', 'warning')
    return
  }
  try {
    await navigator.clipboard.writeText(message)
    showToast('错误信息已复制', 'success')
  } catch {
    showToast('复制失败，请手动复制', 'error')
  }
}

async function loadLogs(p = 1) {
  loading.value = true
  page.value = p
  const params: Record<string, unknown> = { page: p, page_size: pageSize }
  if (filters.scene) params.scene = filters.scene
  if (filters.status) params.status = filters.status
  try {
    const res = await aiApi.callLogs(params as Parameters<typeof aiApi.callLogs>[0])
    if (res.code === 0 && res.data) {
      const data = res.data as { items: LogItem[]; total: number }
      logs.value = data.items || []
      total.value = data.total || 0
    } else {
      showToast(res.message || '日志加载失败，请稍后重试', 'error')
    }
  } catch {
    showToast('日志加载失败，请检查网络后重试', 'error')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await aiApi.usageStats()
    if (res.code === 0 && res.data) {
      stats.value = res.data as StatsData
    } else {
      showToast(res.message || '统计数据加载失败', 'error')
    }
  } catch {
    showToast('统计数据加载失败，请检查网络后重试', 'error')
  }
}

onMounted(() => {
  loadStats()
  loadLogs()
})
</script>

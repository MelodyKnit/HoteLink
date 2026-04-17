<template>
  <section>
    <PageHeader title="系统状态" subtitle="平台运行状态与资源占用" />

    <div v-if="statusLoading && !status" class="text-center py-20 text-slate-400">加载中…</div>
    <div v-else-if="status" class="space-y-6">
      <div class="flex items-center justify-between text-xs text-slate-400">
        <span>数据更新时间：{{ status.generated_at ? formatTime(status.generated_at) : '—' }}</span>
        <span :class="status.cached ? 'rounded-full bg-amber-100 px-2 py-0.5 text-amber-700' : 'rounded-full bg-emerald-100 px-2 py-0.5 text-emerald-700'">
          {{ status.cached ? '缓存数据' : '实时数据' }}
        </span>
      </div>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 p-5 text-white shadow">
          <p class="text-xs font-medium text-blue-100">系统运行</p>
          <p class="mt-1 text-xl font-bold">{{ formatUptime(status.system?.uptime_seconds) }}</p>
          <p class="mt-1 text-[11px] text-blue-200">{{ status.system?.os }}</p>
        </div>
        <div class="rounded-2xl bg-gradient-to-br from-teal-500 to-teal-600 p-5 text-white shadow">
          <p class="text-xs font-medium text-teal-100">数据库</p>
          <p class="mt-1 text-xl font-bold">{{ status.database?.engine }}</p>
          <p class="mt-1 text-[11px] text-teal-200">{{ status.database?.size_mb != null ? status.database.size_mb + ' MB' : status.database?.host }}</p>
        </div>
        <div class="rounded-2xl bg-gradient-to-br from-violet-500 to-violet-600 p-5 text-white shadow">
          <p class="text-xs font-medium text-violet-100">Redis</p>
          <p class="mt-1 text-xl font-bold">{{ status.services?.redis?.status === 'connected' ? '已连接' : '未连接' }}</p>
          <p class="mt-1 text-[11px] text-violet-200">{{ status.services?.redis?.version ? 'v' + status.services.redis.version : '—' }}</p>
        </div>
        <div class="rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600 p-5 text-white shadow">
          <p class="text-xs font-medium text-amber-100">Celery</p>
          <p class="mt-1 text-xl font-bold">{{ status.services?.celery?.status === 'connected' ? '运行中' : '已停止' }}</p>
          <p class="mt-1 text-[11px] text-amber-200">{{ status.services?.celery?.workers ? status.services.celery.workers + ' 个 Worker' : '—' }}</p>
        </div>
      </div>

      <div class="grid gap-5 sm:grid-cols-3">
        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <div class="mb-4 flex items-center justify-between">
            <span class="text-sm font-semibold text-slate-700">磁盘</span>
            <span class="rounded-full px-2 py-0.5 text-xs" :class="badgeClass(status.disk?.usage_percent)">{{ status.disk?.usage_percent }}%</span>
          </div>
          <div class="mb-4 flex justify-center">
            <svg viewBox="0 0 120 120" class="h-28 w-28">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#f1f5f9" stroke-width="10" />
              <circle cx="60" cy="60" r="50" fill="none" :stroke="ringStroke(status.disk?.usage_percent)" stroke-width="10" stroke-linecap="round" :stroke-dasharray="ringDash(status.disk?.usage_percent)" stroke-dashoffset="0" transform="rotate(-90 60 60)" class="transition-all duration-700" />
              <text x="60" y="56" text-anchor="middle" class="fill-slate-700 text-lg font-bold" style="font-size:20px">{{ status.disk?.usage_percent }}%</text>
              <text x="60" y="72" text-anchor="middle" class="fill-slate-400" style="font-size:10px">已使用</text>
            </svg>
          </div>
          <div class="grid grid-cols-3 gap-1 text-center text-[11px] text-slate-400">
            <div><span class="block text-xs font-semibold text-slate-600">{{ status.disk?.total_gb }}</span>总量 GB</div>
            <div><span class="block text-xs font-semibold text-slate-600">{{ status.disk?.used_gb }}</span>已用 GB</div>
            <div><span class="block text-xs font-semibold text-slate-600">{{ status.disk?.free_gb }}</span>可用 GB</div>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <div class="mb-4 flex items-center justify-between">
            <span class="text-sm font-semibold text-slate-700">内存</span>
            <span v-if="status.memory" class="rounded-full px-2 py-0.5 text-xs" :class="badgeClass(status.memory.usage_percent)">{{ status.memory.usage_percent }}%</span>
          </div>
          <template v-if="status.memory">
            <div class="mb-4 flex justify-center">
              <svg viewBox="0 0 120 120" class="h-28 w-28">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#f1f5f9" stroke-width="10" />
                <circle cx="60" cy="60" r="50" fill="none" :stroke="ringStroke(status.memory.usage_percent)" stroke-width="10" stroke-linecap="round" :stroke-dasharray="ringDash(status.memory.usage_percent)" stroke-dashoffset="0" transform="rotate(-90 60 60)" class="transition-all duration-700" />
                <text x="60" y="56" text-anchor="middle" class="fill-slate-700 text-lg font-bold" style="font-size:20px">{{ status.memory.usage_percent }}%</text>
                <text x="60" y="72" text-anchor="middle" class="fill-slate-400" style="font-size:10px">已使用</text>
              </svg>
            </div>
            <div class="grid grid-cols-3 gap-1 text-center text-[11px] text-slate-400">
              <div><span class="block text-xs font-semibold text-slate-600">{{ fmtMem(status.memory.total_mb) }}</span>总量</div>
              <div><span class="block text-xs font-semibold text-slate-600">{{ fmtMem(status.memory.used_mb) }}</span>已用</div>
              <div><span class="block text-xs font-semibold text-slate-600">{{ fmtMem(status.memory.available_mb) }}</span>可用</div>
            </div>
          </template>
          <div v-else class="flex h-28 items-center justify-center text-sm text-slate-400">不可用</div>
        </div>

        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <div class="mb-4 flex items-center justify-between">
            <span class="text-sm font-semibold text-slate-700">CPU 负载</span>
            <span v-if="status.cpu_load" class="text-xs text-slate-400">{{ status.cpu_load.cores }} 核</span>
          </div>
          <template v-if="status.cpu_load">
            <div class="mb-4 flex justify-center">
              <svg viewBox="0 0 120 120" class="h-28 w-28">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#f1f5f9" stroke-width="10" />
                <circle cx="60" cy="60" r="50" fill="none" :stroke="ringStroke(cpuPercent)" stroke-width="10" stroke-linecap="round" :stroke-dasharray="ringDash(cpuPercent)" stroke-dashoffset="0" transform="rotate(-90 60 60)" class="transition-all duration-700" />
                <text x="60" y="56" text-anchor="middle" class="fill-slate-700 text-lg font-bold" style="font-size:20px">{{ status.cpu_load['1min'] }}</text>
                <text x="60" y="72" text-anchor="middle" class="fill-slate-400" style="font-size:10px">1 min avg</text>
              </svg>
            </div>
            <div class="grid grid-cols-3 gap-1 text-center text-[11px] text-slate-400">
              <div><span class="block text-xs font-semibold text-slate-600">{{ status.cpu_load['1min'] }}</span>1 min</div>
              <div><span class="block text-xs font-semibold text-slate-600">{{ status.cpu_load['5min'] }}</span>5 min</div>
              <div><span class="block text-xs font-semibold text-slate-600">{{ status.cpu_load['15min'] }}</span>15 min</div>
            </div>
          </template>
          <div v-else class="flex h-28 items-center justify-center text-sm text-slate-400">不可用</div>
        </div>
      </div>

      <div class="grid gap-5 sm:grid-cols-2">
        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-3 text-sm font-semibold text-slate-700">运行环境</h3>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-slate-100">
              <tr><td class="w-24 py-2 text-slate-400">操作系统</td><td class="py-2 font-medium text-slate-700">{{ status.system?.os }}</td></tr>
              <tr><td class="py-2 text-slate-400">架构</td><td class="py-2 font-medium text-slate-700">{{ status.system?.machine }}</td></tr>
              <tr><td class="py-2 text-slate-400">Python</td><td class="py-2 font-medium text-slate-700">{{ status.system?.python }}</td></tr>
              <tr><td class="py-2 text-slate-400">Django</td><td class="py-2 font-medium text-slate-700">{{ status.system?.django }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h3 class="mb-3 text-sm font-semibold text-slate-700">数据库</h3>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-slate-100">
              <tr><td class="w-24 py-2 text-slate-400">引擎</td><td class="py-2 font-medium text-slate-700">{{ status.database?.engine }}</td></tr>
              <tr><td class="py-2 text-slate-400">数据库名</td><td class="py-2 font-medium text-slate-700">{{ status.database?.name }}</td></tr>
              <tr><td class="py-2 text-slate-400">主机</td><td class="py-2 font-medium text-slate-700">{{ status.database?.host }}{{ status.database?.port ? ':' + status.database.port : '' }}</td></tr>
              <tr v-if="status.database?.size_mb != null"><td class="py-2 text-slate-400">大小</td><td class="py-2 font-medium text-slate-700">{{ status.database.size_mb }} MB</td></tr>
              <tr v-if="status.database?.table_count"><td class="py-2 text-slate-400">表数量</td><td class="py-2 font-medium text-slate-700">{{ status.database.table_count }}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-slate-700">业务数据</h3>
          <span class="text-[11px] text-slate-400">查询耗时 {{ status.query_ms ?? '—' }} ms</span>
        </div>
        <div class="grid grid-cols-3 gap-3 sm:grid-cols-7">
          <div v-for="item in bizItems" :key="item.key" class="rounded-xl bg-slate-50/80 py-3 text-center">
            <span class="block text-xl font-bold text-slate-700">{{ status.business?.[item.key] ?? 0 }}</span>
            <span class="text-[11px] text-slate-400">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <div class="flex justify-end">
        <button class="flex items-center gap-1.5 rounded-lg bg-slate-100 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-200 disabled:opacity-60" :disabled="statusLoading" @click="loadStatus(true)">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          {{ statusLoading ? '刷新中…' : '刷新' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminSystemApi } from '@hotelink/api'
import { PageHeader, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const statusLoading = ref(false)
const status = ref<Record<string, any> | null>(null)

async function loadStatus(force = false) {
  statusLoading.value = true
  try {
    const res = await adminSystemApi.status(force ? { refresh: 1 } : undefined)
    if (res.code === 0 && res.data) {
      status.value = res.data as Record<string, any>
    } else {
      showToast('加载系统状态失败', 'error')
    }
  } catch {
    showToast('加载系统状态失败', 'error')
  } finally {
    statusLoading.value = false
  }
}

function ringDash(percent: number | undefined) {
  const circ = 2 * Math.PI * 50
  const p = percent ?? 0
  return `${(p / 100) * circ} ${circ}`
}

function ringStroke(percent: number | undefined) {
  const p = percent ?? 0
  if (p >= 90) return '#ef4444'
  if (p >= 70) return '#f59e0b'
  return '#14b8a6'
}

function badgeClass(percent: number | undefined) {
  const p = percent ?? 0
  if (p >= 90) return 'bg-red-100 text-red-700'
  if (p >= 70) return 'bg-amber-100 text-amber-700'
  return 'bg-teal-100 text-teal-700'
}

function fmtMem(mb: number | undefined) {
  if (!mb) return '—'
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb} MB`
}

function formatUptime(seconds: number | undefined | null) {
  if (!seconds) return '—'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}天 ${h}时`
  if (h > 0) return `${h}时 ${m}分`
  return `${m}分`
}

function formatTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const cpuPercent = computed(() => {
  if (!status.value?.cpu_load) return 0
  const cores = status.value.cpu_load.cores || 1
  return Math.min(100, Math.round((status.value.cpu_load['1min'] / cores) * 100))
})

const bizItems = [
  { key: 'users', label: '用户' },
  { key: 'orders', label: '订单' },
  { key: 'hotels', label: '酒店' },
  { key: 'room_types', label: '房型' },
  { key: 'reviews', label: '评价' },
  { key: 'notices', label: '通知' },
  { key: 'ai_calls', label: 'AI调用' },
]

onMounted(() => {
  void loadStatus()
})
</script>
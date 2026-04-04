<template>
  <section>
    <PageHeader title="财务与报表" subtitle="营收分析与报表任务管理" />

    <!-- Charts Section -->
    <div class="mb-6 grid gap-6 lg:grid-cols-2">
      <!-- Revenue Chart -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-slate-500">营收趋势</h3>
          <div class="flex gap-2">
            <input v-model="chartStart" type="date" class="rounded-lg border border-slate-200 px-2 py-1 text-xs" @change="loadCharts" />
            <input v-model="chartEnd" type="date" class="rounded-lg border border-slate-200 px-2 py-1 text-xs" @change="loadCharts" />
          </div>
        </div>
        <div ref="revenueRef" class="h-72" />
      </div>

      <!-- Order Chart -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-sm font-semibold text-slate-500">订单数趋势</h3>
        <div ref="orderRef" class="h-72" />
      </div>
    </div>

    <!-- Report Tasks -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h3 class="text-sm font-semibold text-slate-700">报表任务</h3>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreate">新建报表</button>
      </div>
      <DataTable :columns="taskColumns" :rows="tasks" :loading="tasksLoading">
        <template #col-status="{ value }">
          <StatusBadge :label="value === 'success' ? '已完成' : value === 'running' ? '运行中' : value === 'failed' ? '失败' : String(value)" :type="value === 'success' ? 'success' : value === 'failed' ? 'danger' : 'info'" />
        </template>
        <template #col-result_summary="{ value }">
          <span class="line-clamp-2 text-xs text-slate-500">{{ value || '-' }}</span>
        </template>
      </DataTable>
      <Pagination :page="taskPage" :page-size="taskPageSize" :total="taskTotal" class="px-4 pb-4" @change="p => { taskPage = p; loadTasks() }" />
    </div>

    <!-- Create Task Modal -->
    <ModalDialog :visible="showCreate" title="新建报表任务" size="md" @close="showCreate = false">
      <form class="space-y-4" @submit.prevent="handleCreate">
        <div>
          <label class="mb-1 block text-sm font-medium">报表类型</label>
          <select v-model="form.report_type" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="revenue">营收报表</option>
            <option value="occupancy">入住率报表</option>
            <option value="review">评价报表</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">酒店（可选）</label>
          <select v-model="form.hotel_id" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="">全部酒店</option>
            <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-sm font-medium">开始日期</label>
            <input v-model="form.start_date" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">结束日期</label>
            <input v-model="form.end_date" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCreate = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="handleCreate">创建</button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi, reportApi, hotelApi } from '@hotelink/api'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination } from '@hotelink/ui'

const revenueRef = ref<HTMLElement>()
const orderRef = ref<HTMLElement>()
let revenueChart: echarts.ECharts | null = null
let orderChart: echarts.ECharts | null = null

const today = new Date()
const thirtyDaysAgo = new Date(today.getTime() - 30 * 86400000)
const chartStart = ref(thirtyDaysAgo.toISOString().slice(0, 10))
const chartEnd = ref(today.toISOString().slice(0, 10))

const taskColumns = [
  { key: 'id', label: 'ID' },
  { key: 'report_type', label: '类型' },
  { key: 'hotel_name', label: '酒店' },
  { key: 'start_date', label: '开始日期' },
  { key: 'end_date', label: '结束日期' },
  { key: 'status', label: '状态' },
  { key: 'result_summary', label: '结果摘要' },
  { key: 'created_at', label: '创建时间' },
]

const tasks = ref<Record<string, unknown>[]>([])
const tasksLoading = ref(false)
const taskPage = ref(1)
const taskPageSize = ref(10)
const taskTotal = ref(0)

const hotels = ref<Record<string, unknown>[]>([])
const showCreate = ref(false)
const form = reactive({ report_type: 'revenue', hotel_id: '' as string | number, start_date: '', end_date: '' })

async function loadCharts() {
  const res = await dashboardApi.charts({ start_date: chartStart.value, end_date: chartEnd.value })
  if (res.code !== 0 || !res.data) return
  const items = (res.data as Record<string, unknown>).items as { date: string; order_count: number; revenue: number }[]
  const dates = items.map(i => i.date)
  const revenues = items.map(i => i.revenue)
  const counts = items.map(i => i.order_count)

  await nextTick()
  if (revenueRef.value) {
    revenueChart = revenueChart || echarts.init(revenueRef.value)
    revenueChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [{ name: '营收', type: 'line', data: revenues, smooth: true, itemStyle: { color: '#0f766e' }, areaStyle: { color: 'rgba(15,118,110,0.1)' } }],
      grid: { left: 50, right: 20, bottom: 30, top: 20 },
    })
  }
  if (orderRef.value) {
    orderChart = orderChart || echarts.init(orderRef.value)
    orderChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [{ name: '订单数', type: 'bar', data: counts, itemStyle: { color: '#6366f1' } }],
      grid: { left: 50, right: 20, bottom: 30, top: 20 },
    })
  }
}

async function loadTasks() {
  tasksLoading.value = true
  const res = await reportApi.tasks({ page: taskPage.value, page_size: taskPageSize.value })
  if (res.code === 0 && res.data) {
    const d = res.data as unknown as { items: Record<string, unknown>[]; total: number }
    tasks.value = d.items || []
    taskTotal.value = d.total || 0
  }
  tasksLoading.value = false
}

async function loadHotels() {
  const res = await hotelApi.list({ page: 1, page_size: 200 })
  if (res.code === 0 && res.data) {
    hotels.value = (res.data as unknown as { items: Record<string, unknown>[] }).items || []
  }
}

function openCreate() {
  form.report_type = 'revenue'
  form.hotel_id = ''
  form.start_date = chartStart.value
  form.end_date = chartEnd.value
  showCreate.value = true
}

async function handleCreate() {
  const payload: Record<string, unknown> = { report_type: form.report_type, start_date: form.start_date, end_date: form.end_date }
  if (form.hotel_id) payload.hotel_id = form.hotel_id
  await reportApi.createTask(payload)
  showCreate.value = false
  loadTasks()
}

function handleResize() {
  revenueChart?.resize()
  orderChart?.resize()
}

onMounted(() => {
  loadCharts()
  loadTasks()
  loadHotels()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  revenueChart?.dispose()
  orderChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

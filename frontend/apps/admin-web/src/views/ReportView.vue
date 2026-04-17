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
        <div class="flex items-center gap-2">
          <SelectField v-model="taskFilters.ordering" size="sm" @change="onTaskSortChange">
            <option value="-id">ID 最新优先</option>
            <option value="id">ID 最旧优先</option>
            <option value="report_type">类型 A→Z</option>
            <option value="-report_type">类型 Z→A</option>
            <option value="hotel__name">酒店 A→Z</option>
            <option value="-hotel__name">酒店 Z→A</option>
            <option value="start_date">开始日期升序</option>
            <option value="-start_date">开始日期降序</option>
            <option value="end_date">结束日期升序</option>
            <option value="-end_date">结束日期降序</option>
            <option value="status">状态升序</option>
            <option value="-status">状态降序</option>
            <option value="created_at">创建时间升序</option>
            <option value="-created_at">创建时间降序</option>
          </SelectField>
          <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreate">新建报表</button>
        </div>
      </div>
      <DataTable :columns="taskColumns" :rows="tasks" :loading="tasksLoading" :sort-value="taskFilters.ordering" @sort-change="onTaskTableSortChange">
        <template #col-report_type="{ value }">
          <span class="text-sm text-slate-700">{{ reportTypeLabel(String(value)) }}</span>
        </template>
        <template #col-status="{ value }">
          <StatusBadge :label="value === 'success' ? '已完成' : value === 'running' ? '运行中' : value === 'failed' ? '失败' : String(value)" :type="value === 'success' ? 'success' : value === 'failed' ? 'danger' : 'info'" />
        </template>
        <template #col-result_summary="{ value }">
          <span class="line-clamp-2 text-xs text-slate-500">{{ value || '-' }}</span>
        </template>
        <template #actions="{ row }">
          <button class="text-sm text-red-600 hover:underline" @click="handleDeleteTask(row)">删除</button>
        </template>
      </DataTable>
      <Pagination :page="taskPage" :page-size="taskPageSize" :total="taskTotal" class="px-4 pb-4" @change="p => { taskPage = p; loadTasks() }" />
    </div>

    <!-- Create Task Modal -->
    <ModalDialog :visible="showCreate" title="新建报表任务" size="md" @close="showCreate = false">
      <form class="space-y-4" @submit.prevent="handleCreate">
        <div>
          <label class="mb-1 block text-sm font-medium">报表类型</label>
          <SelectField v-model="form.report_type" required class="w-full">
            <option value="revenue_summary">营收报表</option>
            <option value="order_summary">订单报表</option>
            <option value="review_summary">评价报表</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">酒店（可选）</label>
          <SelectField v-model="form.hotel_id" class="w-full">
            <option value="">全部酒店</option>
            <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
          </SelectField>
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
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="creating" @click="handleCreate">
          {{ creating ? '创建中…' : '创建' }}
        </button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi, reportApi, hotelApi } from '@hotelink/api'
import { extractApiError } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, SelectField, useToast, useConfirm } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

interface HotelOption {
  id: number
  name: string
}

const revenueRef = ref<HTMLElement>()
const orderRef = ref<HTMLElement>()
let revenueChart: echarts.ECharts | null = null
let orderChart: echarts.ECharts | null = null

const today = new Date()
const thirtyDaysAgo = new Date(today.getTime() - 30 * 86400000)
const chartStart = ref(thirtyDaysAgo.toISOString().slice(0, 10))
const chartEnd = ref(today.toISOString().slice(0, 10))

const taskColumns = [
  { key: 'id', label: 'ID', sortField: 'id' },
  { key: 'report_type', label: '类型', sortField: 'report_type' },
  { key: 'hotel_name', label: '酒店', sortField: 'hotel__name' },
  { key: 'start_date', label: '开始日期', sortField: 'start_date' },
  { key: 'end_date', label: '结束日期', sortField: 'end_date' },
  { key: 'status', label: '状态', sortField: 'status' },
  { key: 'result_summary', label: '结果摘要' },
  { key: 'created_at', label: '创建时间', sortField: 'created_at' },
]

const tasks = ref<Record<string, unknown>[]>([])
const tasksLoading = ref(false)
const taskPage = ref(1)
const taskPageSize = ref(10)
const taskTotal = ref(0)
const taskFilters = reactive({ ordering: '-id' })

const hotels = ref<HotelOption[]>([])
const showCreate = ref(false)
const creating = ref(false)
const form = reactive({ report_type: 'revenue_summary', hotel_id: '' as string | number, start_date: '', end_date: '' })

const REPORT_TYPE_LABELS: Record<string, string> = {
  revenue_summary: '营收报表',
  order_summary: '订单报表',
  review_summary: '评价报表',
}

function reportTypeLabel(value: string) {
  return REPORT_TYPE_LABELS[value] || value || '未知类型'
}

function prependTaskRow(task: Record<string, unknown>) {
  tasks.value = [task, ...tasks.value]
  taskTotal.value += 1
}

function removeTaskRow(taskId: number) {
  tasks.value = tasks.value.filter((item) => Number(item.id) !== taskId)
  taskTotal.value = Math.max(0, taskTotal.value - 1)
}

function onTaskSortChange() {
  taskPage.value = 1
  loadTasks()
}

function onTaskTableSortChange(ordering: string) {
  if (taskFilters.ordering === ordering) return
  taskFilters.ordering = ordering
  onTaskSortChange()
}

// 加载 Charts 相关数据。
async function loadCharts() {
  const res = await dashboardApi.charts({ start_date: chartStart.value, end_date: chartEnd.value })
  if (res.code !== 0 || !res.data) {
    showToast(res.message || '图表数据加载失败', 'error')
    return
  }
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

// 加载 Tasks 相关数据。
async function loadTasks() {
  tasksLoading.value = true
  try {
    const res = await reportApi.tasks({ page: taskPage.value, page_size: taskPageSize.value, ordering: taskFilters.ordering })
    if (res.code === 0 && res.data) {
      const d = res.data as unknown as { items: Record<string, unknown>[]; total: number }
      tasks.value = d.items || []
      taskTotal.value = d.total || 0
    } else {
      showToast(res.message || '报表任务加载失败', 'error')
    }
  } catch {
    showToast('报表任务加载失败，请检查网络后重试', 'error')
  }
  tasksLoading.value = false
}

// 加载 Hotels 相关数据。
async function loadHotels() {
  try {
    const res = await hotelApi.list({ page: 1, page_size: 200 })
    if (res.code === 0 && res.data) {
      hotels.value = ((res.data as unknown as { items: HotelOption[] }).items || []).map(item => ({
        id: Number(item.id),
        name: String(item.name || ''),
      }))
    } else {
      showToast(res.message || '酒店列表加载失败', 'error')
    }
  } catch {
    showToast('酒店列表加载失败，请检查网络后重试', 'error')
  }
}

// 打开 Create 相关界面。
function openCreate() {
  form.report_type = 'revenue_summary'
  form.hotel_id = ''
  form.start_date = chartStart.value
  form.end_date = chartEnd.value
  showCreate.value = true
}

// 处理 Create 交互逻辑。
async function handleCreate() {
  if (creating.value) return
  if (!REPORT_TYPE_LABELS[form.report_type]) {
    showToast('请选择正确的报表类型', 'warning')
    return
  }
  if (!form.start_date || !form.end_date) {
    showToast('请先选择报表日期范围', 'warning')
    return
  }
  if (form.start_date > form.end_date) {
    showToast('开始日期不能晚于结束日期', 'warning')
    return
  }

  const payload: Record<string, unknown> = { report_type: form.report_type, start_date: form.start_date, end_date: form.end_date }
  if (form.hotel_id) payload.hotel_id = form.hotel_id
  creating.value = true
  try {
    const res = await reportApi.createTask(payload)
    if (res.code === 0) {
      showToast('报表任务创建成功', 'success')
      showCreate.value = false
      const created = res.data as Record<string, unknown> | undefined
      if (created && typeof created === 'object' && !Array.isArray(created)) {
        prependTaskRow(created)
      } else {
        loadTasks()
      }
    } else {
      showToast(extractApiError(res, '创建失败，请检查填写内容', {
        report_type: '报表类型',
        hotel_id: '酒店',
        start_date: '开始日期',
        end_date: '结束日期',
      }), 'error')
    }
  } catch {
    showToast('创建报表任务失败，请稍后重试', 'error')
  } finally {
    creating.value = false
  }
}

async function handleDeleteTask(row: Record<string, unknown>) {
  if (row.status === 'running') {
    showToast('运行中的任务不可删除', 'warning')
    return
  }
  if (!await confirmDialog('确定删除该报表任务？', { type: 'danger' })) return
  try {
    const res = await reportApi.deleteTask(row.id as number)
    if (res.code === 0) {
      showToast('报表任务已删除', 'success')
      removeTaskRow(row.id as number)
    } else {
      showToast(res.message || '删除失败', 'error')
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  }
}

// 处理 Resize 交互逻辑。
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

<template>
  <section class="space-y-6">
    <PageHeader title="工作台" subtitle="今日运营概览" />

    <!-- Stats Cards -->
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard title="今日订单" :value="overview.today_order_count" icon="📋" />
      <StatCard title="今日入住" :value="overview.today_check_in_count" icon="🛎️" />
      <StatCard title="今日退房" :value="overview.today_check_out_count" icon="🚪" />
      <StatCard title="当前入住率" :value="`${overview.occupancy_rate}%`" icon="📊" />
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard title="今日营收" :value="`¥${formatMoney(overview.today_revenue)}`" icon="💰" />
      <StatCard title="本月营收" :value="`¥${formatMoney(overview.month_revenue)}`" icon="📈" />
      <StatCard title="待回复评价" :value="overview.pending_review_count" icon="⭐" />
      <StatCard title="待处理报表" :value="overview.pending_report_task_count" icon="📄" />
    </div>

    <!-- Charts -->
    <div class="grid gap-6 xl:grid-cols-2">
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-900">营收趋势</h3>
          <SelectField v-model="dateRange" size="sm" @change="loadCharts">
            <option value="7">近7天</option>
            <option value="14">近14天</option>
            <option value="30">近30天</option>
          </SelectField>
        </div>
        <div ref="revenueChartRef" class="h-72" />
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-base font-semibold text-slate-900">订单趋势</h3>
        <div ref="orderChartRef" class="h-72" />
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h3 class="mb-4 text-base font-semibold text-slate-900">快捷操作</h3>
      <div class="flex flex-wrap gap-3">
        <router-link to="/admin/orders" class="rounded-lg bg-teal-50 px-4 py-2 text-sm font-medium text-teal-700 transition-colors hover:bg-teal-100">查看订单</router-link>
        <router-link to="/admin/hotels" class="rounded-lg bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100">酒店管理</router-link>
        <router-link to="/admin/reviews" class="rounded-lg bg-yellow-50 px-4 py-2 text-sm font-medium text-yellow-700 transition-colors hover:bg-yellow-100">评价管理</router-link>
        <router-link to="/admin/reports" class="rounded-lg bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 transition-colors hover:bg-purple-100">经营报表</router-link>
        <router-link to="/admin/ai" class="rounded-lg bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100">AI 助手</router-link>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@hotelink/api'
import { formatMoney, formatDate } from '@hotelink/utils'
import { StatCard, PageHeader, SelectField } from '@hotelink/ui'

const overview = reactive({
  today_order_count: 0,
  today_check_in_count: 0,
  today_check_out_count: 0,
  today_revenue: 0,
  month_revenue: 0,
  occupancy_rate: 0,
  pending_review_count: 0,
  pending_report_task_count: 0,
})

const dateRange = ref('7')
const revenueChartRef = ref<HTMLElement>()
const orderChartRef = ref<HTMLElement>()

let revenueChart: echarts.ECharts | null = null
let orderChart: echarts.ECharts | null = null

// 加载 Overview 相关数据。
async function loadOverview() {
  const res = await dashboardApi.overview()
  if (res.code === 0 && res.data) Object.assign(overview, res.data)
}

// 加载 Charts 相关数据。
async function loadCharts() {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - parseInt(dateRange.value) + 1)

  const res = await dashboardApi.charts({
    start_date: formatDate(start),
    end_date: formatDate(end),
  })
  if (res.code !== 0 || !res.data) return

  const items = res.data.items
  const dates = items.map(i => i.date.slice(5))
  const revenues = items.map(i => i.revenue)
  const orders = items.map(i => i.order_count)

  await nextTick()

  if (revenueChartRef.value) {
    if (!revenueChart) revenueChart = echarts.init(revenueChartRef.value)
    revenueChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [{ name: '营收', type: 'line', data: revenues, smooth: true, areaStyle: { opacity: 0.15 }, itemStyle: { color: '#0f766e' } }],
    })
  }

  if (orderChartRef.value) {
    if (!orderChart) orderChart = echarts.init(orderChartRef.value)
    orderChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{ name: '订单量', type: 'bar', data: orders, itemStyle: { color: '#14b8a6', borderRadius: [4, 4, 0, 0] } }],
    })
  }
}

onMounted(() => {
  loadOverview()
  loadCharts()

  window.addEventListener('resize', () => {
    revenueChart?.resize()
    orderChart?.resize()
  })
})
</script>

<template>
  <section>
    <PageHeader title="AI 助手" subtitle="智能报表分析与评价总结" />

    <div class="grid gap-6 lg:grid-cols-2">
      <!-- Report Summary -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-sm font-semibold text-slate-700">📊 营收报告分析</h3>
        <form class="space-y-4" @submit.prevent="getReportSummary">
          <div>
            <label class="mb-1 block text-sm font-medium">酒店（可选）</label>
            <select v-model="reportForm.hotel_id" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="">全部酒店</option>
              <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-medium">开始日期</label>
              <input v-model="reportForm.start_date" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">结束日期</label>
              <input v-model="reportForm.end_date" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <button type="submit" class="w-full rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="reportLoading">
            {{ reportLoading ? '分析中…' : '生成报告分析' }}
          </button>
        </form>
        <div v-if="reportResult" class="mt-4 rounded-lg bg-teal-50 p-4 text-sm text-teal-900 whitespace-pre-wrap">{{ reportResult }}</div>
      </div>

      <!-- Review Summary -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-sm font-semibold text-slate-700">💬 评价总结分析</h3>
        <form class="space-y-4" @submit.prevent="getReviewSummary">
          <div>
            <label class="mb-1 block text-sm font-medium">酒店（可选）</label>
            <select v-model="reviewForm.hotel_id" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="">全部酒店</option>
              <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-medium">开始日期</label>
              <input v-model="reviewForm.start_date" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">结束日期</label>
              <input v-model="reviewForm.end_date" type="date" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <button type="submit" class="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700" :disabled="reviewLoading">
            {{ reviewLoading ? '分析中…' : '生成评价总结' }}
          </button>
        </form>
        <div v-if="reviewResult" class="mt-4 rounded-lg bg-indigo-50 p-4 text-sm text-indigo-900 whitespace-pre-wrap">{{ reviewResult }}</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { aiApi, hotelApi } from '@hotelink/api'
import { PageHeader } from '@hotelink/ui'

const today = new Date()
const thirtyDaysAgo = new Date(today.getTime() - 30 * 86400000)
const defaultStart = thirtyDaysAgo.toISOString().slice(0, 10)
const defaultEnd = today.toISOString().slice(0, 10)

const hotels = ref<Record<string, unknown>[]>([])

const reportForm = reactive({ hotel_id: '' as string | number, start_date: defaultStart, end_date: defaultEnd })
const reportLoading = ref(false)
const reportResult = ref('')

const reviewForm = reactive({ hotel_id: '' as string | number, start_date: defaultStart, end_date: defaultEnd })
const reviewLoading = ref(false)
const reviewResult = ref('')

// 加载 Hotels 相关数据。
async function loadHotels() {
  const res = await hotelApi.list({ page: 1, page_size: 200 })
  if (res.code === 0 && res.data) {
    hotels.value = (res.data as unknown as { items: Record<string, unknown>[] }).items || []
  }
}

// 处理 getReportSummary 业务流程。
async function getReportSummary() {
  reportLoading.value = true
  reportResult.value = ''
  const payload: Record<string, unknown> = { start_date: reportForm.start_date, end_date: reportForm.end_date }
  if (reportForm.hotel_id) payload.hotel_id = reportForm.hotel_id
  const res = await aiApi.reportSummary(payload)
  if (res.code === 0 && res.data) {
    reportResult.value = (res.data as Record<string, unknown>).summary as string || '暂无分析结果'
  }
  reportLoading.value = false
}

// 处理 getReviewSummary 业务流程。
async function getReviewSummary() {
  reviewLoading.value = true
  reviewResult.value = ''
  const payload: Record<string, unknown> = { start_date: reviewForm.start_date, end_date: reviewForm.end_date }
  if (reviewForm.hotel_id) payload.hotel_id = reviewForm.hotel_id
  const res = await aiApi.reviewSummary(payload)
  if (res.code === 0 && res.data) {
    reviewResult.value = (res.data as Record<string, unknown>).summary as string || '暂无分析结果'
  }
  reviewLoading.value = false
}

onMounted(loadHotels)
</script>

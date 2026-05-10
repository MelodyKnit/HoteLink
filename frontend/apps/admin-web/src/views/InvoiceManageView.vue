<template>
  <section class="space-y-6">
    <PageHeader title="发票管理" subtitle="处理用户提交的电子发票申请，回写开票号码、附件与处理结果">
      <template #actions>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50" @click="reload">
          刷新
        </button>
      </template>
    </PageHeader>

    <div class="grid gap-4 md:grid-cols-4">
      <div v-for="card in statCards" :key="card.label" class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
        <p class="text-xs text-slate-400">{{ card.label }}</p>
        <p class="mt-2 text-2xl font-bold" :class="card.color">{{ card.value }}</p>
      </div>
    </div>

    <div class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
        <div class="grid flex-1 gap-3 md:grid-cols-5">
          <div class="md:col-span-2">
            <label class="mb-1 block text-xs font-medium text-slate-500">关键词</label>
            <input
              v-model.trim="filters.keyword"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-teal-500"
              placeholder="订单号 / 抬头 / 税号 / 手机"
              @keyup.enter="search"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">处理状态</label>
            <SelectField v-model="filters.status" class="w-full">
              <option value="">全部状态</option>
              <option value="pending">待处理</option>
              <option value="issued">已开票</option>
              <option value="cancelled">已取消</option>
            </SelectField>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">抬头类型</label>
            <SelectField v-model="filters.invoice_type" class="w-full">
              <option value="">全部类型</option>
              <option value="personal">个人</option>
              <option value="company">企业</option>
            </SelectField>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">排序</label>
            <SelectField v-model="filters.ordering" class="w-full">
              <option value="-id">最新申请</option>
              <option value="amount">金额从低到高</option>
              <option value="-amount">金额从高到低</option>
              <option value="-processed_at">最近处理</option>
            </SelectField>
          </div>
        </div>
        <div class="flex gap-2">
          <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50" @click="resetFilters">重置</button>
          <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-700" @click="search">查询</button>
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-100">
      <div class="overflow-x-auto">
        <table class="min-w-[1120px] w-full text-left text-sm">
          <thead class="bg-slate-50 text-xs font-semibold text-slate-500">
            <tr>
              <th class="px-4 py-3">申请信息</th>
              <th class="px-4 py-3">用户/订单</th>
              <th class="px-4 py-3">抬头信息</th>
              <th class="px-4 py-3">金额</th>
              <th class="px-4 py-3">状态</th>
              <th class="px-4 py-3">处理结果</th>
              <th class="px-4 py-3">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading">
              <td colspan="7" class="px-4 py-12 text-center text-slate-400">加载中…</td>
            </tr>
            <tr v-else-if="!items.length">
              <td colspan="7" class="px-4 py-12 text-center text-slate-400">暂无发票申请</td>
            </tr>
            <template v-else>
              <tr v-for="row in items" :key="row.id" class="align-top transition-colors hover:bg-slate-50/70">
                <td class="px-4 py-4">
                  <p class="font-semibold text-slate-800">#{{ row.id }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ formatDateTime(row.created_at) || '-' }}</p>
                  <p class="mt-2 text-xs text-slate-500">{{ row.invoice_type === 'company' ? '企业发票' : '个人发票' }}</p>
                </td>
                <td class="px-4 py-4">
                  <p class="font-medium text-slate-800">{{ row.username || row.guest_name || '未知用户' }}</p>
                  <p class="mt-1 text-xs text-slate-500">订单 {{ row.order_no }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ row.hotel_name }} · {{ row.room_type_name }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ row.check_in_date }} 至 {{ row.check_out_date }}</p>
                </td>
                <td class="px-4 py-4">
                  <p class="max-w-[260px] truncate font-medium text-slate-800" :title="row.title">{{ row.title || '未填写' }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ row.email || '未填写邮箱' }}</p>
                  <p class="mt-1 max-w-[260px] truncate text-xs text-slate-400" :title="row.tax_no">{{ row.tax_no || '个人抬头无税号' }}</p>
                </td>
                <td class="px-4 py-4">
                  <p class="font-semibold tabular-nums text-slate-900">¥{{ formatMoney(row.amount) }}</p>
                </td>
                <td class="px-4 py-4">
                  <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium" :class="badgeClass(row.status)">
                    {{ statusLabel(row) }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <template v-if="row.status === 'issued'">
                    <p class="text-xs text-slate-500">发票号码</p>
                    <p class="mt-1 font-medium text-slate-800">{{ row.invoice_no || '-' }}</p>
                    <a v-if="row.invoice_file_url" :href="row.invoice_file_url" target="_blank" rel="noreferrer" class="mt-2 inline-flex text-xs font-medium text-teal-600 hover:underline">查看电子票</a>
                  </template>
                  <template v-else-if="row.status === 'cancelled'">
                    <p class="max-w-[260px] text-xs leading-5 text-slate-500">{{ row.processor_remark || '已取消' }}</p>
                  </template>
                  <span v-else class="text-xs text-slate-400">等待财务处理</span>
                </td>
                <td class="px-4 py-4">
                  <div class="flex flex-col items-start gap-2">
                    <button class="text-xs font-medium text-slate-600 hover:text-teal-600 hover:underline" @click="openDetail(row)">查看详情</button>
                    <template v-if="row.status === 'pending'">
                      <button class="text-xs font-medium text-teal-600 hover:underline" @click="openProcess(row, 'issue')">开票</button>
                      <button class="text-xs font-medium text-red-500 hover:underline" @click="openProcess(row, 'cancel')">取消申请</button>
                    </template>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="changePage" />
    </div>

    <ModalDialog :visible="showDetail" title="发票申请详情" size="lg" @close="showDetail = false">
      <div v-if="activeInvoice" class="grid gap-4 text-sm md:grid-cols-2">
        <div class="rounded-xl bg-slate-50 p-4">
          <p class="text-xs text-slate-400">订单信息</p>
          <p class="mt-2 font-semibold text-slate-800">{{ activeInvoice.order_no }}</p>
          <p class="mt-1 text-slate-500">{{ activeInvoice.hotel_name }} · {{ activeInvoice.room_type_name }}</p>
          <p class="mt-1 text-slate-500">{{ activeInvoice.check_in_date }} 至 {{ activeInvoice.check_out_date }}</p>
        </div>
        <div class="rounded-xl bg-slate-50 p-4">
          <p class="text-xs text-slate-400">购买方信息</p>
          <p class="mt-2 font-semibold text-slate-800">{{ activeInvoice.title }}</p>
          <p class="mt-1 text-slate-500">{{ activeInvoice.email || '未填写邮箱' }}</p>
          <p class="mt-1 text-slate-500">{{ activeInvoice.tax_no || '个人抬头无税号' }}</p>
        </div>
        <div class="rounded-xl bg-slate-50 p-4 md:col-span-2">
          <p class="text-xs text-slate-400">处理信息</p>
          <div class="mt-2 grid gap-2 md:grid-cols-3">
            <p>状态：{{ statusLabel(activeInvoice) }}</p>
            <p>处理人：{{ activeInvoice.processed_by_name || '-' }}</p>
            <p>处理时间：{{ formatDateTime(activeInvoice.processed_at || '') || '-' }}</p>
            <p>发票代码：{{ activeInvoice.invoice_code || '-' }}</p>
            <p>发票号码：{{ activeInvoice.invoice_no || '-' }}</p>
            <p>开票时间：{{ formatDateTime(activeInvoice.issued_at || '') || '-' }}</p>
          </div>
          <p v-if="activeInvoice.processor_remark" class="mt-3 rounded-lg bg-white px-3 py-2 text-slate-600">备注：{{ activeInvoice.processor_remark }}</p>
        </div>
      </div>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showDetail = false">关闭</button>
      </template>
    </ModalDialog>

    <ModalDialog :visible="showProcess" :title="processAction === 'issue' ? '开具电子发票' : '取消发票申请'" size="md" @close="closeProcess">
      <div v-if="activeInvoice" class="space-y-4">
        <div class="rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          <p class="font-medium text-slate-800">{{ activeInvoice.title }} · ¥{{ formatMoney(activeInvoice.amount) }}</p>
          <p class="mt-1 text-xs text-slate-400">订单 {{ activeInvoice.order_no }}，处理后用户端发票中心与通知中心会同步显示。</p>
        </div>

        <template v-if="processAction === 'issue'">
          <div class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-xs text-slate-500">发票号码</label>
              <input v-model.trim="processForm.invoice_no" class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition" :class="processErrors.invoice_no ? 'border-red-300 bg-red-50' : 'border-slate-200 focus:border-teal-500'" placeholder="必填" />
              <p v-if="processErrors.invoice_no" class="mt-1 text-xs text-red-500">{{ processErrors.invoice_no }}</p>
            </div>
            <div>
              <label class="mb-1 block text-xs text-slate-500">发票代码</label>
              <input v-model.trim="processForm.invoice_code" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-teal-500" placeholder="数电票可为空" />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-xs text-slate-500">电子发票文件链接</label>
            <input v-model.trim="processForm.invoice_file_url" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-teal-500" placeholder="https:// 或站内 /media/ 链接" />
          </div>
          <div>
            <label class="mb-1 block text-xs text-slate-500">处理备注</label>
            <textarea v-model.trim="processForm.processor_remark" rows="3" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-teal-500" placeholder="例如：已通过电子发票平台开具" />
          </div>
        </template>

        <template v-else>
          <div>
            <label class="mb-1 block text-xs text-slate-500">取消原因</label>
            <textarea v-model.trim="processForm.processor_remark" rows="4" class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition" :class="processErrors.processor_remark ? 'border-red-300 bg-red-50' : 'border-slate-200 focus:border-teal-500'" placeholder="请说明无法开票的原因，用户端会看到该说明" />
            <p v-if="processErrors.processor_remark" class="mt-1 text-xs text-red-500">{{ processErrors.processor_remark }}</p>
          </div>
        </template>

        <div v-if="processError" class="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{{ processError }}</div>
      </div>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="closeProcess">取消</button>
        <button class="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50" :class="processAction === 'issue' ? 'bg-teal-600 hover:bg-teal-700' : 'bg-red-500 hover:bg-red-600'" :disabled="processing" @click="submitProcess">
          {{ processing ? '提交中…' : processAction === 'issue' ? '确认开票' : '确认取消' }}
        </button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { adminInvoiceApi } from '@hotelink/api'
import type { InvoiceRequestItem } from '@hotelink/api'
import { INVOICE_STATUS_MAP, extractApiError, extractApiFieldErrors, formatDateTime, formatMoney } from '@hotelink/utils'
import { ModalDialog, PageHeader, Pagination, SelectField, useToast } from '@hotelink/ui'

const { showToast } = useToast()

type InvoiceAction = 'issue' | 'cancel'

const loading = ref(false)
const items = ref<InvoiceRequestItem[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const summary = ref({ pending: 0, issued: 0, cancelled: 0, total_amount: '0.00' })
const filters = reactive({
  keyword: '',
  status: 'pending',
  invoice_type: '',
  ordering: '-id',
})

const showDetail = ref(false)
const showProcess = ref(false)
const activeInvoice = ref<InvoiceRequestItem | null>(null)
const processAction = ref<InvoiceAction>('issue')
const processing = ref(false)
const processError = ref('')
const processErrors = ref<Partial<Record<'invoice_no' | 'processor_remark', string>>>({})
const processForm = reactive({
  invoice_code: '',
  invoice_no: '',
  invoice_file_url: '',
  processor_remark: '',
})

const statCards = computed(() => [
  { label: '待处理申请', value: summary.value.pending, color: 'text-amber-600' },
  { label: '已开票', value: summary.value.issued, color: 'text-emerald-600' },
  { label: '已取消', value: summary.value.cancelled, color: 'text-slate-500' },
  { label: '筛选金额', value: `¥${formatMoney(summary.value.total_amount)}`, color: 'text-slate-800' },
])

function badgeClass(status: string): string {
  const meta = INVOICE_STATUS_MAP[status] || INVOICE_STATUS_MAP.pending
  return `${meta.bg} ${meta.color}`
}

function statusLabel(row: InvoiceRequestItem): string {
  return row.status_label || INVOICE_STATUS_MAP[row.status]?.label || row.status
}

function buildParams() {
  return {
    page: page.value,
    page_size: pageSize.value,
    keyword: filters.keyword || undefined,
    status: filters.status || undefined,
    invoice_type: filters.invoice_type || undefined,
    ordering: filters.ordering || undefined,
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await adminInvoiceApi.list(buildParams())
    if (res.code === 0 && res.data) {
      items.value = res.data.items || []
      total.value = res.data.total || 0
      summary.value = res.data.summary || { pending: 0, issued: 0, cancelled: 0, total_amount: '0.00' }
    } else {
      showToast(res.message || '加载发票申请失败', 'error')
    }
  } catch {
    showToast('加载发票申请失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  loadList()
}

function reload() {
  loadList()
}

function resetFilters() {
  filters.keyword = ''
  filters.status = 'pending'
  filters.invoice_type = ''
  filters.ordering = '-id'
  search()
}

function changePage(nextPage: number) {
  page.value = nextPage
  loadList()
}

function openDetail(row: InvoiceRequestItem) {
  activeInvoice.value = row
  showDetail.value = true
}

function openProcess(row: InvoiceRequestItem, action: InvoiceAction) {
  activeInvoice.value = row
  processAction.value = action
  processForm.invoice_code = row.invoice_code || ''
  processForm.invoice_no = row.invoice_no || ''
  processForm.invoice_file_url = row.invoice_file_url || ''
  processForm.processor_remark = action === 'issue' ? '已通过电子发票平台开具' : ''
  processError.value = ''
  processErrors.value = {}
  showProcess.value = true
}

function closeProcess() {
  showProcess.value = false
  processError.value = ''
  processErrors.value = {}
}

function validateProcessForm(): boolean {
  const errors: Partial<Record<'invoice_no' | 'processor_remark', string>> = {}
  if (processAction.value === 'issue' && !processForm.invoice_no.trim()) {
    errors.invoice_no = '请填写发票号码'
  }
  if (processAction.value === 'cancel' && !processForm.processor_remark.trim()) {
    errors.processor_remark = '请填写取消原因'
  }
  processErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submitProcess() {
  if (!activeInvoice.value || !validateProcessForm()) return
  processing.value = true
  processError.value = ''
  try {
    const res = await adminInvoiceApi.process({
      invoice_id: activeInvoice.value.id,
      action: processAction.value,
      invoice_code: processForm.invoice_code,
      invoice_no: processForm.invoice_no,
      invoice_file_url: processForm.invoice_file_url,
      processor_remark: processForm.processor_remark,
    })
    if (res.code === 0) {
      showToast(processAction.value === 'issue' ? '发票已开具' : '发票申请已取消', 'success')
      closeProcess()
      await loadList()
    } else {
      processErrors.value = {
        ...processErrors.value,
        ...extractApiFieldErrors(res, {
          invoice_no: '发票号码',
          processor_remark: '处理原因',
        }),
      }
      processError.value = extractApiError(res, '处理发票申请失败')
      showToast(processError.value, 'error')
    }
  } catch {
    processError.value = '处理发票申请失败，请检查网络后重试'
    showToast(processError.value, 'error')
  } finally {
    processing.value = false
  }
}

onMounted(loadList)
</script>

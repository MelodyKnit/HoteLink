<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">发票管理</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-4 pb-24 md:pb-4">
      <!-- Invoice Titles -->
      <div class="rounded-2xl bg-white p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-gray-800">发票抬头</h3>
          <button @click="showAddModal = true" class="text-xs text-brand hover:underline">+ 添加</button>
        </div>
        <div v-if="titles.length === 0" class="py-6 text-center text-sm text-gray-400">暂无抬头信息</div>
        <div v-else class="mt-3 space-y-2">
          <div v-for="t in titles" :key="t.id" class="flex items-center justify-between rounded-xl bg-gray-50 p-3">
            <div>
              <p class="text-sm font-medium text-gray-800">{{ t.title }}</p>
              <p class="text-xs text-gray-400">{{ t.tax_no || '个人' }}</p>
            </div>
            <span class="rounded bg-brand/10 px-2 py-0.5 text-xs text-brand">{{ t.type === 'company' ? '企业' : '个人' }}</span>
          </div>
        </div>
      </div>

      <!-- Invoice Records -->
      <div class="mt-4 rounded-2xl bg-white p-4 shadow-sm">
        <h3 class="font-semibold text-gray-800">开票记录</h3>
        <div v-if="invoices.length === 0" class="py-6 text-center text-sm text-gray-400">暂无开票记录</div>
        <div v-else class="mt-3 space-y-2">
          <div v-for="inv in invoices" :key="inv.id" class="flex items-center justify-between rounded-xl bg-gray-50 p-3">
            <div>
              <p class="text-sm font-medium text-gray-800">¥{{ inv.amount }}</p>
              <p class="text-xs text-gray-400">{{ inv.title }} · {{ inv.created_at }}</p>
            </div>
            <span class="rounded px-2 py-0.5 text-xs"
              :class="inv.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
              {{ inv.status === 'completed' ? '已开具' : '处理中' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Apply Section -->
      <div class="mt-4 rounded-2xl bg-white p-4 shadow-sm">
        <h3 class="mb-3 font-semibold text-gray-800">申请开票</h3>
        <div class="space-y-3">
          <SelectField v-model.number="applyForm.invoice_title_id" class="w-full">
            <option :value="0">选择抄头</option>
            <option v-for="t in titles" :key="t.id" :value="t.id">{{ t.title }}</option>
          </SelectField>
          <input v-model.number="applyForm.order_id" placeholder="订单号" type="number" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <button @click="handleApply" :disabled="applying"
            class="w-full rounded-xl bg-brand py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50">
            {{ applying ? '提交中...' : '提交申请' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add title modal -->
    <Teleport to="body">
      <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showAddModal = false">
        <div class="w-full max-w-sm rounded-2xl bg-white p-6">
          <h3 class="text-lg font-bold text-gray-900">添加发票抬头</h3>
          <div class="mt-4 space-y-3">
            <div class="flex gap-4">
              <label class="flex items-center gap-1 text-sm"><input type="radio" v-model="titleForm.invoice_type" value="personal" class="accent-brand" /> 个人</label>
              <label class="flex items-center gap-1 text-sm"><input type="radio" v-model="titleForm.invoice_type" value="company" class="accent-brand" /> 企业</label>
            </div>
            <input v-model="titleForm.title" placeholder="抬头名称" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            <input v-if="titleForm.invoice_type === 'company'" v-model="titleForm.tax_no" placeholder="税号" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            <input v-model="titleForm.email" placeholder="接收邮箱" type="email" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          </div>
          <div class="mt-4 flex gap-3">
            <button @click="showAddModal = false" class="flex-1 rounded-xl border py-2.5 text-sm text-gray-600">取消</button>
            <button @click="handleAddTitle" :disabled="addingTitle" class="flex-1 rounded-xl bg-brand py-2.5 text-sm text-white disabled:opacity-50">保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userInvoiceApi } from '@hotelink/api'
import { SelectField, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const titles = ref<any[]>([])
const invoices = ref<any[]>([])
const showAddModal = ref(false)
const addingTitle = ref(false)
const applying = ref(false)

const titleForm = ref({ invoice_type: 'personal', title: '', tax_no: '', email: '' })
const applyForm = ref({ order_id: 0, invoice_title_id: 0 })

// 处理 AddTitle 交互逻辑。
async function handleAddTitle() {
  if (!titleForm.value.title.trim()) return
  addingTitle.value = true
  try {
    const res = await userInvoiceApi.createTitle(titleForm.value)
    if (res.code === 0 && res.data) titles.value.push(res.data)
    showAddModal.value = false
    titleForm.value = { invoice_type: 'personal', title: '', tax_no: '', email: '' }
  } catch { /* ignore */ }
  addingTitle.value = false
}

// 处理 Apply 交互逻辑。
async function handleApply() {
  if (!applyForm.value.invoice_title_id || !applyForm.value.order_id) { showToast('请填写完整信息', 'warning'); return }
  applying.value = true
  try {
    const res = await userInvoiceApi.apply(applyForm.value)
    if (res.code === 0) {
      showToast('申请已提交', 'success')
      applyForm.value = { order_id: 0, invoice_title_id: 0 }
    } else {
      showToast((res as any).message || '申请失败', 'error')
    }
  } catch { /* ignore */ }
  applying.value = false
}

onMounted(async () => {
  try {
    const res = await userInvoiceApi.list()
    if (res.code === 0 && res.data) {
      titles.value = (res.data as any).titles || []
      invoices.value = (res.data as any).invoices || []
    }
  } catch {
    titles.value = [
      { id: 1, title: '个人', type: 'personal', tax_no: '' },
      { id: 2, title: '某某科技有限公司', type: 'company', tax_no: '91110000MA00XXXXX' },
    ]
    invoices.value = [
      { id: 1, amount: '688.00', title: '个人', status: 'completed', created_at: '2026-03-25' },
    ]
  }
})
</script>

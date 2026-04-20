<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="goBack()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">发票管理</h1>
    </header>

    <div v-if="pageLoading" class="flex justify-center py-20">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent"></div>
    </div>

    <div v-else class="mx-auto max-w-2xl px-4 py-4 pb-24 md:pb-4">
      <div class="rounded-2xl bg-white p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-gray-800">发票抬头</h3>
          <button @click="openAddModal" class="text-xs text-brand hover:underline">+ 添加</button>
        </div>
        <div v-if="titles.length === 0" class="py-6 text-center text-sm text-gray-400">暂无抬头信息</div>
        <div v-else class="mt-3 space-y-2">
          <div v-for="t in titles" :key="t.id" class="flex items-center justify-between rounded-xl bg-gray-50 p-3">
            <div>
              <p class="text-sm font-medium text-gray-800">{{ t.title }}</p>
              <p class="text-xs text-gray-400">{{ t.tax_no || '个人' }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button @click="openEditTitle(t)" class="text-xs text-brand hover:underline">编辑</button>
              <button @click="handleDeleteTitle(t)" class="text-xs text-red-500 hover:underline">删除</button>
              <span class="rounded bg-brand/10 px-2 py-0.5 text-xs text-brand">{{ t.type === 'company' ? '企业' : '个人' }}</span>
            </div>
          </div>
        </div>
      </div>

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

      <div class="mt-4 rounded-2xl bg-white p-4 shadow-sm">
        <h3 class="mb-3 font-semibold text-gray-800">申请开票</h3>
        <div class="space-y-3">
          <div>
            <SelectField v-model.number="applyForm.invoice_title_id" class="w-full">
              <option :value="0">选择抬头</option>
              <option v-for="t in titles" :key="t.id" :value="t.id">{{ t.title }}</option>
            </SelectField>
            <p v-if="applyErrors.invoice_title_id" class="mt-1 text-xs text-red-500">{{ applyErrors.invoice_title_id }}</p>
          </div>

          <div>
            <input
              v-model.number="applyForm.order_id"
              placeholder="订单号"
              type="number"
              class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
              :class="applyErrors.order_id ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="clearApplyError('order_id')"
              @blur="validateApplyField('order_id')"
            />
            <p v-if="applyErrors.order_id" class="mt-1 text-xs text-red-500">{{ applyErrors.order_id }}</p>
            <p v-else class="mt-1 text-xs text-gray-400">请输入已完成支付的订单编号，避免重复申请。</p>
          </div>

          <button
            @click="handleApply"
            :disabled="applying"
            class="w-full rounded-xl bg-brand py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {{ applying ? '提交中...' : '提交申请' }}
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showAddModal = false">
        <div class="w-full max-w-sm rounded-2xl bg-white p-6">
          <h3 class="text-lg font-bold text-gray-900">添加发票抬头</h3>
          <div class="mt-4 space-y-3">
            <div class="flex gap-4">
              <label class="flex items-center gap-1 text-sm"><input type="radio" v-model="titleForm.invoice_type" value="personal" class="accent-brand" /> 个人</label>
              <label class="flex items-center gap-1 text-sm"><input type="radio" v-model="titleForm.invoice_type" value="company" class="accent-brand" /> 企业</label>
            </div>

            <div>
              <input
                v-model="titleForm.title"
                placeholder="抬头名称"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
                :class="titleErrors.title ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="clearTitleError('title')"
                @blur="validateTitleField('title')"
              />
              <p v-if="titleErrors.title" class="mt-1 text-xs text-red-500">{{ titleErrors.title }}</p>
            </div>

            <div v-if="titleForm.invoice_type === 'company'">
              <input
                v-model="titleForm.tax_no"
                placeholder="税号"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
                :class="titleErrors.tax_no ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="handleTaxNoInput"
                @blur="validateTitleField('tax_no')"
              />
              <p v-if="titleErrors.tax_no" class="mt-1 text-xs text-red-500">{{ titleErrors.tax_no }}</p>
              <p v-else class="mt-1 text-xs text-gray-400">企业抬头需填写 15-20 位税号。</p>
            </div>

            <div>
              <input
                v-model="titleForm.email"
                placeholder="接收邮箱"
                type="email"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
                :class="titleErrors.email ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="clearTitleError('email')"
                @blur="validateTitleField('email')"
              />
              <p v-if="titleErrors.email" class="mt-1 text-xs text-red-500">{{ titleErrors.email }}</p>
              <p v-else class="mt-1 text-xs text-gray-400">开票完成后会发送到这个邮箱，请确认可正常接收。</p>
            </div>
          </div>
          <div class="mt-4 flex gap-3">
            <button @click="showAddModal = false" class="flex-1 rounded-xl border py-2.5 text-sm text-gray-600">取消</button>
            <button @click="handleAddTitle" :disabled="addingTitle" class="flex-1 rounded-xl bg-brand py-2.5 text-sm text-white disabled:opacity-50">保存</button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showEditModal = false">
        <div class="w-full max-w-sm rounded-2xl bg-white p-6">
          <h3 class="text-lg font-bold text-gray-900">编辑发票抬头</h3>
          <div class="mt-4 space-y-3">
            <div class="flex gap-4">
              <label class="flex items-center gap-1 text-sm"><input type="radio" v-model="editTitleForm.invoice_type" value="personal" class="accent-brand" /> 个人</label>
              <label class="flex items-center gap-1 text-sm"><input type="radio" v-model="editTitleForm.invoice_type" value="company" class="accent-brand" /> 企业</label>
            </div>
            <div>
              <input
                v-model="editTitleForm.title"
                placeholder="抬头名称"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
                :class="editTitleErrors.title ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="clearEditTitleError('title')"
                @blur="validateEditTitleField('title')"
              />
              <p v-if="editTitleErrors.title" class="mt-1 text-xs text-red-500">{{ editTitleErrors.title }}</p>
            </div>
            <div v-if="editTitleForm.invoice_type === 'company'">
              <input
                v-model="editTitleForm.tax_no"
                placeholder="税号"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
                :class="editTitleErrors.tax_no ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="handleEditTaxNoInput"
                @blur="validateEditTitleField('tax_no')"
              />
              <p v-if="editTitleErrors.tax_no" class="mt-1 text-xs text-red-500">{{ editTitleErrors.tax_no }}</p>
            </div>
            <div>
              <input
                v-model="editTitleForm.email"
                placeholder="接收邮箱"
                type="email"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
                :class="editTitleErrors.email ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
                @input="clearEditTitleError('email')"
                @blur="validateEditTitleField('email')"
              />
              <p v-if="editTitleErrors.email" class="mt-1 text-xs text-red-500">{{ editTitleErrors.email }}</p>
            </div>
          </div>
          <div class="mt-4 flex gap-3">
            <button @click="showEditModal = false" class="flex-1 rounded-xl border py-2.5 text-sm text-gray-600">取消</button>
            <button @click="handleEditTitle" :disabled="editingTitle" class="flex-1 rounded-xl bg-brand py-2.5 text-sm text-white disabled:opacity-50">保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { userInvoiceApi } from '@hotelink/api'
import { SelectField, useToast, useConfirm } from '@hotelink/ui'
import { extractApiError, extractApiFieldErrors, isValidEmailAddress, isValidTaxNumber } from '@hotelink/utils'
import { useRouter } from 'vue-router'

type TitleField = 'title' | 'tax_no' | 'email'
type ApplyField = 'order_id' | 'invoice_title_id'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()
const router = useRouter()

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/my')
}

const titles = ref<any[]>([])
const invoices = ref<any[]>([])
const showAddModal = ref(false)
const addingTitle = ref(false)
const applying = ref(false)
const pageLoading = ref(true)

const titleForm = ref({ invoice_type: 'personal', title: '', tax_no: '', email: '' })
const applyForm = ref({ order_id: 0, invoice_title_id: 0 })
const titleErrors = ref<Partial<Record<TitleField, string>>>({})
const applyErrors = ref<Partial<Record<ApplyField, string>>>({})

function openAddModal() {
  showAddModal.value = true
  titleForm.value = { invoice_type: 'personal', title: '', tax_no: '', email: '' }
  titleErrors.value = {}
}

function clearTitleError(field: TitleField) {
  if (titleErrors.value[field]) {
    titleErrors.value = { ...titleErrors.value, [field]: undefined }
  }
}

function clearApplyError(field: ApplyField) {
  if (applyErrors.value[field]) {
    applyErrors.value = { ...applyErrors.value, [field]: undefined }
  }
}

function handleTaxNoInput() {
  titleForm.value.tax_no = titleForm.value.tax_no.replace(/\s/g, '').toUpperCase()
  clearTitleError('tax_no')
}

function getTitleFieldError(field: TitleField): string {
  switch (field) {
    case 'title':
      if (!titleForm.value.title.trim()) return '请输入抬头名称'
      return titleForm.value.title.trim().length > 100 ? '抬头名称不能超过 100 个字符' : ''
    case 'tax_no':
      if (titleForm.value.invoice_type !== 'company') return ''
      if (!titleForm.value.tax_no.trim()) return '企业抬头请填写税号'
      return isValidTaxNumber(titleForm.value.tax_no) ? '' : '税号格式不正确，请检查后重试'
    case 'email':
      if (!titleForm.value.email.trim()) return '请输入接收邮箱'
      return isValidEmailAddress(titleForm.value.email) ? '' : '邮箱格式不正确'
    default:
      return ''
  }
}

function validateTitleField(field: TitleField) {
  titleErrors.value = {
    ...titleErrors.value,
    [field]: getTitleFieldError(field) || undefined,
  }
}

function validateTitleForm(): boolean {
  const nextErrors: Partial<Record<TitleField, string>> = {}
  titleForm.value.title = titleForm.value.title.trim()
  titleForm.value.email = titleForm.value.email.trim()
  titleForm.value.tax_no = titleForm.value.tax_no.trim().toUpperCase()

  ;(['title', 'tax_no', 'email'] as TitleField[]).forEach((field) => {
    const message = getTitleFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  titleErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

function getApplyFieldError(field: ApplyField): string {
  switch (field) {
    case 'invoice_title_id':
      return applyForm.value.invoice_title_id > 0 ? '' : '请选择发票抬头'
    case 'order_id':
      return applyForm.value.order_id > 0 ? '' : '请输入有效的订单号'
    default:
      return ''
  }
}

function validateApplyField(field: ApplyField) {
  applyErrors.value = {
    ...applyErrors.value,
    [field]: getApplyFieldError(field) || undefined,
  }
}

function validateApplyForm(): boolean {
  const nextErrors: Partial<Record<ApplyField, string>> = {}
  ;(['invoice_title_id', 'order_id'] as ApplyField[]).forEach((field) => {
    const message = getApplyFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })
  applyErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 AddTitle 交互逻辑。
async function handleAddTitle() {
  if (!validateTitleForm()) {
    showToast(Object.values(titleErrors.value).find(Boolean) || '请检查抬头信息', 'warning')
    return
  }

  addingTitle.value = true
  try {
    const res = await userInvoiceApi.createTitle(titleForm.value)
    if (res.code === 0 && res.data) {
      titles.value.push(res.data)
      showToast('发票抬头已保存', 'success')
      showAddModal.value = false
      titleForm.value = { invoice_type: 'personal', title: '', tax_no: '', email: '' }
      titleErrors.value = {}
    } else {
      titleErrors.value = {
        ...titleErrors.value,
        ...extractApiFieldErrors(res, {
          email: '邮箱',
          tax_no: '税号',
          title: '抬头名称',
        }),
      }
      showToast(extractApiError(res, '保存失败，请检查填写内容'), 'error')
    }
  } catch {
    showToast('保存失败，请稍后重试', 'error')
  } finally {
    addingTitle.value = false
  }
}

// 处理 Apply 交互逻辑。
async function handleApply() {
  if (!validateApplyForm()) {
    showToast(Object.values(applyErrors.value).find(Boolean) || '请检查开票信息', 'warning')
    return
  }

  applying.value = true
  try {
    const res = await userInvoiceApi.apply(applyForm.value)
    if (res.code === 0) {
      showToast('申请已提交', 'success')
      applyForm.value = { order_id: 0, invoice_title_id: 0 }
      applyErrors.value = {}
    } else {
      applyErrors.value = {
        ...applyErrors.value,
        ...extractApiFieldErrors(res, {
          invoice_title_id: '发票抬头',
          order_id: '订单',
        }),
      }
      showToast(extractApiError(res, '申请失败，请稍后重试'), 'error')
    }
  } catch {
    showToast('申请失败，请稍后重试', 'error')
  } finally {
    applying.value = false
  }
}

const showEditModal = ref(false)
const editingTitle = ref(false)
const editTitleForm = reactive({ title_id: 0, invoice_type: 'personal', title: '', tax_no: '', email: '' })
const editTitleErrors = ref<Partial<Record<TitleField, string>>>({})

function clearEditTitleError(field: TitleField) {
  if (editTitleErrors.value[field]) {
    editTitleErrors.value = { ...editTitleErrors.value, [field]: undefined }
  }
}

function handleEditTaxNoInput() {
  editTitleForm.tax_no = editTitleForm.tax_no.replace(/\s/g, '').toUpperCase()
  clearEditTitleError('tax_no')
}

function getEditTitleFieldError(field: TitleField): string {
  switch (field) {
    case 'title':
      if (!editTitleForm.title.trim()) return '请输入抬头名称'
      return editTitleForm.title.trim().length > 100 ? '抬头名称不能超过 100 个字符' : ''
    case 'tax_no':
      if (editTitleForm.invoice_type !== 'company') return ''
      if (!editTitleForm.tax_no.trim()) return '企业抬头请填写税号'
      return isValidTaxNumber(editTitleForm.tax_no) ? '' : '税号格式不正确，请检查后重试'
    case 'email':
      if (!editTitleForm.email.trim()) return '请输入接收邮箱'
      return isValidEmailAddress(editTitleForm.email) ? '' : '邮箱格式不正确'
    default:
      return ''
  }
}

function validateEditTitleField(field: TitleField) {
  editTitleErrors.value = {
    ...editTitleErrors.value,
    [field]: getEditTitleFieldError(field) || undefined,
  }
}

function validateEditTitleForm(): boolean {
  const nextErrors: Partial<Record<TitleField, string>> = {}
  editTitleForm.title = editTitleForm.title.trim()
  editTitleForm.email = editTitleForm.email.trim()
  editTitleForm.tax_no = editTitleForm.tax_no.trim().toUpperCase()

  ;(['title', 'tax_no', 'email'] as TitleField[]).forEach((field) => {
    const message = getEditTitleFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  editTitleErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

function openEditTitle(t: any) {
  editTitleForm.title_id = t.id
  editTitleForm.invoice_type = t.type === 'company' ? 'company' : 'personal'
  editTitleForm.title = t.title || ''
  editTitleForm.tax_no = t.tax_no || ''
  editTitleForm.email = t.email || ''
  editTitleErrors.value = {}
  showEditModal.value = true
}

async function handleEditTitle() {
  if (!validateEditTitleForm()) {
    showToast(Object.values(editTitleErrors.value).find(Boolean) || '请检查抬头信息', 'warning')
    return
  }
  editingTitle.value = true
  try {
    const res = await userInvoiceApi.updateTitle(editTitleForm)
    if (res.code === 0) {
      showToast('发票抬头已更新', 'success')
      showEditModal.value = false
      const listRes = await userInvoiceApi.list()
      if (listRes.code === 0 && listRes.data) {
        titles.value = (listRes.data as any).titles || []
      }
    } else {
      showToast(res.message || '更新失败', 'error')
    }
  } catch {
    showToast('更新失败，请重试', 'error')
  } finally {
    editingTitle.value = false
  }
}

async function handleDeleteTitle(t: any) {
  if (!await confirmDialog(`确定删除抬头「${t.title}」？`, { type: 'danger' })) return
  try {
    const res = await userInvoiceApi.deleteTitle(t.id)
    if (res.code === 0) {
      showToast('发票抬头已删除', 'success')
      titles.value = titles.value.filter((item: any) => item.id !== t.id)
    } else {
      showToast(res.message || '删除失败', 'error')
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  }
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
  } finally {
    pageLoading.value = false
  }
})
</script>

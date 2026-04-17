<template>
  <section>
    <PageHeader title="价格库存管理" subtitle="按房型管理每日价格与库存" />

    <div class="mb-4 flex flex-wrap gap-3">
      <SelectField v-model="selectedRoomType" size="sm" @change="loadCalendar">
        <option value="">选择房型</option>
        <option v-for="rt in roomTypes" :key="rt.id" :value="rt.id">{{ rt.hotel_name }} - {{ rt.name }}</option>
      </SelectField>
      <input v-model="startDate" type="date" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
      <input v-model="endDate" type="date" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
      <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="loadCalendar">查询</button>
    </div>

    <div v-if="!selectedRoomType" class="rounded-2xl bg-white p-16 text-center shadow-sm ring-1 ring-slate-200">
      <p class="text-slate-400">请先选择房型</p>
    </div>

    <div v-else class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="calColumns" :rows="calendarData" :loading="loading">
        <template #col-price="{ value }">¥{{ formatMoney(value as number) }}</template>
        <template #col-status="{ value }">
          <StatusBadge :label="ROOM_STATUS_MAP[value as string]?.label || String(value)" :type="value === 'available' ? 'success' : 'default'" />
        </template>
        <template #actions="{ row }">
          <button class="text-sm text-teal-600 hover:underline" @click="openEdit(row)">编辑</button>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadCalendar() }" />
    </div>

    <ModalDialog :visible="showModal" title="编辑价格库存" size="sm" @close="showModal = false">
      <form class="space-y-4" @submit.prevent="handleSave">
        <div>
          <label class="mb-1 block text-sm font-medium">日期</label>
          <input :value="editForm.date" disabled class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">价格</label>
          <input
            v-model.number="editForm.price"
            type="number"
            step="0.01"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none"
            :class="formErrors.price ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-slate-300 focus:border-teal-500'"
            @blur="validateField('price')"
          />
          <p v-if="formErrors.price" class="mt-1 text-xs text-red-500">{{ formErrors.price }}</p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">库存</label>
          <input
            v-model.number="editForm.stock"
            type="number"
            min="0"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none"
            :class="formErrors.stock ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-slate-300 focus:border-teal-500'"
            @blur="validateField('stock')"
          />
          <p v-if="formErrors.stock" class="mt-1 text-xs text-red-500">{{ formErrors.stock }}</p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">状态</label>
          <SelectField v-model="editForm.status" class="w-full">
            <option value="available">可售</option>
            <option value="offline">不可售</option>
          </SelectField>
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showModal = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving" @click="handleSave">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </ModalDialog>

  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { inventoryApi, roomTypeApi } from '@hotelink/api'
import { formatMoney, formatDate, ROOM_STATUS_MAP, extractApiError } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, useToast, SelectField } from '@hotelink/ui'

const { showToast } = useToast()

const calColumns = [
  { key: 'date', label: '日期' },
  { key: 'price', label: '价格' },
  { key: 'stock', label: '库存' },
  { key: 'status', label: '状态' },
]

const roomTypes = ref<{ id: number; name: string; hotel_name: string }[]>([])
const selectedRoomType = ref('')
const calendarData = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(31)
const total = ref(0)

const today = new Date()
const startDate = ref(formatDate(today))
const endDateD = new Date(today); endDateD.setDate(endDateD.getDate() + 30)
const endDate = ref(formatDate(endDateD))

const showModal = ref(false)
const saving = ref(false)
type InventoryField = 'price' | 'stock'
const formErrors = ref<Partial<Record<InventoryField, string>>>({})
const editForm = reactive({ date: '', price: 0, stock: 0, status: 'available' })

function patchCalendarRow(date: string, patch: Record<string, unknown>) {
  calendarData.value = calendarData.value.map((item) => (String(item.date) === date ? { ...item, ...patch } : item))
}

function getFieldError(field: InventoryField): string {
  switch (field) {
    case 'price':
      if (!Number.isFinite(Number(editForm.price)) || Number(editForm.price) < 0) return '价格不能小于 0'
      return ''
    case 'stock':
      if (!Number.isFinite(Number(editForm.stock)) || Number(editForm.stock) < 0) return '库存不能小于 0'
      return ''
    default:
      return ''
  }
}

function validateField(field: InventoryField) {
  const message = getFieldError(field)
  formErrors.value = {
    ...formErrors.value,
    [field]: message || undefined,
  }
}

function validateForm(): boolean {
  const nextErrors: Partial<Record<InventoryField, string>> = {}
  ;(['price', 'stock'] as InventoryField[]).forEach((field) => {
    const message = getFieldError(field)
    if (message) nextErrors[field] = message
  })
  formErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 加载 RoomTypes 相关数据。
async function loadRoomTypes() {
  try {
    const res = await roomTypeApi.list({ page_size: 200 })
    if (res.code === 0 && res.data) {
      roomTypes.value = ((res.data as unknown as { items: Record<string, unknown>[] }).items || []).map(
        (rt) => ({ id: rt.id as number, name: rt.name as string, hotel_name: (rt.hotel_name as string) || '' })
      )
    }
  } catch {
    showToast('加载房型列表失败', 'error')
  }
}

// 加载 Calendar 相关数据。
async function loadCalendar() {
  if (!selectedRoomType.value) {
    showToast('请先选择房型', 'warning')
    return
  }
  if (startDate.value && endDate.value && startDate.value > endDate.value) {
    showToast('开始日期不能晚于结束日期', 'warning')
    return
  }
  loading.value = true
  try {
    const res = await inventoryApi.calendar({
      room_type_id: selectedRoomType.value,
      start_date: startDate.value,
      end_date: endDate.value,
      page: page.value,
      page_size: pageSize.value,
    })
    if (res.code === 0 && res.data) {
      calendarData.value = (res.data as unknown as { items: Record<string, unknown>[] }).items || []
      total.value = (res.data as unknown as { total: number }).total || 0
    } else {
      showToast(res.message || '加载库存数据失败', 'error')
    }
  } catch {
    showToast('加载库存数据失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

// 打开 Edit 相关界面。
function openEdit(row: Record<string, unknown>) {
  editForm.date = row.date as string
  editForm.price = row.price as number
  editForm.stock = row.stock as number
  editForm.status = (row.status as string) || 'available'
  formErrors.value = {}
  showModal.value = true
}

// 处理 Save 交互逻辑。
async function handleSave() {
  if (!validateForm()) {
    showToast(Object.values(formErrors.value).find(Boolean) || '请先完善库存信息', 'warning')
    return
  }

  saving.value = true
  try {
    const res = await inventoryApi.update({
      room_type_id: Number(selectedRoomType.value),
      date: editForm.date,
      price: editForm.price,
      stock: editForm.stock,
      status: editForm.status,
    })
    if (res.code === 0) {
      showToast('库存更新成功', 'success')
      showModal.value = false
      patchCalendarRow(editForm.date, {
        price: editForm.price,
        stock: editForm.stock,
        status: editForm.status,
      })
    } else {
      showToast(extractApiError(res, '库存更新失败'), 'error')
    }
  } catch {
    showToast('库存更新失败，请重试', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(loadRoomTypes)
</script>

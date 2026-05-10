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
      <button class="rounded-lg border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-medium text-teal-700 hover:bg-teal-100" @click="openBulkModal">批量设置</button>
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

    <ModalDialog :visible="showBulkModal" title="批量设置价格库存" size="lg" @close="showBulkModal = false">
      <form class="space-y-5" @submit.prevent="handleBulkSave">
        <div>
          <div class="mb-2 flex items-center justify-between">
            <label class="block text-sm font-medium text-slate-700">适用房型</label>
            <span class="text-xs text-slate-400">已选 {{ bulkForm.roomTypeIds.length }} 个房型</span>
          </div>
          <div class="grid max-h-44 gap-2 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50/60 p-3 sm:grid-cols-2">
            <label
              v-for="rt in roomTypes"
              :key="rt.id"
              class="flex cursor-pointer items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm text-slate-600 ring-1 ring-slate-100 transition hover:ring-teal-200"
            >
              <input
                type="checkbox"
                :checked="bulkForm.roomTypeIds.includes(rt.id)"
                class="h-4 w-4 rounded border-slate-300 text-teal-600"
                @change="toggleBulkRoomType(rt.id)"
              />
              <span class="min-w-0 flex-1 truncate">{{ rt.hotel_name }} - {{ rt.name }}</span>
            </label>
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">开始日期</label>
            <input v-model="bulkForm.startDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">结束日期</label>
            <input v-model="bulkForm.endDate" type="date" class="input-field" />
          </div>
        </div>

        <div>
          <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
            <label class="block text-sm font-medium text-slate-700">适用星期</label>
            <div class="flex gap-2 text-xs">
              <button type="button" class="rounded-full bg-slate-100 px-2.5 py-1 text-slate-500 hover:bg-slate-200" @click="setBulkWeekdays([0, 1, 2, 3, 4, 5, 6])">每天</button>
              <button type="button" class="rounded-full bg-slate-100 px-2.5 py-1 text-slate-500 hover:bg-slate-200" @click="setBulkWeekdays([0, 1, 2, 3, 4])">工作日</button>
              <button type="button" class="rounded-full bg-slate-100 px-2.5 py-1 text-slate-500 hover:bg-slate-200" @click="setBulkWeekdays([5, 6])">周末</button>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <label
              v-for="day in WEEKDAY_OPTIONS"
              :key="day.value"
              class="inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs transition"
              :class="bulkForm.weekdays.includes(day.value) ? 'border-teal-200 bg-teal-50 text-teal-700' : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300'"
            >
              <input
                type="checkbox"
                :checked="bulkForm.weekdays.includes(day.value)"
                class="sr-only"
                @change="toggleBulkWeekday(day.value)"
              />
              {{ day.label }}
            </label>
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">统一价格</label>
            <input v-model="bulkForm.price" type="number" min="0" step="0.01" placeholder="不改价格可留空" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">周末价格</label>
            <input v-model="bulkForm.weekendPrice" type="number" min="0" step="0.01" placeholder="周六/周日覆盖" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">库存</label>
            <input v-model="bulkForm.stock" type="number" min="0" step="1" placeholder="不改库存可留空" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">状态</label>
            <SelectField v-model="bulkForm.status" class="w-full">
              <option value="">不修改</option>
              <option value="available">可售</option>
              <option value="offline">不可售</option>
            </SelectField>
          </div>
        </div>

        <div class="rounded-xl bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-500">
          将影响 {{ bulkPreview.dateCount }} 个自然日范围内的目标日期；后端会按房型默认值补齐新建库存记录，并为本次批量操作写入审计日志。
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showBulkModal = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="bulkSaving" @click="handleBulkSave">
          {{ bulkSaving ? '批量保存中…' : '确认批量设置' }}
        </button>
      </template>
    </ModalDialog>

  </section>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue'
import { inventoryApi, roomTypeApi } from '@hotelink/api'
import { formatMoney, formatDate, ROOM_STATUS_MAP, extractApiError } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, useToast, SelectField } from '@hotelink/ui'
import {
  buildInclusiveDateList,
  normalizeInventoryBulkWeekdays,
  validateInventoryBulkDraft,
} from '../utils/inventory-bulk'

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
const showBulkModal = ref(false)
const bulkSaving = ref(false)
type InventoryField = 'price' | 'stock'
const formErrors = ref<Partial<Record<InventoryField, string>>>({})
const editForm = reactive({ date: '', price: 0, stock: 0, status: 'available' })
const bulkForm = reactive({
  roomTypeIds: [] as number[],
  startDate: startDate.value,
  endDate: endDate.value,
  price: '',
  weekendPrice: '',
  stock: '',
  status: '',
  weekdays: [0, 1, 2, 3, 4, 5, 6] as number[],
})
const WEEKDAY_OPTIONS = [
  { value: 0, label: '周一' },
  { value: 1, label: '周二' },
  { value: 2, label: '周三' },
  { value: 3, label: '周四' },
  { value: 4, label: '周五' },
  { value: 5, label: '周六' },
  { value: 6, label: '周日' },
]

const bulkPreview = computed(() => ({
  dateCount: buildInclusiveDateList(bulkForm.startDate, bulkForm.endDate).length,
}))

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

function openBulkModal() {
  bulkForm.roomTypeIds = selectedRoomType.value ? [Number(selectedRoomType.value)] : []
  bulkForm.startDate = startDate.value
  bulkForm.endDate = endDate.value
  bulkForm.price = ''
  bulkForm.weekendPrice = ''
  bulkForm.stock = ''
  bulkForm.status = ''
  bulkForm.weekdays = [0, 1, 2, 3, 4, 5, 6]
  showBulkModal.value = true
}

function toggleBulkRoomType(roomTypeId: number) {
  bulkForm.roomTypeIds = bulkForm.roomTypeIds.includes(roomTypeId)
    ? bulkForm.roomTypeIds.filter(item => item !== roomTypeId)
    : [...bulkForm.roomTypeIds, roomTypeId]
}

function toggleBulkWeekday(weekday: number) {
  bulkForm.weekdays = bulkForm.weekdays.includes(weekday)
    ? bulkForm.weekdays.filter(item => item !== weekday)
    : normalizeInventoryBulkWeekdays([...bulkForm.weekdays, weekday])
}

function setBulkWeekdays(weekdays: number[]) {
  bulkForm.weekdays = normalizeInventoryBulkWeekdays(weekdays)
}

async function handleBulkSave() {
  const validation = validateInventoryBulkDraft(bulkForm)
  if (!validation.valid) {
    showToast(validation.message, 'warning')
    return
  }

  bulkSaving.value = true
  try {
    const payload = {
      room_type_ids: bulkForm.roomTypeIds,
      start_date: bulkForm.startDate,
      end_date: bulkForm.endDate,
      weekdays: normalizeInventoryBulkWeekdays(bulkForm.weekdays),
      ...(bulkForm.price !== '' ? { price: bulkForm.price } : {}),
      ...(bulkForm.weekendPrice !== '' ? { weekend_price: bulkForm.weekendPrice } : {}),
      ...(bulkForm.stock !== '' ? { stock: Number(bulkForm.stock) } : {}),
      ...(bulkForm.status ? { status: bulkForm.status } : {}),
    }
    // Backend owns the final inventory write and audit log creation.
    const res = await inventoryApi.bulkUpdate(payload)
    if (res.code === 0) {
      const data = res.data || { created_count: 0, updated_count: 0, skipped_count: 0 }
      showToast(`批量设置完成：新建 ${data.created_count} 条，更新 ${data.updated_count} 条，跳过 ${data.skipped_count} 条`, 'success')
      showBulkModal.value = false
      if (selectedRoomType.value) await loadCalendar()
    } else {
      showToast(extractApiError(res, '批量设置失败'), 'error')
    }
  } catch {
    showToast('批量设置失败，请检查网络后重试', 'error')
  } finally {
    bulkSaving.value = false
  }
}

onMounted(loadRoomTypes)
</script>

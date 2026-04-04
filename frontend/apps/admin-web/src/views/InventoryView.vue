<template>
  <section>
    <PageHeader title="价格库存管理" subtitle="按房型管理每日价格与库存" />

    <div class="mb-4 flex flex-wrap gap-3">
      <select v-model="selectedRoomType" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" @change="loadCalendar">
        <option value="">选择房型</option>
        <option v-for="rt in roomTypes" :key="rt.id" :value="rt.id">{{ rt.hotel_name }} - {{ rt.name }}</option>
      </select>
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
          <input v-model.number="editForm.price" type="number" step="0.01" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">库存</label>
          <input v-model.number="editForm.stock" type="number" min="0" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">状态</label>
          <select v-model="editForm.status" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="available">可售</option>
            <option value="offline">不可售</option>
          </select>
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
import { formatMoney, formatDate, ROOM_STATUS_MAP } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination } from '@hotelink/ui'

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
const editForm = reactive({ date: '', price: 0, stock: 0, status: 'available' })

async function loadRoomTypes() {
  const res = await roomTypeApi.list({ page_size: 200 })
  if (res.code === 0 && res.data) {
    roomTypes.value = ((res.data as unknown as { items: Record<string, unknown>[] }).items || []).map(
      (rt) => ({ id: rt.id as number, name: rt.name as string, hotel_name: (rt.hotel_name as string) || '' })
    )
  }
}

async function loadCalendar() {
  if (!selectedRoomType.value) return
  loading.value = true
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
  }
  loading.value = false
}

function openEdit(row: Record<string, unknown>) {
  editForm.date = row.date as string
  editForm.price = row.price as number
  editForm.stock = row.stock as number
  editForm.status = (row.status as string) || 'available'
  showModal.value = true
}

async function handleSave() {
  saving.value = true
  try {
    await inventoryApi.update({
      room_type_id: Number(selectedRoomType.value),
      date: editForm.date,
      price: editForm.price,
      stock: editForm.stock,
      status: editForm.status,
    })
    showModal.value = false
    loadCalendar()
  } finally {
    saving.value = false
  }
}

onMounted(loadRoomTypes)
</script>

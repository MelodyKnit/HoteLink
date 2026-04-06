<template>
  <section>
    <PageHeader title="房型管理" subtitle="管理房型信息、价格与上下架状态">
      <template #actions>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreate">新增房型</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-3">
      <select v-model="filters.hotel_id" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" @change="loadList">
        <option value="">全部酒店</option>
        <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
      </select>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">刷新</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-bed_type="{ value }">{{ BED_TYPE_MAP[value as string] || value }}</template>
        <template #col-base_price="{ value }">¥{{ formatMoney(value as number) }}</template>
        <template #col-status="{ value }">
          <StatusBadge :label="value === 'online' ? '上架' : '下架'" :type="value === 'online' ? 'success' : 'default'" />
        </template>
        <template #actions="{ row }">
          <div class="flex gap-2">
            <button class="text-sm text-teal-600 hover:underline" @click="openEdit(row)">编辑</button>
            <button class="text-sm text-red-600 hover:underline" @click="handleDelete(row)">删除</button>
          </div>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <ModalDialog :visible="showModal" :title="editingId ? '编辑房型' : '新增房型'" size="lg" @close="showModal = false">
      <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="handleSave">
        <div class="sm:col-span-2">
          <label class="mb-1 block text-sm font-medium">房型名称</label>
          <input v-model="form.name" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">所属酒店</label>
          <select v-model="form.hotel_id" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">床型</label>
          <select v-model="form.bed_type" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="single">单人床</option>
            <option value="double">双人床</option>
            <option value="queen">大床</option>
            <option value="twin">双床</option>
            <option value="family">家庭床</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">面积 (㎡)</label>
          <input v-model.number="form.area" type="number" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">基础价格</label>
          <input v-model.number="form.base_price" type="number" step="0.01" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">早餐份数</label>
          <input v-model.number="form.breakfast_count" type="number" min="0" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">最大入住人数</label>
          <input v-model.number="form.max_guest_count" type="number" min="1" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">状态</label>
          <select v-model="form.status" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="online">上架</option>
            <option value="offline">下架</option>
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
import { roomTypeApi, hotelApi } from '@hotelink/api'
import { formatMoney, BED_TYPE_MAP } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination } from '@hotelink/ui'

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: '房型名称' },
  { key: 'hotel_name', label: '所属酒店' },
  { key: 'bed_type', label: '床型' },
  { key: 'area', label: '面积' },
  { key: 'base_price', label: '基础价格' },
  { key: 'max_guest_count', label: '最大入住' },
  { key: 'status', label: '状态' },
]

const list = ref<Record<string, unknown>[]>([])
const hotels = ref<{ id: number; name: string }[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ hotel_id: '' })

const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  name: '', hotel_id: 0, bed_type: 'queen', area: 30, base_price: 399,
  breakfast_count: 0, max_guest_count: 2, status: 'online',
})

// 重置 Form 状态。
function resetForm() {
  form.name = ''; form.hotel_id = hotels.value[0]?.id || 0; form.bed_type = 'queen'
  form.area = 30; form.base_price = 399; form.breakfast_count = 0
  form.max_guest_count = 2; form.status = 'online'
  editingId.value = null
}

// 打开 Create 相关界面。
function openCreate() { resetForm(); showModal.value = true }

// 打开 Edit 相关界面。
function openEdit(row: Record<string, unknown>) {
  editingId.value = row.id as number
  form.name = (row.name as string) || ''
  form.hotel_id = (row.hotel as number) || (row.hotel_id as number) || 0
  form.bed_type = (row.bed_type as string) || 'queen'
  form.area = (row.area as number) || 30
  form.base_price = (row.base_price as number) || 399
  form.breakfast_count = (row.breakfast_count as number) || 0
  form.max_guest_count = (row.max_guest_count as number) || 2
  form.status = (row.status as string) || 'online'
  showModal.value = true
}

// 加载 Hotels 相关数据。
async function loadHotels() {
  const res = await hotelApi.list({ page_size: 100 })
  if (res.code === 0 && res.data) {
    hotels.value = ((res.data as unknown as { items: Record<string, unknown>[] }).items || []).map(
      (h) => ({ id: h.id as number, name: h.name as string })
    )
  }
}

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
  if (filters.hotel_id) params.hotel_id = filters.hotel_id
  const res = await roomTypeApi.list(params)
  if (res.code === 0 && res.data) {
    list.value = (res.data as unknown as { items: Record<string, unknown>[]; total: number }).items || []
    total.value = (res.data as unknown as { total: number }).total || 0
  }
  loading.value = false
}

// 处理 Save 交互逻辑。
async function handleSave() {
  saving.value = true
  try {
    if (editingId.value) {
      await roomTypeApi.update({ room_type_id: editingId.value, ...form })
    } else {
      await roomTypeApi.create({ ...form })
    }
    showModal.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

// 处理 Delete 交互逻辑。
async function handleDelete(row: Record<string, unknown>) {
  if (!confirm(`确定删除房型「${row.name}」？`)) return
  await roomTypeApi.delete(row.id as number)
  loadList()
}

onMounted(async () => {
  await loadHotels()
  loadList()
})
</script>

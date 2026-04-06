<template>
  <section>
    <PageHeader title="酒店管理" subtitle="管理酒店基本信息与上下架状态">
      <template #actions>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreate">新增酒店</button>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="mb-4 flex flex-wrap gap-3">
      <input v-model="filters.keyword" placeholder="搜索酒店名/地址" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="loadList" />
      <select v-model="filters.status" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" @change="loadList">
        <option value="">全部状态</option>
        <option value="online">已上架</option>
        <option value="offline">已下架</option>
        <option value="draft">草稿</option>
      </select>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-status="{ value }">
          <StatusBadge :label="HOTEL_STATUS_MAP[value as string] || String(value)" :type="value === 'online' ? 'success' : value === 'offline' ? 'danger' : 'default'" />
        </template>
        <template #col-star="{ value }">{{ value }}星</template>
        <template #col-min_price="{ value }">¥{{ formatMoney(value as number) }}</template>
        <template #actions="{ row }">
          <div class="flex gap-2">
            <button class="text-sm text-teal-600 hover:underline" @click="openEdit(row)">编辑</button>
            <button class="text-sm text-red-600 hover:underline" @click="handleDelete(row)">删除</button>
          </div>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <!-- Create/Edit Modal -->
    <ModalDialog :visible="showModal" :title="editingId ? '编辑酒店' : '新增酒店'" @close="showModal = false">
      <form class="space-y-4" @submit.prevent="handleSave">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">酒店名称</label>
          <input v-model="form.name" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">城市</label>
            <input v-model="form.city" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">星级</label>
            <select v-model="form.star" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option :value="2">二星</option>
              <option :value="3">三星</option>
              <option :value="4">四星</option>
              <option :value="5">五星</option>
            </select>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">地址</label>
          <input v-model="form.address" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">联系电话</label>
          <input v-model="form.phone" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">描述</label>
          <textarea v-model="form.description" rows="3" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">状态</label>
          <select v-model="form.status" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="draft">草稿</option>
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
import { hotelApi } from '@hotelink/api'
import { formatMoney, HOTEL_STATUS_MAP } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination } from '@hotelink/ui'

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: '酒店名称' },
  { key: 'city', label: '城市' },
  { key: 'star', label: '星级' },
  { key: 'min_price', label: '起价' },
  { key: 'status', label: '状态' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ keyword: '', status: '' })

const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  name: '', city: '', address: '', star: 4, phone: '', description: '', status: 'draft',
})

// 重置 Form 状态。
function resetForm() {
  form.name = ''; form.city = ''; form.address = ''; form.star = 4
  form.phone = ''; form.description = ''; form.status = 'draft'
  editingId.value = null
}

// 打开 Create 相关界面。
function openCreate() {
  resetForm()
  showModal.value = true
}

// 打开 Edit 相关界面。
function openEdit(row: Record<string, unknown>) {
  editingId.value = row.id as number
  form.name = (row.name as string) || ''
  form.city = (row.city as string) || ''
  form.address = (row.address as string) || ''
  form.star = (row.star as number) || 4
  form.phone = (row.phone as string) || ''
  form.description = (row.description as string) || ''
  form.status = (row.status as string) || 'draft'
  showModal.value = true
}

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
  if (filters.keyword) params.keyword = filters.keyword
  if (filters.status) params.status = filters.status
  const res = await hotelApi.list(params)
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
      await hotelApi.update({ hotel_id: editingId.value, ...form })
    } else {
      await hotelApi.create({ ...form })
    }
    showModal.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

// 处理 Delete 交互逻辑。
async function handleDelete(row: Record<string, unknown>) {
  if (!confirm(`确定删除酒店「${row.name}」？`)) return
  await hotelApi.delete(row.id as number)
  loadList()
}

onMounted(loadList)
</script>

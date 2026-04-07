<template>
  <section>
    <PageHeader title="房型管理" subtitle="管理房型信息、价格与上下架状态">
      <template #actions>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreate">新增房型</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-3">
      <SelectField v-model="filters.hotel_id" size="sm" @change="loadList">
        <option value="">全部酒店</option>
        <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
      </SelectField>
      <SelectField v-model="filters.ordering" size="sm" @change="onSortChange">
        <option value="-id">ID 最新优先</option>
        <option value="id">ID 最旧优先</option>
        <option value="name">名称 A→Z</option>
        <option value="-name">名称 Z→A</option>
        <option value="base_price">价格从低到高</option>
        <option value="-base_price">价格从高到低</option>
        <option value="bed_type">床型排序</option>
        <option value="-bed_type">床型逆序</option>
      </SelectField>
      <SelectField v-model="thumbnailMode" size="sm">
        <option value="compact">缩略图: 小图(更流畅)</option>
        <option value="standard">缩略图: 标准</option>
        <option value="hidden">缩略图: 隐藏(极速)</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">刷新</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-image="{ value, row }">
          <img
            v-if="value && thumbnailMode !== 'hidden'"
            :src="String((row as Record<string, unknown>).image_thumb || value)"
            alt="房型图"
            loading="lazy"
            decoding="async"
            @error="onThumbError($event, String(value))"
            :width="thumbnailWidth"
            :height="thumbnailHeight"
            :class="[thumbnailClass, 'rounded object-cover']"
          />
          <span v-else class="text-xs text-slate-400">{{ thumbnailMode === 'hidden' ? '已隐藏' : '暂无' }}</span>
        </template>
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
          <SelectField v-model="form.hotel_id" required class="w-full">
            <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">床型</label>
          <SelectField v-model="form.bed_type" class="w-full">
            <option value="single">单人床</option>
            <option value="double">双人床</option>
            <option value="queen">大床</option>
            <option value="twin">双床</option>
            <option value="family">家庭床</option>
          </SelectField>
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
          <SelectField v-model="form.status" class="w-full">
            <option value="online">上架</option>
            <option value="offline">下架</option>
          </SelectField>
        </div>
        <!-- 房型主图 -->
        <div class="sm:col-span-2">
          <label class="mb-1 block text-sm font-medium">房型图片</label>
          <div class="flex items-center gap-3">
            <img v-if="form.image" :src="form.image" alt="房型图" class="h-20 w-28 rounded-lg object-cover ring-1 ring-slate-200" />
            <label class="cursor-pointer rounded-lg border-2 border-dashed border-slate-300 px-4 py-2 text-sm text-slate-500 hover:border-teal-400 hover:text-teal-600">
              {{ uploading ? '上传中…' : '选择图片' }}
              <input type="file" accept="image/*" class="hidden" :disabled="uploading" @change="handleImageUpload" />
            </label>
            <button v-if="form.image" type="button" class="text-sm text-red-500 hover:underline" @click="form.image = ''">移除</button>
          </div>
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showModal = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving" @click="handleSave">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </ModalDialog>

    <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" @close="closeToast" />
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { roomTypeApi, hotelApi, commonApi } from '@hotelink/api'
import { formatMoney, BED_TYPE_MAP, extractApiError } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, Toast, useToast, SelectField } from '@hotelink/ui'

const { toastVisible, toastMessage, toastType, showToast, closeToast } = useToast()

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'image', label: '图片' },
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
const pageSize = ref(10)
const total = ref(0)
const thumbnailMode = ref<'compact' | 'standard' | 'hidden'>('compact')
const filters = reactive({ hotel_id: '', ordering: '-id' })
const uploading = ref(false)

const thumbnailClass = computed(() => (thumbnailMode.value === 'compact' ? 'h-8 w-12' : 'h-10 w-14'))
const thumbnailWidth = computed(() => (thumbnailMode.value === 'compact' ? 48 : 56))
const thumbnailHeight = computed(() => (thumbnailMode.value === 'compact' ? 32 : 40))

const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  name: '', hotel_id: 0, bed_type: 'queen', area: 30, base_price: 399,
  breakfast_count: 0, max_guest_count: 2, status: 'online', image: '',
})

function resetForm() {
  form.name = ''; form.hotel_id = hotels.value[0]?.id || 0; form.bed_type = 'queen'
  form.area = 30; form.base_price = 399; form.breakfast_count = 0
  form.max_guest_count = 2; form.status = 'online'; form.image = ''
  editingId.value = null
}

function onSortChange() {
  page.value = 1
  loadList()
}

function onThumbError(event: Event, fallbackSrc: string) {
  const el = event.target as HTMLImageElement
  if (!el || !fallbackSrc || el.src === fallbackSrc) return
  el.src = fallbackSrc
}

function openCreate() { resetForm(); showModal.value = true }

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
  form.image = (row.image as string) || ''
  showModal.value = true
}

async function handleImageUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const res = await commonApi.upload(file, 'room_type')
    if (res.code === 0 && res.data) {
      form.image = res.data.file_url
    } else {
      showToast(res.message || '图片上传失败', 'error')
    }
  } catch {
    showToast('图片上传失败，请重试', 'error')
  } finally {
    uploading.value = false
    ;(e.target as HTMLInputElement).value = ''
  }
}

async function loadHotels() {
  try {
    const res = await hotelApi.list({ page_size: 100 })
    if (res.code === 0 && res.data) {
      hotels.value = ((res.data as unknown as { items: Record<string, unknown>[] }).items || []).map(
        (h) => ({ id: h.id as number, name: h.name as string })
      )
    }
  } catch {
    showToast('加载酒店列表失败', 'error')
  }
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value, ordering: filters.ordering, thumb_mode: thumbnailMode.value }
    if (filters.hotel_id) params.hotel_id = filters.hotel_id
    const res = await roomTypeApi.list(params)
    if (res.code === 0 && res.data) {
      list.value = (res.data as unknown as { items: Record<string, unknown>[]; total: number }).items || []
      total.value = (res.data as unknown as { total: number }).total || 0
    } else {
      showToast(res.message || '加载房型列表失败', 'error')
    }
  } catch {
    showToast('加载房型列表失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    let res
    if (editingId.value) {
      res = await roomTypeApi.update({ room_type_id: editingId.value, ...form })
    } else {
      res = await roomTypeApi.create({ ...form })
    }
    if (res.code === 0) {
      showToast(editingId.value ? '房型更新成功' : '房型创建成功', 'success')
      showModal.value = false
      loadList()
    } else {
      showToast(extractApiError(res, '保存失败'), 'error')
    }
  } catch {
    showToast('保存失败，请重试', 'error')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  if (!confirm(`确定删除房型「${row.name}」？`)) return
  try {
    const res = await roomTypeApi.delete(row.id as number)
    if (res.code === 0) {
      showToast('房型删除成功', 'success')
      loadList()
    } else {
      showToast(extractApiError(res, '删除失败'), 'error')
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  }
}

onMounted(async () => {
  await loadHotels()
  loadList()
})
</script>

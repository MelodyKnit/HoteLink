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
        <template #col-cover_image="{ value }">
          <img v-if="value" :src="String(value)" alt="封面" class="h-10 w-14 rounded object-cover" />
          <span v-else class="text-xs text-slate-400">暂无图片</span>
        </template>
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
    <ModalDialog :visible="showModal" :title="editingId ? '编辑酒店' : '新增酒店'" size="lg" @close="showModal = false">
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
        <!-- 封面图上传 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">封面图</label>
          <div class="flex items-center gap-3">
            <img v-if="form.cover_image" :src="form.cover_image" alt="封面" class="h-20 w-28 rounded-lg object-cover ring-1 ring-slate-200" />
            <label class="cursor-pointer rounded-lg border-2 border-dashed border-slate-300 px-4 py-2 text-sm text-slate-500 hover:border-teal-400 hover:text-teal-600">
              {{ uploading ? '上传中…' : '选择图片' }}
              <input type="file" accept="image/*" class="hidden" :disabled="uploading" @change="handleCoverUpload" />
            </label>
          </div>
        </div>
        <!-- 酒店图集 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">酒店图集</label>
          <div class="flex flex-wrap gap-2">
            <div v-for="(img, idx) in form.images" :key="idx" class="group relative">
              <img :src="img" alt="图片" class="h-20 w-28 rounded-lg object-cover ring-1 ring-slate-200" />
              <button type="button" class="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white opacity-0 group-hover:opacity-100" @click="removeImage(idx)">×</button>
            </div>
            <label class="flex h-20 w-28 cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-slate-300 text-slate-400 hover:border-teal-400 hover:text-teal-600">
              <span class="text-2xl">+</span>
              <input type="file" accept="image/*" class="hidden" :disabled="uploading" @change="handleGalleryUpload" />
            </label>
          </div>
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

    <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" @close="closeToast" />
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { hotelApi, commonApi } from '@hotelink/api'
import { formatMoney, HOTEL_STATUS_MAP } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, Toast, useToast } from '@hotelink/ui'

const { toastVisible, toastMessage, toastType, showToast, closeToast } = useToast()

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'cover_image', label: '封面' },
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
const uploading = ref(false)

const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  name: '', city: '', address: '', star: 4, phone: '', description: '',
  cover_image: '', images: [] as string[], status: 'draft',
})

function resetForm() {
  form.name = ''; form.city = ''; form.address = ''; form.star = 4
  form.phone = ''; form.description = ''; form.status = 'draft'
  form.cover_image = ''; form.images = []
  editingId.value = null
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = row.id as number
  form.name = (row.name as string) || ''
  form.city = (row.city as string) || ''
  form.address = (row.address as string) || ''
  form.star = (row.star as number) || 4
  form.phone = (row.phone as string) || ''
  form.description = (row.description as string) || ''
  form.status = (row.status as string) || 'draft'
  form.cover_image = (row.cover_image as string) || ''
  form.images = Array.isArray(row.images) ? [...(row.images as string[])] : []
  showModal.value = true
}

async function uploadFile(file: File, scene: string): Promise<string | null> {
  uploading.value = true
  try {
    const res = await commonApi.upload(file, scene)
    if (res.code === 0 && res.data) {
      return res.data.file_url
    }
    showToast(res.message || '图片上传失败', 'error')
    return null
  } catch {
    showToast('图片上传失败，请重试', 'error')
    return null
  } finally {
    uploading.value = false
  }
}

async function handleCoverUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const url = await uploadFile(file, 'hotel')
  if (url) form.cover_image = url
  ;(e.target as HTMLInputElement).value = ''
}

async function handleGalleryUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const url = await uploadFile(file, 'hotel')
  if (url) form.images.push(url)
  ;(e.target as HTMLInputElement).value = ''
}

function removeImage(idx: number) {
  form.images.splice(idx, 1)
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    const res = await hotelApi.list(params)
    if (res.code === 0 && res.data) {
      list.value = (res.data as unknown as { items: Record<string, unknown>[]; total: number }).items || []
      total.value = (res.data as unknown as { total: number }).total || 0
    } else {
      showToast(res.message || '加载酒店列表失败', 'error')
    }
  } catch {
    showToast('加载酒店列表失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const payload: Record<string, unknown> = { ...form }
    let res
    if (editingId.value) {
      res = await hotelApi.update({ hotel_id: editingId.value, ...payload })
    } else {
      res = await hotelApi.create(payload)
    }
    if (res.code === 0) {
      showToast(editingId.value ? '酒店更新成功' : '酒店创建成功', 'success')
      showModal.value = false
      loadList()
    } else {
      showToast(res.message || '保存失败', 'error')
    }
  } catch {
    showToast('保存失败，请重试', 'error')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  if (!confirm(`确定删除酒店「${row.name}」？`)) return
  try {
    const res = await hotelApi.delete(row.id as number)
    if (res.code === 0) {
      showToast('酒店删除成功', 'success')
      loadList()
    } else {
      showToast(res.message || '删除失败', 'error')
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  }
}

onMounted(loadList)
</script>

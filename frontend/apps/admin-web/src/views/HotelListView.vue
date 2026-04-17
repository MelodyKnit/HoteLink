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
      <SelectField v-model="filters.status" size="sm" @change="loadList">
        <option value="">全部状态</option>
        <option value="online">已上架</option>
        <option value="offline">已下架</option>
        <option value="draft">草稿</option>
      </SelectField>
      <SelectField v-model="filters.type" size="sm" @change="loadList">
        <option value="">全部类型</option>
        <option value="hotel">酒店</option>
        <option value="homestay">民宿</option>
        <option value="short_rent">短租</option>
      </SelectField>
      <SelectField v-model="filters.ordering" size="sm" @change="onSortChange">
        <option value="-id">ID 最新优先</option>
        <option value="id">ID 最旧优先</option>
        <option value="name">名称 A→Z</option>
        <option value="-name">名称 Z→A</option>
        <option value="star">星级从低到高</option>
        <option value="-star">星级从高到低</option>
        <option value="min_price">价格从低到高</option>
        <option value="-min_price">价格从高到低</option>
      </SelectField>
      <SelectField v-model="thumbnailMode" size="sm">
        <option value="compact">缩略图: 小图(更流畅)</option>
        <option value="standard">缩略图: 标准</option>
        <option value="hidden">缩略图: 隐藏(极速)</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <!-- Table -->
    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable
        :columns="columns"
        :rows="list"
        :loading="loading"
        :sort-value="filters.ordering"
        @sort-change="onTableSortChange"
      >
        <template #col-cover_image="{ value, row }">
          <img
            v-if="value && thumbnailMode !== 'hidden'"
            :src="String((row as Record<string, unknown>).cover_thumb || value)"
            alt="封面"
            loading="lazy"
            decoding="async"
            @error="onThumbError($event, String(value))"
            :width="thumbnailWidth"
            :height="thumbnailHeight"
            :class="[thumbnailClass, 'rounded object-cover']"
          />
          <span v-else class="text-xs text-slate-400">{{ thumbnailMode === 'hidden' ? '已隐藏' : '暂无图片' }}</span>
        </template>
        <template #col-status="{ value }">
          <StatusBadge :label="HOTEL_STATUS_MAP[value as string] || String(value)" :type="value === 'online' ? 'success' : value === 'offline' ? 'danger' : 'default'" />
        </template>
        <template #col-type="{ value }">
          <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" :class="value === 'hotel' ? 'bg-blue-100 text-blue-700' : value === 'homestay' ? 'bg-amber-100 text-amber-700' : 'bg-purple-100 text-purple-700'">
            {{ HOTEL_TYPE_MAP[value as string] || String(value) }}
          </span>
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
          <input
            v-model="form.name"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none"
            :class="formErrors.name ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-slate-300 focus:border-teal-500'"
            @blur="validateField('name')"
          />
          <p v-if="formErrors.name" class="mt-1 text-xs text-red-500">{{ formErrors.name }}</p>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">类型</label>
            <SelectField v-model="form.type" class="w-full">
              <option value="hotel">酒店</option>
              <option value="homestay">民宿</option>
              <option value="short_rent">短租</option>
            </SelectField>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">城市</label>
            <input
              v-model="form.city"
              class="w-full rounded-lg border px-3 py-2 text-sm outline-none"
              :class="formErrors.city ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-slate-300 focus:border-teal-500'"
              @blur="validateField('city')"
            />
            <p v-if="formErrors.city" class="mt-1 text-xs text-red-500">{{ formErrors.city }}</p>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">星级</label>
            <SelectField v-model="form.star" class="w-full">
              <option :value="2">二星</option>
              <option :value="3">三星</option>
              <option :value="4">四星</option>
              <option :value="5">五星</option>
            </SelectField>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">地址</label>
          <input
            v-model="form.address"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none"
            :class="formErrors.address ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-slate-300 focus:border-teal-500'"
            @blur="validateField('address')"
          />
          <p v-if="formErrors.address" class="mt-1 text-xs text-red-500">{{ formErrors.address }}</p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">联系电话</label>
          <input
            v-model="form.phone"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none"
            :class="formErrors.phone ? 'border-red-400 bg-red-50/60 focus:border-red-500' : 'border-slate-300 focus:border-teal-500'"
            @blur="validateField('phone')"
          />
          <p v-if="formErrors.phone" class="mt-1 text-xs text-red-500">{{ formErrors.phone }}</p>
          <p v-else class="mt-1 text-xs text-slate-400">选填，支持手机号或座机号</p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">描述</label>
          <textarea v-model="form.description" rows="3" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <!-- 封面图上传 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">封面图</label>
          <div class="flex items-center gap-3">
            <img v-if="form.cover_image" :src="buildImageThumbUrl(form.cover_image, 224, 160)" alt="封面" class="h-20 w-28 rounded-lg object-cover ring-1 ring-slate-200" loading="lazy" decoding="async" />
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
              <img :src="buildImageThumbUrl(img, 224, 160)" alt="图片" class="h-20 w-28 rounded-lg object-cover ring-1 ring-slate-200" loading="lazy" decoding="async" />
              <button type="button" class="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white opacity-0 group-hover:opacity-100" @click="removeImage(idx)">×</button>
            </div>
            <label class="flex h-20 w-28 cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-slate-300 text-slate-400 hover:border-teal-400 hover:text-teal-600">
              <span class="text-2xl">+</span>
              <input type="file" accept="image/*" class="hidden" :disabled="uploading" @change="handleGalleryUpload" />
            </label>
          </div>
        </div>
        <!-- 设施标签 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">设施标签</label>
          <div class="flex flex-wrap gap-2">
            <label v-for="fac in facilityOptions" :key="fac.value" class="flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors" :class="form.facilities.includes(fac.value) ? 'border-teal-500 bg-teal-50 text-teal-700' : 'border-slate-200 text-slate-600 hover:border-slate-300'">
              <input type="checkbox" :value="fac.value" v-model="form.facilities" class="hidden" />
              {{ fac.label }}
            </label>
          </div>
        </div>
        <!-- 自定义标签 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">自定义标签</label>
          <div class="flex flex-wrap items-center gap-2">
            <span v-for="(tag, idx) in form.tags" :key="idx" class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700">
              {{ tag }}
              <button type="button" class="text-slate-400 hover:text-red-500" @click="form.tags.splice(idx, 1)">×</button>
            </span>
            <input v-model="newTag" placeholder="输入标签后回车" class="rounded-lg border border-slate-300 px-2 py-1 text-xs outline-none focus:border-teal-500" @keydown.enter.prevent="addTag" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">状态</label>
          <SelectField v-model="form.status" class="w-full">
            <option value="draft">草稿</option>
            <option value="online">上架</option>
            <option value="offline">下架</option>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { hotelApi, commonApi } from '@hotelink/api'
import { buildImageThumbUrl, formatMoney, HOTEL_STATUS_MAP, HOTEL_TYPE_MAP, extractApiError, extractApiFieldErrors } from '@hotelink/utils'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, useToast, useConfirm, SelectField } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

const columns = [
  { key: 'id', label: 'ID', sortField: 'id' },
  { key: 'cover_image', label: '封面' },
  { key: 'name', label: '酒店名称', sortField: 'name' },
  { key: 'type', label: '类型', sortField: 'type' },
  { key: 'city', label: '城市', sortField: 'city' },
  { key: 'star', label: '星级', sortField: 'star' },
  { key: 'min_price', label: '起价', sortField: 'min_price' },
  { key: 'status', label: '状态' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const thumbnailMode = ref<'compact' | 'standard' | 'hidden'>('compact')
const filters = reactive({ keyword: '', status: '', type: '', ordering: '-id' })
const uploading = ref(false)

const thumbnailClass = computed(() => (thumbnailMode.value === 'compact' ? 'h-8 w-12' : 'h-10 w-14'))
const thumbnailWidth = computed(() => (thumbnailMode.value === 'compact' ? 48 : 56))
const thumbnailHeight = computed(() => (thumbnailMode.value === 'compact' ? 32 : 40))

const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
type HotelField = 'name' | 'city' | 'address' | 'phone'
const formErrors = ref<Partial<Record<HotelField, string>>>({})
const form = reactive({
  name: '', type: 'hotel' as string, city: '', address: '', star: 4, phone: '', description: '',
  cover_image: '', images: [] as string[], facilities: [] as string[], tags: [] as string[], status: 'draft',
})
const newTag = ref('')

const facilityOptions = [
  { label: 'WiFi', value: 'wifi' },
  { label: '停车场', value: 'parking' },
  { label: '泳池', value: 'pool' },
  { label: '健身房', value: 'gym' },
  { label: '餐厅', value: 'restaurant' },
  { label: '空调', value: 'air_conditioning' },
  { label: '电梯', value: 'elevator' },
  { label: '洗衣服务', value: 'laundry' },
  { label: '行李寄存', value: 'luggage_storage' },
  { label: '24小时前台', value: 'front_desk_24h' },
  { label: '接机服务', value: 'airport_shuttle' },
  { label: '会议室', value: 'meeting_room' },
  { label: '无烟房', value: 'non_smoking' },
  { label: '宠物友好', value: 'pet_friendly' },
  { label: '厨房', value: 'kitchen' },
  { label: '洗衣机', value: 'washing_machine' },
]

function resetForm() {
  form.name = ''; form.type = 'hotel'; form.city = ''; form.address = ''; form.star = 4
  form.phone = ''; form.description = ''; form.status = 'draft'
  form.cover_image = ''; form.images = []; form.facilities = []; form.tags = []
  formErrors.value = {}
  editingId.value = null
  newTag.value = ''
}

function isValidPhone(value: string): boolean {
  return /^[0-9+()\-\s]{6,30}$/.test(value)
}

function getFieldError(field: HotelField): string {
  switch (field) {
    case 'name': {
      const value = form.name.trim()
      if (!value) return '请填写酒店名称'
      if (value.length > 200) return '酒店名称不能超过 200 个字符'
      return ''
    }
    case 'city': {
      const value = form.city.trim()
      if (!value) return '请填写城市'
      if (value.length > 100) return '城市名称不能超过 100 个字符'
      return ''
    }
    case 'address': {
      const value = form.address.trim()
      if (!value) return '请填写地址'
      if (value.length > 255) return '地址不能超过 255 个字符'
      return ''
    }
    case 'phone': {
      const value = form.phone.trim()
      if (!value) return ''
      if (!isValidPhone(value)) return '请输入有效的联系电话'
      return ''
    }
    default:
      return ''
  }
}

function validateField(field: HotelField) {
  const message = getFieldError(field)
  formErrors.value = {
    ...formErrors.value,
    [field]: message || undefined,
  }
}

function validateForm(): boolean {
  form.name = form.name.trim()
  form.city = form.city.trim()
  form.address = form.address.trim()
  form.phone = form.phone.trim()

  const nextErrors: Partial<Record<HotelField, string>> = {}
  ;(['name', 'city', 'address', 'phone'] as HotelField[]).forEach((field) => {
    const message = getFieldError(field)
    if (message) nextErrors[field] = message
  })
  formErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

function onSortChange() {
  page.value = 1
  loadList()
}

function onTableSortChange(ordering: string) {
  if (filters.ordering === ordering) return
  filters.ordering = ordering
  onSortChange()
}

function onThumbError(event: Event, fallbackSrc: string) {
  const el = event.target as HTMLImageElement
  if (!el || !fallbackSrc || el.src === fallbackSrc) return
  el.src = fallbackSrc
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = row.id as number
  form.name = (row.name as string) || ''
  form.type = (row.type as string) || 'hotel'
  form.city = (row.city as string) || ''
  form.address = (row.address as string) || ''
  form.star = (row.star as number) || 4
  form.phone = (row.phone as string) || ''
  form.description = (row.description as string) || ''
  form.status = (row.status as string) || 'draft'
  form.cover_image = (row.cover_image as string) || ''
  form.images = Array.isArray(row.images) ? [...(row.images as string[])] : []
  form.facilities = Array.isArray(row.facilities) ? [...(row.facilities as string[])] : []
  form.tags = Array.isArray(row.tags) ? [...(row.tags as string[])] : []
  newTag.value = ''
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

function addTag() {
  const tag = newTag.value.trim()
  if (tag && !form.tags.includes(tag)) {
    form.tags.push(tag)
  }
  newTag.value = ''
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value, ordering: filters.ordering, thumb_mode: thumbnailMode.value }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.type) params.type = filters.type
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

function patchHotelRow(hotelId: number, patch: Record<string, unknown>) {
  list.value = list.value.map((item) => (Number(item.id) === hotelId ? { ...item, ...patch } : item))
}

function removeHotelRow(hotelId: number) {
  list.value = list.value.filter((item) => Number(item.id) !== hotelId)
  total.value = Math.max(0, total.value - 1)
}

async function handleSave() {
  if (!validateForm()) {
    showToast(Object.values(formErrors.value).find(Boolean) || '请先完善酒店信息', 'warning')
    return
  }

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
      const savedHotel = res.data as Record<string, unknown> | undefined
      if (savedHotel && typeof savedHotel === 'object' && !Array.isArray(savedHotel)) {
        if (editingId.value) {
          patchHotelRow(editingId.value, savedHotel)
        } else {
          list.value = [savedHotel, ...list.value]
          total.value += 1
        }
      } else {
        loadList()
      }
    } else {
      formErrors.value = {
        ...formErrors.value,
        ...extractApiFieldErrors(res, {
          name: '酒店名称',
          city: '城市',
          address: '地址',
          phone: '联系电话',
        }),
      }
      showToast(extractApiError(res, '保存失败，请检查填写内容', {
        name: '酒店名称',
        city: '城市',
        address: '地址',
        phone: '联系电话',
      }), 'error')
    }
  } catch {
    showToast('保存失败，请重试', 'error')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  if (!await confirmDialog(`确定删除酒店「${row.name}」？`, { type: 'danger' })) return
  try {
    const res = await hotelApi.delete(row.id as number)
    if (res.code === 0) {
      showToast('酒店删除成功', 'success')
      removeHotelRow(row.id as number)
    } else {
      showToast(extractApiError(res, '删除失败'), 'error')
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  }
}

onMounted(loadList)
</script>

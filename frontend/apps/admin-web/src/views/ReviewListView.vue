<template>
  <section>
    <PageHeader title="评价管理" subtitle="查看并回复用户评价" />

    <div class="mb-4 flex flex-wrap gap-3">
      <select v-model="hotelId" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" @change="loadList">
        <option value="">全部酒店</option>
        <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
      </select>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-score="{ value }">
          <span class="font-semibold" :class="(value as number) >= 4 ? 'text-teal-600' : (value as number) >= 3 ? 'text-amber-600' : 'text-red-600'">{{ value }}分</span>
        </template>
        <template #col-reply_content="{ value }">
          <span :class="value ? 'text-slate-700' : 'text-slate-400'">{{ value || '未回复' }}</span>
        </template>
        <template #actions="{ row }">
          <button class="text-sm text-teal-600 hover:underline" @click="openReply(row)">{{ row.reply_content ? '修改回复' : '回复' }}</button>
          <button class="ml-2 text-sm text-indigo-600 hover:underline" @click="getAISuggestion(row)">AI建议</button>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <!-- Reply Modal -->
    <ModalDialog :visible="showReply" title="回复评价" size="md" @close="showReply = false">
      <div class="space-y-4">
        <div>
          <h4 class="mb-1 text-sm font-medium text-slate-500">用户评价</h4>
          <div class="rounded-lg bg-slate-50 p-3 text-sm">
            <span class="font-semibold">{{ replyTarget.username }}</span> — {{ replyTarget.score }}分
            <p class="mt-1 text-slate-600">{{ replyTarget.content }}</p>
          </div>
        </div>
        <div v-if="aiSuggestion" class="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm">
          <div class="mb-1 font-medium text-indigo-700">AI 建议回复</div>
          <p class="text-indigo-900">{{ aiSuggestion }}</p>
          <button class="mt-2 text-xs text-indigo-600 hover:underline" @click="replyContent = aiSuggestion">采纳此回复</button>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">回复内容</label>
          <textarea v-model="replyContent" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="输入回复内容…" />
        </div>
      </div>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showReply = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="!replyContent.trim()" @click="submitReply">提交回复</button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { reviewApi, hotelApi, aiApi } from '@hotelink/api'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination } from '@hotelink/ui'

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'username', label: '用户' },
  { key: 'score', label: '评分' },
  { key: 'content', label: '评价内容' },
  { key: 'reply_content', label: '回复' },
  { key: 'created_at', label: '评价时间' },
]

const list = ref<Record<string, unknown>[]>([])
const hotels = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const hotelId = ref('')

const showReply = ref(false)
const replyTarget = reactive<Record<string, unknown>>({})
const replyContent = ref('')
const aiSuggestion = ref('')

async function loadList() {
  loading.value = true
  const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
  if (hotelId.value) params.hotel_id = hotelId.value
  const res = await reviewApi.list(params)
  if (res.code === 0 && res.data) {
    const d = res.data as unknown as { items: Record<string, unknown>[]; total: number }
    list.value = d.items || []
    total.value = d.total || 0
  }
  loading.value = false
}

async function loadHotels() {
  const res = await hotelApi.list({ page: 1, page_size: 200 })
  if (res.code === 0 && res.data) {
    hotels.value = (res.data as unknown as { items: Record<string, unknown>[] }).items || []
  }
}

function openReply(row: Record<string, unknown>) {
  Object.assign(replyTarget, row)
  replyContent.value = (row.reply_content as string) || ''
  aiSuggestion.value = ''
  showReply.value = true
}

async function getAISuggestion(row: Record<string, unknown>) {
  openReply(row)
  try {
    const res = await aiApi.replySuggestion({ review_id: row.id as number })
    if (res.code === 0 && res.data) {
      aiSuggestion.value = (res.data as Record<string, unknown>).suggestion as string || ''
    }
  } catch {
    // AI service may be unavailable
  }
}

async function submitReply() {
  await reviewApi.reply({ review_id: replyTarget.id as number, content: replyContent.value })
  showReply.value = false
  loadList()
}

onMounted(() => {
  loadList()
  loadHotels()
})
</script>

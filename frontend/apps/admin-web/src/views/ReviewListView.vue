<template>
  <section>
    <PageHeader title="评价管理" subtitle="查看并回复用户评价" />

    <div class="mb-4 flex flex-wrap gap-3">
      <SelectField v-model="hotelId" size="sm" @change="loadList">
        <option value="">全部酒店</option>
        <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
      </SelectField>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <table class="w-full table-fixed text-left text-sm">
        <colgroup>
          <col class="w-12" />
          <col class="w-24" />
          <col class="w-16" />
          <col />
          <col class="w-48" />
          <col class="w-44" />
          <col class="w-24" />
        </colgroup>
        <thead>
          <tr class="border-b border-slate-200 text-xs font-semibold uppercase text-slate-500">
            <th class="px-4 py-3">ID</th>
            <th class="px-4 py-3">用户</th>
            <th class="px-4 py-3">评分</th>
            <th class="px-4 py-3">评价内容</th>
            <th class="px-4 py-3">回复</th>
            <th class="px-4 py-3">评价时间</th>
            <th class="px-4 py-3">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="px-4 py-8 text-center text-slate-400">加载中…</td>
          </tr>
          <tr v-else-if="!list.length">
            <td colspan="7" class="px-4 py-8 text-center text-slate-400">暂无数据</td>
          </tr>
          <tr v-for="row in list" :key="row.id as number" class="border-b border-slate-100 transition-colors hover:bg-slate-50">
            <td class="px-4 py-3 text-slate-400">{{ row.id }}</td>
            <td class="truncate px-4 py-3 font-medium">{{ row.username }}</td>
            <td class="px-4 py-3">
              <span class="font-semibold" :class="(row.score as number) >= 4 ? 'text-teal-600' : (row.score as number) >= 3 ? 'text-amber-600' : 'text-red-600'">{{ row.score }}分</span>
            </td>
            <td class="px-4 py-3">
              <p class="cursor-pointer truncate text-slate-700" :title="row.content as string" @click="openReply(row)">{{ row.content }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="truncate" :class="row.reply_content ? 'text-slate-700' : 'text-slate-400'">{{ row.reply_content || '未回复' }}</p>
            </td>
            <td class="px-4 py-3 text-xs text-slate-400">{{ row.created_at }}</td>
            <td class="px-4 py-3">
              <button class="text-sm text-teal-600 hover:underline" @click="openReply(row)">查看详情</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <!-- Reply / Detail Modal -->
    <ModalDialog :visible="showReply" title="评价详情" size="md" @close="showReply = false">
      <div class="space-y-4">
        <div>
          <div class="mb-1 flex items-center justify-between">
            <h4 class="text-sm font-medium text-slate-500">用户评价</h4>
            <span class="text-sm font-semibold" :class="(replyTarget.score as number) >= 4 ? 'text-teal-600' : (replyTarget.score as number) >= 3 ? 'text-amber-600' : 'text-red-500'">{{ replyTarget.score }}分</span>
          </div>
          <div class="rounded-lg bg-slate-50 p-3 text-sm">
            <span class="font-semibold text-slate-700">{{ replyTarget.username }}</span>
            <p class="mt-2 max-h-36 overflow-y-auto break-words whitespace-pre-wrap text-slate-600 leading-relaxed">{{ replyTarget.content }}</p>
          </div>
        </div>

        <!-- AI Suggestion -->
        <div>
          <div class="mb-1 flex items-center justify-between">
            <h4 class="text-sm font-medium text-slate-500">AI 建议回复</h4>
            <button class="flex items-center gap-1 rounded-lg bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-100 disabled:opacity-50" :disabled="loadingAI || replying || deleting" @click="fetchAISuggestion">
              <span v-if="loadingAI" class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></span>
              <span>{{ loadingAI ? '获取中…' : '获取AI建议' }}</span>
            </button>
          </div>
          <div v-if="aiSuggestion" class="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm">
            <p class="text-indigo-900 leading-relaxed">{{ aiSuggestion }}</p>
            <button class="mt-2 text-xs text-indigo-600 hover:underline" @click="replyContent = aiSuggestion">采纳此回复</button>
          </div>
          <div v-else class="rounded-lg border border-dashed border-slate-200 px-3 py-2 text-xs text-slate-400">点击『获取AI建议』生成智能回复</div>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">回复内容</label>
          <textarea v-model="replyContent" rows="3" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="输入回复内容…" />
        </div>
      </div>
      <template #footer>
        <button v-if="isSystemAdmin" class="mr-auto rounded-lg bg-red-50 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60" :disabled="replying || deleting" @click="deleteReview(replyTarget.id as number)">{{ deleting ? '删除中…' : '删除评价' }}</button>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showReply = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="!replyContent.trim() || replying || deleting" @click="submitReply">{{ replying ? '提交中…' : '提交回复' }}</button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { reviewApi, hotelApi, aiApi } from '@hotelink/api'
import { extractApiError } from '@hotelink/utils'
import { PageHeader, ModalDialog, Pagination, useToast, useConfirm, SelectField } from '@hotelink/ui'
import { useAuthStore } from '@hotelink/store'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()
const auth = useAuthStore()
const isSystemAdmin = computed(() => auth.user?.role === 'system_admin')

interface HotelOption {
  id: number
  name: string
}

const list = ref<Record<string, unknown>[]>([])
const hotels = ref<HotelOption[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const hotelId = ref('')

const showReply = ref(false)
const replyTarget = reactive<Record<string, unknown>>({})
const replyContent = ref('')
const aiSuggestion = ref('')
const loadingAI = ref(false)
const replying = ref(false)
const deleting = ref(false)

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
    if (hotelId.value) params.hotel_id = hotelId.value
    const res = await reviewApi.list(params)
    if (res.code === 0 && res.data) {
      const d = res.data as unknown as { items: Record<string, unknown>[]; total: number }
      list.value = d.items || []
      total.value = d.total || 0
    } else {
      showToast(res.message || '加载评价列表失败', 'error')
    }
  } catch {
    showToast('加载评价列表失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

// 加载 Hotels 相关数据。
async function loadHotels() {
  try {
    const res = await hotelApi.list({ page: 1, page_size: 200 })
    if (res.code === 0 && res.data) {
      hotels.value = ((res.data as unknown as { items: HotelOption[] }).items || []).map(item => ({
        id: Number(item.id),
        name: String(item.name || ''),
      }))
    }
  } catch {
    showToast('加载酒店列表失败', 'error')
  }
}

// 打开 Reply 相关界面。
function openReply(row: Record<string, unknown>) {
  Object.assign(replyTarget, row)
  replyContent.value = (row.reply_content as string) || ''
  aiSuggestion.value = ''
  loadingAI.value = false
  showReply.value = true
}

// 内联获取 AI 建议。
async function fetchAISuggestion() {
  loadingAI.value = true
  try {
    const res = await aiApi.replySuggestion({ review_id: replyTarget.id as number })
    if (res.code === 0 && res.data) {
      const payload = res.data as Record<string, unknown>
      const direct = String(payload.suggested_reply || '')
      const suggestions = Array.isArray(payload.suggestions) ? payload.suggestions : []
      const firstSuggestion = suggestions.length > 0 ? String((suggestions[0] as Record<string, unknown>).content || '') : ''
      aiSuggestion.value = direct || firstSuggestion
      if (aiSuggestion.value) {
        showToast('已获取 AI 建议回复', 'success')
      } else {
        showToast('未获取到有效建议，请稍后重试', 'warning')
      }
    } else {
      showToast(res.message || 'AI 建议获取失败', 'warning')
    }
  } catch {
    showToast('AI 服务不可用，请检查 AI 配置', 'warning')
  } finally {
    loadingAI.value = false
  }
}

// 处理 submitReply 业务流程。
async function submitReply() {
  if (replying.value) return
  replying.value = true
  try {
    const res = await reviewApi.reply({ review_id: replyTarget.id as number, content: replyContent.value })
    if (res.code === 0) {
      showToast('回复提交成功', 'success')
      showReply.value = false
      loadList()
    } else {
      showToast(extractApiError(res, '回复提交失败'), 'error')
    }
  } catch {
    showToast('回复提交失败，请重试', 'error')
  } finally {
    replying.value = false
  }
}

// 删除评价。
async function deleteReview(id: number) {
  if (deleting.value) return
  if (!await confirmDialog('确定删除这条评价？该操作不可恢复。', { type: 'danger', title: '删除评价' })) return
  deleting.value = true
  try {
    const res = await reviewApi.delete({ review_id: id })
    if (res.code === 0) {
      showToast('评价已删除', 'success')
      showReply.value = false
      loadList()
    } else {
      showToast(extractApiError(res, '删除失败'), 'error')
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  loadList()
  loadHotels()
})
</script>

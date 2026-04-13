<template>
  <div class="flex min-h-[100dvh] flex-col bg-gradient-to-br from-gray-50 to-gray-100">
    <!-- Header -->
    <header class="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm">
      <button @click="$router.back()" class="rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <div class="flex items-center gap-2">
        <span class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand/80 text-white shadow-sm">🤖</span>
        <div>
          <h1 class="text-sm font-semibold text-gray-800">{{ pageTitle }}</h1>
          <p class="text-xs text-green-500">🟢 在线</p>
        </div>
      </div>
      <!-- Header Actions -->
      <div class="relative">
        <button @click="showMenu = !showMenu" class="rounded-lg p-2 text-gray-600 hover:bg-gray-100 transition">
          ⋮
        </button>
        <div v-if="showMenu" class="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-100 z-50">
          <button @click="showHistoryPanel = true; showMenu = false" class="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 text-gray-700 flex items-center gap-2 hover:text-brand">
            📜 查看历史聊天
          </button>
          <button @click="confirmClear" class="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 text-gray-700 flex items-center gap-2 hover:text-red-500 border-t">
            🗑️ 清空当前聊天
          </button>
        </div>
      </div>
    </header>

    <!-- History Panel Modal -->
    <div v-if="showHistoryPanel" class="fixed inset-0 z-40 flex items-end bg-black/20 animate-fadeIn">
      <div class="w-full rounded-t-2xl bg-white p-4 shadow-2xl max-h-[80vh] flex flex-col">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <h2 class="text-base font-semibold text-gray-800">📜 聊天历史</h2>
          <button @click="showHistoryPanel = false" class="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div class="flex-1 overflow-y-auto my-3">
          <div v-if="chatHistories.length === 0" class="text-center py-8 text-gray-500">
            <p class="text-sm">还没有历史聊天记录</p>
          </div>
          <div v-else class="space-y-2">
            <div v-for="(history, idx) in chatHistories" :key="`${history.timestamp}-${idx}`" 
              class="group flex items-start justify-between gap-2 rounded-lg p-3 bg-gray-50 hover:bg-gray-100 transition">
              <div class="flex-1 min-w-0">
                <p class="text-xs text-gray-500">{{ formatHistoryTime(history.timestamp) }}</p>
                <p class="text-sm font-medium text-gray-800 line-clamp-2 mt-1">
                  {{ history.preview || '（空聊天）' }}
                </p>
                <p class="text-xs text-gray-500 mt-1">{{ history.messageCount }} 条消息</p>
              </div>
              <div class="flex gap-1">
                <button @click="restoreHistory(idx)" class="rounded p-1.5 text-gray-600 hover:bg-blue-100 hover:text-blue-600 transition opacity-0 group-hover:opacity-100"
                  title="恢复">
                  ↩️
                </button>
                <button @click="deleteHistory(idx)" class="rounded p-1.5 text-gray-600 hover:bg-red-100 hover:text-red-600 transition opacity-0 group-hover:opacity-100"
                  title="删除">
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
        <button @click="showHistoryPanel = false" class="mt-3 w-full rounded-lg bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-200">
          关闭
        </button>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showClearConfirm" class="fixed inset-0 z-40 flex items-center justify-center bg-black/30 animate-fadeIn">
      <div class="rounded-2xl bg-white p-5 shadow-xl w-80">
        <p class="text-base font-semibold text-gray-800">确定要清空当前聊天吗？</p>
        <p class="text-sm text-gray-500 mt-2">这会清除本次对话的所有消息记录（历史聊天不会删除）。</p>
        <div class="flex gap-2 mt-5">
          <button @click="showClearConfirm = false" class="flex-1 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100">
            取消
          </button>
          <button @click="clearChat" class="flex-1 rounded-lg px-3 py-2.5 text-sm font-medium text-white bg-red-500 hover:bg-red-600">
            清空聊天
          </button>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div ref="chatBox" class="flex-1 space-y-4 overflow-y-auto p-4">
      <div v-for="msg in messages" :key="msg.id"
        class="flex animate-fadeIn" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <div class="max-w-[85%] rounded-2xl px-4 py-3 text-sm"
          :class="msg.role === 'user' ? 'bg-brand text-white rounded-br-sm shadow-md' : 'bg-white text-gray-700 shadow-md rounded-bl-sm'">
          <!-- Loading State -->
          <div v-if="msg.loading" class="flex gap-1">
            <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-400" style="animation-delay: 0ms" />
            <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-400" style="animation-delay: 100ms" />
            <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-400" style="animation-delay: 200ms" />
          </div>
          <!-- Assistant Response -->
          <template v-else-if="msg.role === 'assistant'">
            <div class="ai-markdown space-y-2" v-html="renderMd(msg.content)" />
            <!-- Smart Options -->
            <div v-if="msg.bookingAssistant?.options?.length" class="mt-4 space-y-2 border-t border-gray-100 pt-3">
              <p class="text-xs font-medium text-gray-500">💡 推荐选项：</p>
              <div
                v-for="option in msg.bookingAssistant.options"
                :key="`${option.type}-${option.value}`"
                @click="handleAssistantOption(option)"
                @keydown.enter="handleAssistantOption(option)"
                tabindex="0"
                role="button"
                class="group w-full rounded-2xl border-2 border-brand/20 bg-gradient-to-r from-brand/5 to-transparent px-3 py-3 text-left transition-all hover:border-brand/50 hover:bg-brand/10"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1">
                    <p class="font-semibold text-gray-800 group-hover:text-brand">{{ option.label }}</p>
                    <p v-if="option.description" class="mt-1 text-xs leading-5 text-gray-500">{{ option.description }}</p>
                  </div>
                  <div class="shrink-0 flex items-center gap-2">
                    <button
                      v-if="isHotelOption(option)"
                      @click.stop="openHotelDetail(option)"
                      class="rounded-md border border-brand/30 px-2 py-1 text-[11px] font-medium leading-none text-brand hover:bg-brand/10"
                    >
                      详情
                    </button>
                    <span class="text-xl group-hover:scale-110 transition-transform">
                      {{ getOptionEmoji(option.type) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <!-- User Message -->
          <p v-else class="whitespace-pre-wrap">{{ msg.content }}</p>
        </div>
      </div>

      <!-- Empty State Suggestion -->
      <div v-if="messages.length === 1" class="px-2">
        <div class="rounded-2xl bg-white p-4 shadow-sm border border-brand/10">
          <p class="text-xs text-gray-600 leading-relaxed">
            💬 直接告诉我您的需求，比如：<br/>
            <span class="mt-2 inline-block">
              • "我想在上海订个五星酒店"<br/>
              • "帮我找近地铁的酒店"<br/>
              • "预算500左右，要高评分的"
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div v-if="shouldShowQuickActions" class="flex flex-wrap gap-2 px-4 pb-2">
      <button v-for="q in dynamicQuickQuestions" :key="q" @click="sendMessage(q)"
        class="rounded-full border-2 border-brand/30 px-3 py-1.5 text-xs font-medium text-brand hover:border-brand/60 hover:bg-brand/5 transition-colors">
        {{ q }}
      </button>
    </div>

    <!-- Input -->
    <div class="safe-area-bottom border-t border-gray-200 bg-white p-3 shadow-lg">
      <div class="flex gap-2">
        <input v-model="input" @keydown.enter="sendMessage()" @focus="onInputFocus" placeholder="直接问我，我会帮您找到合适的酒店..."
          class="flex-1 rounded-2xl border-2 border-gray-200 px-4 py-2.5 text-sm outline-none focus:border-brand transition-colors" />
        <button @click="sendMessage()" :disabled="!input.trim() || sending"
          class="flex-shrink-0 rounded-2xl bg-gradient-to-r from-brand to-brand/90 px-6 py-2.5 text-sm font-medium text-white hover:shadow-lg disabled:opacity-50 transition-all">
          {{ sending ? '...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { userAiApi } from '@hotelink/api'

const router = useRouter()
const route = useRoute()
const chatBox = ref<HTMLElement | null>(null)
const input = ref('')
const sending = ref(false)
const showMenu = ref(false)
const showHistoryPanel = ref(false)
const showClearConfirm = ref(false)
const chatHistories = ref<ChatHistory[]>([])
const backendSessionId = ref<number | null>(null)

interface ChatHistory {
  timestamp: number
  messages: Msg[]
  preview: string
  messageCount: number
  bookingContext: BookingContext
  backendSessionId?: number | null
}

interface BookingContext {
  [key: string]: string | number | null | undefined
  intent?: string
  selected_city?: string | null
  selected_hotel_id?: number | null
}

interface AssistantOption {
  type: string
  label: string
  value: string
  description?: string
  payload?: Record<string, unknown>
  route?: string
  query?: Record<string, string>
}

interface BookingAssistant {
  intent: string
  phase: string
  context?: BookingContext
  options?: AssistantOption[]
}

interface Msg {
  id: string
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
  bookingAssistant?: BookingAssistant | null
}

let msgSeed = 0
function createMsgId(role: 'user' | 'assistant'): string {
  msgSeed += 1
  const prefix = role === 'user' ? 'u' : 'a'
  return `${prefix}-${Date.now()}-${msgSeed}`
}

function createMessage(
  role: 'user' | 'assistant',
  content: string,
  extras?: { loading?: boolean; bookingAssistant?: BookingAssistant | null }
): Msg {
  return {
    id: createMsgId(role),
    role,
    content,
    loading: extras?.loading,
    bookingAssistant: extras?.bookingAssistant,
  }
}

function normalizeMessages(raw: unknown): Msg[] {
  if (!Array.isArray(raw)) return []
  const normalized: Msg[] = []
  for (const item of raw) {
    if (!item || typeof item !== 'object') continue
    const record = item as Partial<Msg>
    if ((record.role !== 'user' && record.role !== 'assistant') || typeof record.content !== 'string') {
      continue
    }
    normalized.push({
      id: typeof record.id === 'string' && record.id ? record.id : createMsgId(record.role),
      role: record.role,
      content: record.content,
      loading: record.loading === true ? true : undefined,
      bookingAssistant: record.bookingAssistant || null,
    })
  }
  return normalized
}

const isBookingMode = route.path === '/ai-booking'
const scene = isBookingMode ? 'booking_assistant' : 'customer_service'

const pageTitle = isBookingMode ? 'AI 订房助手 🧭' : 'AI 智能客服 💬'

const sessionKey = isBookingMode ? 'hotelink_ai_booking_chat_state' : 'hotelink_ai_customer_chat_state'
const historyStorageKey = isBookingMode ? 'hotelink_ai_booking_history' : 'hotelink_ai_customer_history'
const defaultWelcome = isBookingMode
  ? '嗨，我是您的 AI 订房助手 🧭\n\n直接告诉我您想在哪里订酒店，什么时间？我会帮您快速找到最适合的房间。'
  : '您好！我是 HoteLink 的智能助理 💬\n\n有什么我可以帮您的吗？（预订、取消、退款、会员权益...）'

const messages = ref<Msg[]>([
  createMessage('assistant', defaultWelcome),
])

const bookingContext = ref<BookingContext>({})

// 动态快速问题：根据对话进度显示
const dynamicQuickQuestions = computed(() => {
  if (messages.value.length <= 1) {
    if (isBookingMode) {
      return ['上海出差订酒店', '北京五星酒店', '杭州近地铁的', '南京亲子房', '广州高评分的']
    } else {
      return ['如何预订？', '怎么取消？', '有退款吗？', '会员权益？', '在线客服？']
    }
  }
  return []
})

// 是否显示快速问题
const shouldShowQuickActions = computed(() => {
  return messages.value.length <= 1 && !sending.value
})

// 获取选项对应的emoji
function getOptionEmoji(type: string): string {
  const emojiMap: Record<string, string> = {
    'navigate_booking': '🛏️',
    'navigate_hotel': '🗺️',
    'select_city': '📍',
    'select_hotel': '🏨',
    'select_radius': '📏',
    'clarify_poi': '🧭',
    'select_price': '💰',
    'select_rating': '⭐',
    'select_feature': '✨',
    'check_availability': '📅',
    'confirm': '✅',
  }
  return emojiMap[type] || '→'
}

// 焦点时的处理
function onInputFocus() {
  // 可用于显示更多建议或提示
}

// 时间格式化
function formatHistoryTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - timestamp
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`

  return date.toLocaleDateString('zh-CN')
}

// 保存当前聊天到历史
function saveCurrentChatToHistory() {
  if (messages.value.length <= 1) return // 只有欢迎词，不保存
  
  const userMessages = messages.value.filter(m => m.role === 'user')
  if (userMessages.length === 0) return // 没有用户消息，不保存

  const preview = userMessages[0].content.slice(0, 50)
  const history: ChatHistory = {
    timestamp: Date.now(),
    messages: [...messages.value],
    preview,
    messageCount: messages.value.length,
    bookingContext: { ...bookingContext.value },
    backendSessionId: backendSessionId.value,
  }

  const existing = loadHistories()
  existing.unshift(history) // 新聊天放在最前面
  if (existing.length > 20) existing.pop() // 最多保留20条历史

  localStorage.setItem(historyStorageKey, JSON.stringify(existing))
  chatHistories.value = existing
}

// 从存储加载历史
function loadHistories(): ChatHistory[] {
  const raw = localStorage.getItem(historyStorageKey)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw) as ChatHistory[]
    if (!Array.isArray(parsed)) return []
    return parsed.map((item) => ({
      ...item,
      messages: normalizeMessages(item?.messages),
      bookingContext: (item?.bookingContext && typeof item.bookingContext === 'object')
        ? item.bookingContext
        : {},
      backendSessionId: Number.isFinite(Number(item?.backendSessionId))
        ? Number(item?.backendSessionId)
        : null,
    }))
  } catch {
    return []
  }
}

// 恢复历史聊天
function restoreHistory(idx: number) {
  const history = chatHistories.value[idx]
  if (!history) return

  messages.value = normalizeMessages(history.messages).filter(m => !m.loading)
  bookingContext.value = { ...history.bookingContext }
  backendSessionId.value = Number.isFinite(Number(history.backendSessionId)) ? Number(history.backendSessionId) : null
  showHistoryPanel.value = false
  scrollBottom()
  
  // 关闭菜单
  showMenu.value = false
}

// 删除历史聊天
function deleteHistory(idx: number) {
  const remaining = chatHistories.value.filter((_, i) => i !== idx)
  chatHistories.value = remaining
  localStorage.setItem(historyStorageKey, JSON.stringify(remaining))
}

// 确认清空
function confirmClear() {
  showClearConfirm.value = true
  showMenu.value = false
}

// 清空当前聊天
function clearChat() {
  messages.value = [
    createMessage('assistant', defaultWelcome),
  ]
  bookingContext.value = {}
  backendSessionId.value = null
  input.value = ''
  showClearConfirm.value = false
  scrollBottom()
}

function saveSessionState() {
  const payload = {
    messages: messages.value,
    bookingContext: bookingContext.value,
    backendSessionId: backendSessionId.value,
  }
  sessionStorage.setItem(sessionKey, JSON.stringify(payload))
}

function restoreSessionState() {
  const raw = sessionStorage.getItem(sessionKey)
  if (!raw) return false
  try {
    const parsed = JSON.parse(raw) as { messages?: Msg[]; bookingContext?: BookingContext; backendSessionId?: number | null }
    const restoredMessages = normalizeMessages(parsed.messages)
    if (restoredMessages.length) {
      messages.value = restoredMessages.filter((m) => !m.loading)
    }
    if (parsed.bookingContext && typeof parsed.bookingContext === 'object') {
      bookingContext.value = parsed.bookingContext
    }
    backendSessionId.value = Number.isFinite(Number(parsed.backendSessionId)) ? Number(parsed.backendSessionId) : null
    return true
  } catch {
    return false
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function sanitizeRenderedMarkdown(html: string): string {
  return html.replace(/href="([^"]*)"/gi, (_, href: string) => {
    const normalized = href.trim()
    if (/^(https?:|mailto:|tel:|\/)/i.test(normalized)) {
      return `href="${normalized}" target="_blank" rel="noopener noreferrer"`
    }
    return 'href="#"'
  })
}

function renderMd(text: string): string {
  const html = marked.parse(escapeHtml(text)) as string
  return sanitizeRenderedMarkdown(html)
}

function mergeBookingContext(contextPatch?: Record<string, unknown>): BookingContext {
  const patch = (contextPatch || {}) as BookingContext
  return {
    ...bookingContext.value,
    ...patch,
  }
}

function shouldCarryBookingContext(message: string, contextPatch?: Record<string, unknown>): boolean {
  if (contextPatch) return true
  if (!bookingContext.value.intent) return false
  const value = message.trim()
  if (value.length <= 10) return true
  return ['订', '预订', '房型', '入住', '酒店', '城市', '地点', '地区'].some(keyword => value.includes(keyword))
}

// 将列表滚动到容器底部
function scrollBottom() {
  nextTick(() => { 
    if (chatBox.value) {
      chatBox.value.scrollTo({ top: chatBox.value.scrollHeight, behavior: 'smooth' })
    }
  })
}

async function handleAssistantOption(option: AssistantOption) {
  if (option.route) {
    await router.push({ path: option.route, query: option.query || {} })
    return
  }
  await sendMessage(option.label, option.payload)
}

function isHotelOption(option: AssistantOption): boolean {
  return option.type === 'select_hotel' || option.type === 'navigate_hotel'
}

function resolveHotelDetailTarget(option: AssistantOption): { path: string; query?: Record<string, string> } | null {
  if (option.type === 'navigate_hotel' && option.route) {
    return { path: option.route, query: option.query || {} }
  }
  if (option.type === 'select_hotel') {
    const hotelId = Number(option.value)
    if (Number.isFinite(hotelId) && hotelId > 0) {
      return { path: `/hotels/${hotelId}`, query: option.query || {} }
    }
  }
  return null
}

async function openHotelDetail(option: AssistantOption) {
  const target = resolveHotelDetailTarget(option)
  if (!target) return
  await router.push(target)
}

// 处理 sendMessage 业务流程（流式）
async function sendMessage(text?: string, contextPatch?: Record<string, unknown>) {
  const msg = (text || input.value).trim()
  if (!msg || sending.value) return
  
  const carryBookingContext = shouldCarryBookingContext(msg, contextPatch)
  const nextBookingContext = carryBookingContext ? mergeBookingContext(contextPatch) : undefined
  input.value = ''
  messages.value.push(createMessage('user', msg))
  scrollBottom()

  // Loading placeholder until first token arrives
  messages.value.push(createMessage('assistant', '', { loading: true }))
  scrollBottom()
  sending.value = true

  let receivedAny = false
  let pendingBookingAssistant: BookingAssistant | null = null
  try {
    for await (const event of userAiApi.chatStream({
      scene,
      question: msg,
      hotel_id: nextBookingContext?.selected_hotel_id || undefined,
      session_id: backendSessionId.value || undefined,
      booking_context: nextBookingContext,
    })) {
      if (event.type === 'meta') {
        pendingBookingAssistant = (event.booking_assistant as BookingAssistant) || null
        const incomingSessionId = Number(event.session_id)
        if (Number.isFinite(incomingSessionId) && incomingSessionId > 0) {
          backendSessionId.value = incomingSessionId
        }
        if (pendingBookingAssistant?.context) {
          bookingContext.value = { ...pendingBookingAssistant.context }
        }
        continue
      }

      const chunk = typeof event.content === 'string' ? event.content : ''
      const isDone = event.done === true || event.type === 'done'
      const incomingSessionId = Number(event.session_id)
      if (Number.isFinite(incomingSessionId) && incomingSessionId > 0) {
        backendSessionId.value = incomingSessionId
      }
      if (!receivedAny) {
        messages.value.pop()
        messages.value.push(createMessage('assistant', '', { bookingAssistant: pendingBookingAssistant }))
        receivedAny = true
      }
      if (chunk) {
        messages.value[messages.value.length - 1].content += chunk
        scrollBottom()
      }
      if (isDone) break
    }
    if (!receivedAny) throw new Error('no reply')
    if (!pendingBookingAssistant && !carryBookingContext) {
      bookingContext.value = {}
    }
  } catch (err) {
    if (!receivedAny) messages.value.pop()
    messages.value.push(createMessage('assistant', generateFallback(msg)))
    if (!carryBookingContext) {
      bookingContext.value = {}
    }
  }
  sending.value = false
  scrollBottom()
}

// 处理 generateFallback 业务流程。优化的业务逻辑
function generateFallback(q: string): string {
  // 订房相关
  if (isBookingMode) {
    if (q.includes('上海') || q.includes('北京') || q.includes('广东') || q.includes('浙江')) {
      return '我没能完整理解您的需求，但我可以帮您：\n\n📍 指定您想要的具体城市\n📅 告诉我入住日期\n💰 预算范围\n\n这样我就能为您推荐最合适的酒店了！'
    }
    return '抱歉，我暂时遇到了问题。您可以：\n\n1️⃣ 在首页直接搜索酒店\n2️⃣ 重新描述您的需求，比如"我要在上海预订酒店，5月1日入住"\n3️⃣ 如需帮助请拨打 400-123-4567'
  }

  // 客服相关
  if (q.includes('预订')) return '预订酒店只需 3 步：\n\n1️⃣ 搜索目的地和日期\n2️⃣ 选择心仪的房型\n3️⃣ 填写信息并支付\n\n就能完成预订了！'
  if (q.includes('取消')) return '您可以在「我的订单」页面找到订单，点击「取消」即可。\n\n⚠️ 请注意查看酒店的取消政策和最后退订时间。'
  if (q.includes('退款')) return '取消订单后，根据酒店政策：\n\n✅ 可退款订单 → 1-3 个工作日内原路返还\n⏳ 不可退款 → 无法退款但可能支持改期\n\n具体请查看订单详情。'
  if (q.includes('会员') || q.includes('权益')) return '会员权益包括：\n\n⭐ 预订享折扣\n🎁 积分返利\n🛏️ 高级房型免费升级\n⏱️ 延迟退房\n\n入住即可升级会员等级！'
  if (q.includes('推荐') || q.includes('热门')) return '我可以为您推荐热门酒店！请告诉我：\n\n📍 想去哪个城市？\n🎯 什么时间入住？\n💰 预算范围？\n\n我会给您最合适的推荐。'

  return '感谢您的提问！😊\n\n我暂时还无法理解这个问题，请：\n\n💬 换个方式描述您的需求\n📞 拨打客服：400-123-4567\n🌐 访问帮助中心'
}

onMounted(async () => {
  const restored = restoreSessionState()
  chatHistories.value = loadHistories()
  scrollBottom()
  const ask = typeof route.query.ask === 'string' ? route.query.ask.trim() : ''
  if (ask && !restored) {
    await sendMessage(ask)
  }
})

watch(messages, () => {
  saveSessionState()
  // 当发送消息后，保存到历史（但不是每次都保存，只在清空或切换时保存）
}, { deep: true })

watch(bookingContext, saveSessionState, { deep: true })
watch(backendSessionId, saveSessionState)

function handleBeforeUnload() {
  if (messages.value.length > 1) {
    saveCurrentChatToHistory()
  }
}

// 在离开页面时保存聊天到历史
onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  handleBeforeUnload()
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<style scoped>
.ai-markdown :deep(p) { margin: 0 0 0.4em; }
.ai-markdown :deep(p:last-child) { margin-bottom: 0; }
.ai-markdown :deep(ul),
.ai-markdown :deep(ol) { padding-left: 1.2em; margin: 0.3em 0; }
.ai-markdown :deep(li) { margin: 0.15em 0; }
.ai-markdown :deep(strong) { font-weight: 600; }
.ai-markdown :deep(code) { background: #f3f4f6; border-radius: 3px; padding: 0.1em 0.3em; font-size: 0.85em; }
.ai-markdown :deep(pre) { background: #1e293b; color: #e2e8f0; border-radius: 6px; padding: 0.75em 1em; overflow-x: auto; margin: 0.4em 0; }
.ai-markdown :deep(pre code) { background: none; padding: 0; }
.ai-markdown :deep(blockquote) { border-left: 3px solid #d1d5db; padding-left: 0.75em; color: #6b7280; margin: 0.3em 0; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}
</style>

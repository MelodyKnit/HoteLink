<template>
  <div class="flex h-screen flex-col bg-gray-50">
    <!-- Header -->
    <header class="flex h-14 items-center gap-3 border-b border-gray-100 bg-white px-4">
      <button @click="$router.back()" class="rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <div class="flex items-center gap-2">
        <span class="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-white">🤖</span>
        <div>
          <h1 class="text-sm font-semibold text-gray-800">{{ pageTitle }}</h1>
          <p class="text-xs text-green-500">在线</p>
        </div>
      </div>
    </header>

    <!-- Messages -->
    <div ref="chatBox" class="flex-1 space-y-3 overflow-y-auto p-4">
      <div v-for="(msg, i) in messages" :key="i"
        class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <div class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm"
          :class="msg.role === 'user' ? 'bg-brand text-white rounded-br-md' : 'bg-white text-gray-700 shadow-sm rounded-bl-md'">
          <div v-if="msg.loading" class="flex gap-1">
            <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-300" style="animation-delay: 0ms" />
            <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-300" style="animation-delay: 150ms" />
            <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-300" style="animation-delay: 300ms" />
          </div>
          <template v-else-if="msg.role === 'assistant'">
            <div class="ai-markdown" v-html="renderMd(msg.content)" />
            <div v-if="msg.bookingAssistant?.options?.length" class="mt-3 space-y-2">
              <button
                v-for="option in msg.bookingAssistant.options"
                :key="`${option.type}-${option.value}-${option.label}`"
                @click="handleAssistantOption(option)"
                class="w-full rounded-2xl border border-brand/15 bg-brand/5 px-3 py-3 text-left transition hover:border-brand/30 hover:bg-brand/10"
              >
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-sm font-semibold text-gray-800">{{ option.label }}</p>
                    <p v-if="option.description" class="mt-1 text-xs leading-5 text-gray-500">{{ option.description }}</p>
                  </div>
                  <span class="shrink-0 text-xs font-medium text-brand">{{ option.type === 'navigate_booking' ? '去下单' : '选择' }}</span>
                </div>
              </button>
            </div>
          </template>
          <p v-else class="whitespace-pre-wrap">{{ msg.content }}</p>
        </div>
      </div>
    </div>

    <!-- Quick Questions -->
    <div v-if="messages.length <= 1" class="flex flex-wrap gap-2 px-4 pb-2">
      <button v-for="q in quickQuestions" :key="q" @click="sendMessage(q)"
        class="rounded-full border border-brand/30 px-3 py-1.5 text-xs font-medium text-brand hover:bg-brand/5">
        {{ q }}
      </button>
    </div>

    <!-- Input -->
    <div class="safe-area-bottom border-t border-gray-100 bg-white p-3">
      <div class="flex gap-2">
        <input v-model="input" @keydown.enter="sendMessage()" placeholder="输入您的问题..."
          class="flex-1 rounded-2xl border border-gray-200 px-4 py-2.5 text-sm outline-none focus:border-brand" />
        <button @click="sendMessage()" :disabled="!input.trim() || sending"
          class="flex-shrink-0 rounded-2xl bg-brand px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-40">
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { userAiApi } from '@hotelink/api'

const router = useRouter()
const route = useRoute()
const chatBox = ref<HTMLElement | null>(null)
const input = ref('')
const sending = ref(false)

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
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
  bookingAssistant?: BookingAssistant | null
}

const isBookingMode = route.path === '/ai-booking'
const scene = isBookingMode ? 'booking_assistant' : 'customer_service'

const pageTitle = isBookingMode ? 'AI 订房助手' : 'AI 智能客服'

const messages = ref<Msg[]>([
  {
    role: 'assistant',
    content: isBookingMode
      ? '您好，我是 HoteLink AI 订房助手 🧭\n\n告诉我目的地或酒店名，我会带您直接到可下单房型。'
      : '您好，我是 HoteLink 智能客服 🤖\n\n请问有什么可以帮您？',
  },
])

const bookingContext = ref<BookingContext>({})

const quickQuestions = isBookingMode
  ? [
      '我想订酒店',
      '我想订上海的酒店',
      '帮我找高评分酒店',
      '推荐适合亲子的酒店',
      '我想住离地铁近的酒店',
    ]
  : [
      '如何预订酒店？',
      '如何取消订单？',
      '如何申请退款？',
      '会员有什么权益？',
      '推荐热门酒店',
    ]

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderMd(text: string): string {
  return marked.parse(escapeHtml(text)) as string
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
  return ['订', '预订', '房型', '入住', '酒店'].some(keyword => value.includes(keyword))
}

// 将列表滚动到容器底部。
function scrollBottom() {
  nextTick(() => { chatBox.value?.scrollTo({ top: chatBox.value.scrollHeight, behavior: 'smooth' }) })
}

async function handleAssistantOption(option: AssistantOption) {
  if (option.route) {
    await router.push({ path: option.route, query: option.query || {} })
    return
  }
  await sendMessage(option.label, option.payload)
}

// 处理 sendMessage 业务流程（流式）。
async function sendMessage(text?: string, contextPatch?: Record<string, unknown>) {
  const msg = (text || input.value).trim()
  if (!msg || sending.value) return
  const carryBookingContext = shouldCarryBookingContext(msg, contextPatch)
  const nextBookingContext = carryBookingContext ? mergeBookingContext(contextPatch) : undefined
  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  scrollBottom()

  // Loading placeholder until first token arrives
  messages.value.push({ role: 'assistant', content: '', loading: true })
  scrollBottom()
  sending.value = true

  let receivedAny = false
  let pendingBookingAssistant: BookingAssistant | null = null
  try {
    for await (const event of userAiApi.chatStream({
      scene,
      question: msg,
      hotel_id: nextBookingContext?.selected_hotel_id || undefined,
      booking_context: nextBookingContext,
    })) {
      if (event.type === 'meta') {
        pendingBookingAssistant = (event.booking_assistant as BookingAssistant) || null
        if (pendingBookingAssistant?.context) {
          bookingContext.value = { ...pendingBookingAssistant.context }
        }
        continue
      }

      const chunk = typeof event.content === 'string' ? event.content : ''
      const isDone = event.done === true || event.type === 'done'
      if (!receivedAny) {
        messages.value.pop()
        messages.value.push({ role: 'assistant', content: '', bookingAssistant: pendingBookingAssistant })
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
  } catch {
    if (!receivedAny) messages.value.pop()
    messages.value.push({ role: 'assistant', content: generateFallback(msg) })
    if (!carryBookingContext) {
      bookingContext.value = {}
    }
  }
  sending.value = false
  scrollBottom()
}

// 处理 generateFallback 业务流程。
function generateFallback(q: string): string {
  if (q.includes('预订')) return '预订酒店非常简单：\n\n1. 在首页搜索或浏览酒店\n2. 选择心仪的房型\n3. 填写入住信息并支付\n\n即可完成预订 😊'
  if (q.includes('取消')) return '您可以在「我的订单」页面找到对应订单，点击「取消订单」即可。\n\n请注意查看酒店的取消政策哦。'
  if (q.includes('退款')) return '取消订单后，退款将在 **1-3 个工作日**内原路返回到您的支付账户。'
  if (q.includes('会员') || q.includes('权益')) return '成为会员可享受：\n\n- 专属折扣\n- 延迟退房\n- 免费升房\n\n入住即可累积积分升级哦！🎁'
  if (q.includes('推荐') || q.includes('热门')) return '我可以根据城市、预算和评分偏好为您推荐酒店。\n\n您可以直接说：\n- 我想订上海的酒店\n- 预算 500 左右\n- 优先高评分酒店'
  return '感谢您的提问！目前 AI 客服正在学习中。\n\n如需紧急帮助，请拨打客服电话：**400-123-4567**'
}

onMounted(async () => {
  scrollBottom()
  const ask = typeof route.query.ask === 'string' ? route.query.ask.trim() : ''
  if (ask) {
    await sendMessage(ask)
  }
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
</style>

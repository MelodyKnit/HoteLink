<template>
  <div class="flex h-screen flex-col bg-gray-50">
    <!-- Header -->
    <header class="flex h-14 items-center gap-3 border-b border-gray-100 bg-white px-4">
      <button @click="$router.back()" class="rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <div class="flex items-center gap-2">
        <span class="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-white">🤖</span>
        <div>
          <h1 class="text-sm font-semibold text-gray-800">AI 智能客服</h1>
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
          <div v-else-if="msg.role === 'assistant'" class="ai-markdown" v-html="renderMd(msg.content)" />
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
import { marked } from 'marked'
import { userAiApi } from '@hotelink/api'

const chatBox = ref<HTMLElement | null>(null)
const input = ref('')
const sending = ref(false)

interface Msg { role: 'user' | 'assistant'; content: string; loading?: boolean }
const messages = ref<Msg[]>([
  { role: 'assistant', content: '您好，我是 HoteLink 智能客服 🤖\n\n请问有什么可以帮您？' },
])

const quickQuestions = [
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

// 将列表滚动到容器底部。
function scrollBottom() {
  nextTick(() => { chatBox.value?.scrollTo({ top: chatBox.value.scrollHeight, behavior: 'smooth' }) })
}

// 处理 sendMessage 业务流程（流式）。
async function sendMessage(text?: string) {
  const msg = (text || input.value).trim()
  if (!msg || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  scrollBottom()

  // Loading placeholder until first token arrives
  messages.value.push({ role: 'assistant', content: '', loading: true })
  scrollBottom()
  sending.value = true

  let receivedAny = false
  try {
    for await (const event of userAiApi.chatStream({ scene: 'general', question: msg })) {
      if (!receivedAny) {
        messages.value.pop()
        messages.value.push({ role: 'assistant', content: '' })
        receivedAny = true
      }
      if (event.content) {
        messages.value[messages.value.length - 1].content += event.content
        scrollBottom()
      }
      if (event.done) break
    }
    if (!receivedAny) throw new Error('no reply')
  } catch {
    if (!receivedAny) messages.value.pop()
    messages.value.push({ role: 'assistant', content: generateFallback(msg) })
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
  if (q.includes('推荐') || q.includes('热门')) return '为您推荐几家热门酒店：\n\n- 🏨 海景花园大酒店（三亚）\n- 🏨 城市精品酒店（上海）\n- 🏨 山水度假村（桂林）\n\n您可以在首页查看更多推荐。'
  return '感谢您的提问！目前 AI 客服正在学习中。\n\n如需紧急帮助，请拨打客服电话：**400-123-4567**'
}

onMounted(scrollBottom)
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

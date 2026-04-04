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
import { userAiApi } from '@hotelink/api'

const chatBox = ref<HTMLElement | null>(null)
const input = ref('')
const sending = ref(false)

interface Msg { role: 'user' | 'assistant'; content: string; loading?: boolean }
const messages = ref<Msg[]>([
  { role: 'assistant', content: '您好，我是 HoteLink 智能客服 🤖\n请问有什么可以帮您？' },
])

const quickQuestions = [
  '如何预订酒店？',
  '如何取消订单？',
  '如何申请退款？',
  '会员有什么权益？',
  '推荐热门酒店',
]

function scrollBottom() {
  nextTick(() => { chatBox.value?.scrollTo({ top: chatBox.value.scrollHeight, behavior: 'smooth' }) })
}

async function sendMessage(text?: string) {
  const msg = (text || input.value).trim()
  if (!msg || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  scrollBottom()

  // Loading placeholder
  messages.value.push({ role: 'assistant', content: '', loading: true })
  scrollBottom()
  sending.value = true

  try {
    const res = await userAiApi.chat({ scene: 'general', question: msg })
    messages.value.pop() // Remove loading
    if (res.code === 0 && res.data?.answer) {
      messages.value.push({ role: 'assistant', content: res.data.answer })
    } else {
      throw new Error('no reply')
    }
  } catch {
    messages.value.pop()
    messages.value.push({
      role: 'assistant',
      content: generateFallback(msg),
    })
  }
  sending.value = false
  scrollBottom()
}

function generateFallback(q: string): string {
  if (q.includes('预订')) return '预订酒店非常简单：\n1. 在首页搜索或浏览酒店\n2. 选择心仪的房型\n3. 填写入住信息并支付\n即可完成预订 😊'
  if (q.includes('取消')) return '您可以在「我的订单」页面找到对应订单，点击「取消订单」即可。请注意查看酒店的取消政策哦。'
  if (q.includes('退款')) return '取消订单后，退款将在1-3个工作日内原路返回到您的支付账户。'
  if (q.includes('会员') || q.includes('权益')) return '成为会员可享受专属折扣、延迟退房、免费升房等权益。入住即可累积积分升级哦！🎁'
  if (q.includes('推荐') || q.includes('热门')) return '为您推荐几家热门酒店：\n🏨 海景花园大酒店（三亚）\n🏨 城市精品酒店（上海）\n🏨 山水度假村（桂林）\n您可以在首页查看更多推荐。'
  return '感谢您的提问！目前AI客服正在学习中。\n如需紧急帮助，请拨打客服电话：400-123-4567'
}

onMounted(scrollBottom)
</script>

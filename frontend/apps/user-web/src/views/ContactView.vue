<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">联系我们</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-6 pb-24 md:pb-6">
      <div class="space-y-3">
        <a href="tel:4001234567" class="flex items-center gap-4 rounded-2xl bg-white p-5 shadow-sm hover:shadow">
          <span class="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-2xl">📞</span>
          <div>
            <p class="font-semibold text-gray-800">客服热线</p>
            <p class="text-sm text-brand">400-123-4567</p>
            <p class="text-xs text-gray-400">工作日 9:00 - 21:00</p>
          </div>
        </a>

        <a href="mailto:service@hotelink.com" class="flex items-center gap-4 rounded-2xl bg-white p-5 shadow-sm hover:shadow">
          <span class="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-2xl">📧</span>
          <div>
            <p class="font-semibold text-gray-800">电子邮箱</p>
            <p class="text-sm text-blue-600">service@hotelink.com</p>
            <p class="text-xs text-gray-400">1-2个工作日内回复</p>
          </div>
        </a>

        <router-link to="/ai-chat" class="flex items-center gap-4 rounded-2xl bg-white p-5 shadow-sm hover:shadow">
          <span class="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-2xl">🤖</span>
          <div>
            <p class="font-semibold text-gray-800">AI 在线客服</p>
            <p class="text-sm text-purple-600">7×24小时在线</p>
            <p class="text-xs text-gray-400">即时响应，智能解答</p>
          </div>
        </router-link>
      </div>

      <div class="mt-6 rounded-2xl bg-white p-5 shadow-sm">
        <h3 class="font-semibold text-gray-800">公司地址</h3>
        <div class="mt-3 space-y-4">
          <div v-for="addr in addresses" :key="addr.city" class="flex gap-3">
            <span class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-lg">📍</span>
            <div>
              <p class="text-sm font-medium text-gray-800">{{ addr.city }}{{ addr.label }}</p>
              <p class="text-xs text-gray-400">{{ addr.address }}</p>
              <p class="text-xs text-gray-400">{{ addr.phone }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-6 rounded-2xl bg-white p-5 shadow-sm">
        <h3 class="font-semibold text-gray-800">意见反馈</h3>
        <p class="mt-1 text-xs text-gray-400">您可以描述遇到的问题、期待的功能，或留下想对我们说的话。</p>
        <div class="mt-4 space-y-3">
          <div>
            <SelectField v-model="feedback.type" class="w-full">
              <option value="">请选择反馈类型</option>
              <option value="suggestion">功能建议</option>
              <option value="bug">问题反馈</option>
              <option value="complaint">投诉</option>
              <option value="praise">表扬</option>
            </SelectField>
            <p v-if="errors.type" class="mt-1 text-xs text-red-500">{{ errors.type }}</p>
          </div>

          <div>
            <textarea
              v-model="feedback.content"
              rows="4"
              placeholder="请详细描述您的反馈内容..."
              class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
              :class="errors.content ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="clearError('content')"
              @blur="validateField('content')"
            />
            <div class="mt-1 flex items-center justify-between">
              <p v-if="errors.content" class="text-xs text-red-500">{{ errors.content }}</p>
              <p v-else class="text-xs text-gray-400">建议尽量说明发生时间、页面位置或预期结果，方便我们更快处理。</p>
              <span class="text-xs" :class="feedback.content.length > 300 ? 'text-red-500' : 'text-gray-400'">{{ feedback.content.length }}/300</span>
            </div>
          </div>

          <div>
            <input
              v-model="feedback.contact"
              placeholder="联系方式（手机或邮箱，选填）"
              class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
              :class="errors.contact ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-gray-200 focus:border-brand'"
              @input="clearError('contact')"
              @blur="validateField('contact')"
            />
            <p v-if="errors.contact" class="mt-1 text-xs text-red-500">{{ errors.contact }}</p>
            <p v-else class="mt-1 text-xs text-gray-400">如果愿意接受回访，留下联系方式会更方便我们跟进。</p>
          </div>

          <button
            @click="submitFeedback"
            :disabled="submitting"
            class="w-full rounded-xl bg-brand py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {{ submitting ? '提交中...' : '提交反馈' }}
          </button>
        </div>
      </div>

      <div class="mt-6 rounded-2xl bg-white p-5 text-center shadow-sm">
        <h3 class="font-semibold text-gray-800">关注我们</h3>
        <div class="mt-3 flex justify-center gap-6">
          <div class="text-center">
            <span class="text-3xl">💬</span>
            <p class="mt-1 text-xs text-gray-400">微信公众号</p>
          </div>
          <div class="text-center">
            <span class="text-3xl">📱</span>
            <p class="mt-1 text-xs text-gray-400">官方微博</p>
          </div>
          <div class="text-center">
            <span class="text-3xl">🎵</span>
            <p class="mt-1 text-xs text-gray-400">抖音号</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { SelectField, useToast } from '@hotelink/ui'
import { isValidContactInfo } from '@hotelink/utils'

type FeedbackField = 'type' | 'content' | 'contact'

const { showToast } = useToast()

const feedback = ref({ type: '', content: '', contact: '' })
const submitting = ref(false)
const errors = ref<Partial<Record<FeedbackField, string>>>({})

const addresses = [
  { city: '北京', label: '总部', address: '朝阳区建国路88号SOHO现代城A座18层', phone: '010-8888-0001' },
  { city: '上海', label: '分公司', address: '浦东新区陆家嘴环路1000号恒生银行大厦32层', phone: '021-6688-0002' },
  { city: '深圳', label: '分公司', address: '南山区科技中一路腾讯滨海大厦旁创新科技园6层', phone: '0755-8688-0003' },
]

function clearError(field: FeedbackField) {
  if (errors.value[field]) {
    errors.value = { ...errors.value, [field]: undefined }
  }
}

function getFieldError(field: FeedbackField): string {
  switch (field) {
    case 'type':
      return feedback.value.type ? '' : '请选择反馈类型'
    case 'content':
      if (!feedback.value.content.trim()) return '请填写反馈内容'
      if (feedback.value.content.trim().length < 10) return '为了便于定位问题，建议至少填写 10 个字'
      return feedback.value.content.length > 300 ? '反馈内容不能超过 300 个字符' : ''
    case 'contact':
      if (!feedback.value.contact.trim()) return ''
      return isValidContactInfo(feedback.value.contact) ? '' : '请填写有效的手机号或邮箱'
    default:
      return ''
  }
}

function validateField(field: FeedbackField) {
  errors.value = {
    ...errors.value,
    [field]: getFieldError(field) || undefined,
  }
}

function validateForm(): boolean {
  const nextErrors: Partial<Record<FeedbackField, string>> = {}
  feedback.value.contact = feedback.value.contact.trim()

  ;(['type', 'content', 'contact'] as FeedbackField[]).forEach((field) => {
    const message = getFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  errors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 submitFeedback 业务流程。
async function submitFeedback() {
  if (!validateForm()) {
    showToast(Object.values(errors.value).find(Boolean) || '请检查反馈信息', 'warning')
    return
  }

  submitting.value = true
  // TODO: 对接实际反馈 API，当前为前端演示。
  await new Promise((resolve) => setTimeout(resolve, 800))
  showToast('感谢您的反馈！我们已收到并会认真处理。', 'success')
  feedback.value = { type: '', content: '', contact: '' }
  errors.value = {}
  submitting.value = false
}
</script>

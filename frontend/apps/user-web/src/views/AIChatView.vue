<template>
  <div class="flex h-[100dvh] flex-col overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100">
    <!-- Header -->
    <header class="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-white/95 px-4 shadow-sm backdrop-blur">
      <button @click="$router.back()" class="rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <div class="flex items-center gap-2">
        <span class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand/80 text-[11px] font-semibold tracking-wide text-white shadow-sm">AI</span>
        <div>
          <h1 class="text-sm font-semibold text-gray-800">{{ pageTitle }}</h1>
          <p class="mt-0.5 inline-flex items-center gap-1.5 text-[11px] text-emerald-500">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            在线服务中
          </p>
        </div>
      </div>
      <!-- Header Actions -->
      <div class="relative">
        <button @click="showMenu = !showMenu" class="rounded-lg p-2 text-gray-600 hover:bg-gray-100 transition">
          ⋮
        </button>
        <div v-if="showMenu" class="absolute right-0 z-50 mt-1 w-40 rounded-lg border border-gray-100 bg-white shadow-lg">
          <button @click="showHistoryPanel = true; showMenu = false" class="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 hover:text-brand">
            查看历史聊天
          </button>
          <button @click="confirmClear" class="flex w-full items-center gap-2 border-t px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 hover:text-red-500">
            清空当前聊天
          </button>
        </div>
      </div>
    </header>

    <!-- History Panel Modal -->
    <div
      v-if="showHistoryPanel"
      class="fixed inset-0 z-40 flex items-end bg-slate-950/25 px-2 pt-10 animate-fadeIn backdrop-blur-[2px]"
      @click.self="closeHistoryPanel"
    >
      <div class="flex max-h-[82vh] w-full flex-col overflow-hidden rounded-t-[28px] border border-white/80 bg-white/95 shadow-[0_-24px_70px_rgba(15,23,42,0.18)] backdrop-blur">
        <div class="flex justify-center pt-3">
          <span class="h-1.5 w-12 rounded-full bg-slate-200" />
        </div>
        <div class="flex items-start justify-between gap-3 px-4 pb-3 pt-2">
          <div class="min-w-0">
            <p class="text-[11px] font-medium tracking-[0.08em] text-slate-400">本地会话</p>
            <h2 class="mt-1 text-lg font-semibold text-slate-900">聊天历史</h2>
            <p class="mt-1 text-[12px] leading-5 text-slate-500">
              按最近使用排序，可随时恢复之前的对话。
            </p>
          </div>
          <button
            @click="closeHistoryPanel"
            class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-sm text-slate-500 transition hover:border-slate-300 hover:text-slate-700"
            aria-label="关闭历史聊天"
          >
            ✕
          </button>
        </div>
        <div class="flex-1 overflow-y-auto border-t border-slate-100 px-4 pb-4 pt-3">
          <div
            v-if="chatHistories.length === 0"
            class="rounded-[24px] border border-dashed border-slate-200 bg-slate-50/70 px-5 py-10 text-center"
          >
            <p class="text-sm font-medium text-slate-700">还没有历史聊天记录</p>
            <p class="mt-2 text-[12px] leading-5 text-slate-500">
              开始一段新对话后，这里会自动保留最近 20 条记录。
            </p>
          </div>
          <div v-else class="space-y-3">
            <article
              v-for="(history, idx) in chatHistories"
              :key="`${history.timestamp}-${idx}`"
              class="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-3.5 shadow-[0_10px_30px_rgba(15,23,42,0.05)] transition hover:border-slate-300 hover:bg-white"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-[11px] font-medium text-slate-400">{{ formatHistoryTime(history.timestamp) }}</p>
                <span class="shrink-0 rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 ring-1 ring-slate-200/80">
                  {{ history.messageCount }} 条消息
                </span>
              </div>
              <p class="mt-2 break-words text-[13px] font-medium leading-6 text-slate-700">
                {{ normalizeChatHistoryPreview(history.preview) || '这段对话里暂时没有可展示的提问摘要。' }}
              </p>
              <div class="mt-3 flex flex-wrap justify-end gap-2">
                <button
                  @click="restoreHistory(idx)"
                  class="inline-flex min-w-[88px] items-center justify-center rounded-full bg-slate-900 px-3.5 py-1.5 text-[12px] font-medium leading-5 text-white transition hover:bg-slate-800"
                >
                  恢复对话
                </button>
                <button
                  @click="deleteHistory(idx)"
                  class="inline-flex min-w-[88px] items-center justify-center rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-[12px] font-medium leading-5 text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                >
                  删除记录
                </button>
              </div>
            </article>
          </div>
        </div>
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
    <div ref="chatBox" @scroll="handleChatScroll" class="flex-1 space-y-4 overflow-y-auto p-4">
      <div v-for="msg in messages" :key="msg.id"
        class="flex animate-fadeIn" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <div class="max-w-[85%] rounded-2xl px-4 py-3 text-sm"
          :class="msg.role === 'user' ? 'bg-brand text-white rounded-br-sm shadow-md' : 'bg-white text-gray-700 shadow-md rounded-bl-sm'">
          <!-- Assistant Response -->
          <template v-if="msg.role === 'assistant'">
            <div v-if="msg.trace" class="mb-2">
              <button
                v-if="!msg.loading && !isAssistantTraceExpanded(msg.id)"
                @click="toggleAssistantTrace(msg.id)"
                class="group inline-flex max-w-full items-center gap-1.5 rounded-full bg-slate-50/80 px-2.5 py-1 text-[11px] leading-none text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
                :aria-expanded="isAssistantTraceExpanded(msg.id)"
              >
                <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400/70" />
                <span class="truncate">{{ resolveTraceCollapsedLabel(msg.trace) }}</span>
                <span class="text-[13px] leading-none transition group-hover:translate-x-0.5">›</span>
              </button>
              <div
                v-else
                class="rounded-2xl border border-slate-200/70 bg-slate-50/60 px-3 py-2 text-[11px] leading-5 text-slate-500 shadow-[0_8px_24px_rgba(15,23,42,0.03)]"
              >
                <div class="flex items-start justify-between gap-2">
                  <div class="min-w-0">
                    <p class="truncate text-[11px] font-medium text-slate-400">{{ msg.trace.title }}</p>
                    <p class="mt-0.5 text-[12px] font-medium leading-5 text-slate-600">
                      {{ msg.loading ? msg.trace.statusTitle : '已完成分析' }}
                    </p>
                    <p v-if="msg.trace.summary" class="mt-1.5 text-[11px] leading-5 text-slate-500">
                      {{ msg.trace.summary }}
                    </p>
                  </div>
                  <button
                    v-if="!msg.loading"
                    @click="toggleAssistantTrace(msg.id)"
                    class="shrink-0 rounded-full border border-slate-200 bg-white/80 px-2.5 py-0.5 text-[11px] font-medium text-slate-400 transition hover:border-slate-300 hover:text-slate-600"
                  >
                    收起
                  </button>
                  <span
                    v-else
                    class="shrink-0 rounded-full border border-sky-100 bg-sky-50 px-2.5 py-0.5 text-[11px] font-medium text-sky-500"
                  >
                    分析中
                  </span>
                </div>

                <div v-if="msg.trace.metrics.length" class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="metric in msg.trace.metrics"
                    :key="`${metric.label}-${metric.value}`"
                    class="inline-flex items-center gap-1 rounded-full border border-slate-200/80 bg-white/70 px-2 py-0.5 text-[10px] leading-4 text-slate-500"
                  >
                    <span class="text-slate-400">{{ metric.label }}</span>
                    <span class="font-medium text-slate-600">{{ metric.value }}</span>
                  </span>
                </div>

                <div v-if="msg.trace.facts.length" class="mt-2.5 rounded-xl bg-white/55 px-2.5 py-2">
                  <p class="text-[11px] font-medium text-slate-400">依据</p>
                  <ul class="mt-1 space-y-1">
                    <li
                      v-for="(fact, factIndex) in msg.trace.facts"
                      :key="`fact-${factIndex}`"
                      class="flex gap-1.5 break-words text-[11px] leading-5 text-slate-500"
                    >
                      <span class="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-slate-300" />
                      <span>{{ fact }}</span>
                    </li>
                  </ul>
                </div>

                <div v-if="msg.trace.stages.length" class="mt-2.5 space-y-2">
                  <section
                    v-for="stage in msg.trace.stages"
                    :key="stage.id"
                    class="flex gap-2"
                  >
                    <div class="pt-1.5">
                      <span
                        class="block h-1.5 w-1.5 rounded-full"
                        :class="resolveTraceStageDotClass(stage.tone)"
                      />
                    </div>
                    <div class="min-w-0 flex-1">
                      <div class="text-[11px] font-medium text-slate-600">
                        {{ stage.title }}
                      </div>
                      <ul class="mt-1 space-y-1">
                        <li
                          v-for="(item, itemIndex) in stage.items"
                          :key="`${stage.id}-${itemIndex}`"
                          class="flex gap-1.5 break-words text-[11px] leading-5 text-slate-500"
                        >
                          <span class="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-slate-300/90" />
                          <span>{{ item }}</span>
                        </li>
                      </ul>
                    </div>
                  </section>
                </div>
              </div>
            </div>
            <div v-if="msg.content" class="ai-markdown space-y-2" v-html="renderMd(msg.content)" />
            <div v-if="msg.loading && !msg.content" class="flex gap-1">
              <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-400" style="animation-delay: 0ms" />
              <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-400" style="animation-delay: 100ms" />
              <span class="inline-block h-2 w-2 animate-bounce rounded-full bg-gray-400" style="animation-delay: 200ms" />
            </div>
            <div v-if="msg.loading && msg.content" class="mt-2 inline-flex items-center gap-2 rounded-full bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600">
              <span>AI 正在继续整理回复</span>
              <span class="flex gap-1">
                <span class="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style="animation-delay: 0ms" />
                <span class="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style="animation-delay: 120ms" />
                <span class="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style="animation-delay: 240ms" />
              </span>
            </div>
            <div v-if="msg.stopped" class="mt-2 inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700">
              已停止回复
            </div>
            <!-- Smart Options -->
            <div v-if="msg.bookingAssistant?.options?.length" class="mt-3 border-t border-slate-100 pt-2.5">
              <button
                @click="toggleAssistantOptions(msg.id)"
                class="flex w-full items-center justify-between rounded-full bg-slate-50/90 px-2.5 py-1.5 text-[11px] font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <span class="inline-flex items-center gap-1.5">
                  <span class="h-1.5 w-1.5 rounded-full bg-brand/60" />
                  推荐下一步（{{ resolveAssistantOptions(msg.bookingAssistant?.options).length }}）
                </span>
                <span>{{ isAssistantOptionsExpanded(msg.id) ? '收起' : '查看' }}</span>
              </button>
              <div v-if="isAssistantOptionsExpanded(msg.id)" class="mt-2 space-y-1.5">
                <div
                  v-for="(option, optionIndex) in resolveAssistantOptions(msg.bookingAssistant?.options)"
                  :key="`${option.type}-${option.value}-${optionIndex}`"
                  @click="handleAssistantOption(option)"
                  @keydown.enter="handleAssistantOption(option)"
                  tabindex="0"
                  role="button"
                  class="group w-full cursor-pointer rounded-xl border border-slate-200/80 bg-white/80 px-3 py-2.5 text-left transition-all hover:border-brand/30 hover:bg-brand/5 focus:outline-none focus:ring-2 focus:ring-brand/20"
                >
                  <div class="flex items-start gap-2.5">
                    <span
                      class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold"
                      :class="resolveOptionBadgeClass(option)"
                    >
                      {{ getOptionCode(option.type) }}
                    </span>
                    <div class="min-w-0 flex-1">
                      <div :class="isHotelOption(option) ? '' : 'flex items-start justify-between gap-2'">
                        <div class="min-w-0 flex-1">
                          <p
                            :class="isHotelOption(option)
                              ? 'line-clamp-2 text-[13px] font-semibold leading-5 text-slate-700 group-hover:text-brand'
                              : 'text-[12px] font-medium leading-5 text-slate-700 group-hover:text-brand'"
                          >
                            {{ option.label }}
                          </p>
                          <div
                            v-if="isHotelOption(option) && normalizeAssistantOptionHotelMeta(option).length"
                            class="mt-1.5 flex flex-wrap gap-1.5"
                          >
                            <span
                              v-for="meta in normalizeAssistantOptionHotelMeta(option)"
                              :key="`${option.value}-${meta.key}`"
                              class="rounded-full border px-2 py-0.5 text-[10px] font-medium leading-4"
                              :class="meta.tone === 'accent'
                                ? 'border-amber-100 bg-amber-50/90 text-amber-700'
                                : 'border-slate-200 bg-slate-100/80 text-slate-500'"
                            >
                              {{ meta.text }}
                            </span>
                          </div>
                          <p v-else-if="option.description" class="mt-0.5 text-[11px] leading-5 text-slate-500">{{ option.description }}</p>
                        </div>
                        <div v-if="!isHotelOption(option)" class="mt-0.5 flex shrink-0 items-center gap-2 self-start">
                          <span class="text-[15px] leading-none text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand">›</span>
                        </div>
                      </div>
                      <div v-if="normalizeAssistantOptionBadges(option).length" class="mt-1.5 flex flex-wrap gap-1">
                        <span
                          v-for="badge in normalizeAssistantOptionBadges(option)"
                          :key="`${option.value}-${badge}`"
                          class="rounded-full border border-sky-100 bg-sky-50/80 px-2 py-0.5 text-[10px] font-medium leading-4 text-sky-700"
                        >
                          {{ badge }}
                        </span>
                      </div>
                      <ul v-if="normalizeAssistantOptionHighlights(option).length" class="mt-1.5 space-y-0.5">
                        <li
                          v-for="highlight in normalizeAssistantOptionHighlights(option)"
                          :key="`${option.value}-${highlight}`"
                          class="flex gap-1.5 text-[10px] leading-4 text-slate-400"
                        >
                          <span class="mt-[6px] h-1 w-1 shrink-0 rounded-full bg-slate-300" />
                          <span class="break-words">{{ highlight }}</span>
                        </li>
                      </ul>
                      <div class="mt-2 flex items-center justify-between gap-2">
                        <div class="flex flex-wrap items-center gap-1.5 text-[10px]">
                          <span
                            v-if="isRecommendedOption(option)"
                            class="rounded-full bg-brand/10 px-2 py-0.5 font-medium text-brand"
                          >
                            推荐
                          </span>
                          <span
                            v-if="option.requires_confirmation"
                            class="rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-700"
                          >
                            需确认
                          </span>
                          <span v-if="isHotelOption(option)" class="text-slate-400">
                            点击卡片继续选房型
                          </span>
                        </div>
                        <div v-if="isHotelOption(option)" class="flex shrink-0 items-center gap-2">
                          <button
                            @click.stop="openHotelDetail(option)"
                            class="rounded-full border border-brand/20 bg-white/90 px-2.5 py-1 text-[10px] font-medium leading-none text-brand transition hover:bg-brand/10"
                          >
                            查看酒店
                          </button>
                          <span class="text-[15px] leading-none text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand">›</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <!-- User Message -->
          <p v-else class="whitespace-pre-wrap">{{ msg.content }}</p>
        </div>
        <button
          v-if="msg.role === 'user' && msg.sendState === 'failed'"
          @click.stop="retryFailedMessage(msg)"
          class="ml-2 mt-auto flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-red-200 bg-red-50 text-xs font-bold text-red-600 transition hover:bg-red-100"
          title="消息发送失败，点击重发"
        >
          ↻
        </button>
      </div>

      <!-- Empty State Suggestion -->
      <div v-if="messages.length === 1" class="px-2">
        <div class="rounded-2xl bg-white p-4 shadow-sm border border-brand/10">
          <template v-if="isBookingMode">
            <p class="text-xs text-gray-600 leading-relaxed">
              直接告诉我您的订房需求，例如城市、预算、位置或出行场景。
            </p>
            <div class="mt-3 grid gap-1.5 text-[11px] leading-5 text-slate-500">
              <span>我想在上海订个五星酒店</span>
              <span>帮我找近地铁的酒店</span>
              <span>预算500左右，要高评分的</span>
            </div>
          </template>
          <template v-else>
            <p class="text-xs text-gray-600 leading-relaxed">
              可以直接问系统与订单问题，我会先核对当前账号可见信息再回答。
            </p>
            <div class="mt-3 grid gap-1.5 text-[11px] leading-5 text-slate-500">
              <span>怎么取消订单？</span>
              <span>退款大概多久到账？</span>
              <span>我的发票申请到哪一步了？</span>
            </div>
          </template>
        </div>
      </div>
    </div>

    <button
      v-if="showScrollToBottom"
      @click="scrollBottom()"
      class="fixed bottom-24 right-4 z-30 flex h-10 min-w-10 items-center justify-center rounded-full border border-brand/30 bg-white/95 px-3 text-xs font-medium text-brand shadow-lg backdrop-blur transition hover:bg-brand/5"
      title="回到底部"
    >
      ↓ 最新
    </button>

    <!-- Quick Actions -->
    <div v-if="shouldShowQuickActions" class="shrink-0 px-4 pb-2">
      <button
        @click="quickActionsExpanded = !quickActionsExpanded"
        class="mb-2 flex w-full items-center justify-between rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-600"
      >
        <span>快捷问题</span>
        <span>{{ quickActionsExpanded ? '收起' : '展开' }}</span>
      </button>
      <div v-if="quickActionsExpanded" class="flex flex-wrap gap-2">
        <button v-for="q in dynamicQuickQuestions" :key="q" @click="sendMessage(q)"
          class="rounded-full border-2 border-brand/30 px-3 py-1.5 text-xs font-medium text-brand hover:border-brand/60 hover:bg-brand/5 transition-colors">
          {{ q }}
        </button>
      </div>
    </div>

    <!-- Input -->
    <div class="safe-area-bottom shrink-0 border-t border-gray-200 bg-white p-3 shadow-lg">
      <div class="flex gap-2">
        <input v-model="input" @keydown.enter="sendMessage()" @focus="onInputFocus" :placeholder="inputPlaceholder"
          class="flex-1 rounded-2xl border-2 border-gray-200 px-4 py-2.5 text-sm outline-none focus:border-brand transition-colors" />
        <button
          v-if="sending"
          @click="stopGenerating"
          class="flex-shrink-0 rounded-2xl bg-amber-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-amber-600 hover:shadow-lg transition-all"
        >
          停止
        </button>
        <button
          v-else
          @click="sendMessage()"
          :disabled="!input.trim()"
          class="flex-shrink-0 rounded-2xl bg-gradient-to-r from-brand to-brand/90 px-6 py-2.5 text-sm font-medium text-white hover:shadow-lg disabled:opacity-50 transition-all"
        >
          发送
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
import type { AssistantTrace, AssistantTraceStage } from '@hotelink/utils'
import {
  buildChatHistoryPreview,
  normalizeAssistantOptionBadges,
  normalizeAssistantOptionHighlights,
  normalizeAssistantOptionHotelMeta,
  normalizeChatHistoryPreview,
  normalizeAssistantTrace,
  resolveAssistantTypingBurstSize,
  resolveAssistantTypingDelayMs,
  shouldAutoSendEntryAsk,
  splitAssistantStreamText,
} from '@hotelink/utils'
import { useConfirm, useToast } from '@hotelink/ui'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()
const chatBox = ref<HTMLElement | null>(null)
const input = ref('')
const sending = ref(false)
const showMenu = ref(false)
const showHistoryPanel = ref(false)
const showClearConfirm = ref(false)
const chatHistories = ref<ChatHistory[]>([])
const backendSessionId = ref<number | null>(null)
const showScrollToBottom = ref(false)
const quickActionsExpanded = ref(false)
const assistantOptionsExpanded = ref<Record<string, boolean>>({})
const assistantTraceExpanded = ref<Record<string, boolean>>({})
const conversationSummary = ref('')
const activeStreamController = ref<AbortController | null>(null)
const activeUserMessageId = ref<string | null>(null)
const activeAssistantMessageId = ref<string | null>(null)
const activeStreamToken = ref(0)
let activeTypingTimer: number | null = null
let activeTypingQueue: string[] = []
let activeTypingMessageId: string | null = null
let activeTypingResolvers: Array<() => void> = []

interface ChatHistory {
  timestamp: number
  messages: Msg[]
  preview: string
  messageCount: number
  bookingContext: BookingContext
  backendSessionId?: number | null
}

interface BookingContext {
  [key: string]: unknown
  intent?: string
  selected_city?: string | null
  selected_hotel_id?: number | null
}

interface AssistantOption {
  type: string
  label: string
  value: string
  description?: string
  action_type?: string
  target?: string
  params?: Record<string, unknown>
  requires_confirmation?: boolean
  priority?: number
  tracking_id?: string
  source_scene?: string
  badges?: string[]
  highlights?: string[]
  match_reason?: string
  hotel_summary?: Record<string, unknown>
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
  sendState?: 'sending' | 'failed' | 'sent'
  bookingAssistant?: BookingAssistant | null
  trace?: AssistantTrace | null
  stopped?: boolean
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
  extras?: {
    loading?: boolean
    bookingAssistant?: BookingAssistant | null
    trace?: AssistantTrace | null
    sendState?: 'sending' | 'failed' | 'sent'
    stopped?: boolean
  }
): Msg {
  return {
    id: createMsgId(role),
    role,
    content,
    loading: extras?.loading,
    sendState: extras?.sendState,
    bookingAssistant: extras?.bookingAssistant,
    trace: extras?.trace,
    stopped: extras?.stopped,
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
      sendState: record.sendState === 'sending' || record.sendState === 'failed' || record.sendState === 'sent'
        ? record.sendState
        : undefined,
      bookingAssistant: record.bookingAssistant || null,
      trace: normalizeAssistantTrace((record as Record<string, unknown>).trace, record.bookingAssistant || undefined),
      stopped: record.stopped === true ? true : undefined,
    })
  }
  return normalized
}

const BOOKING_PATH = '/ai-booking'
const BOOKING_SESSION_KEY = 'hotelink_ai_booking_chat_state'
const CUSTOMER_SESSION_KEY = 'hotelink_ai_customer_chat_state'
const BOOKING_HISTORY_STORAGE_KEY = 'hotelink_ai_booking_history'
const CUSTOMER_HISTORY_STORAGE_KEY = 'hotelink_ai_customer_history'
const COMPRESS_MESSAGE_THRESHOLD = 24
const COMPRESS_KEEP_RECENT = 10
const SUMMARY_PREFIX = '[对话摘要]'

function isBookingPath(path: string): boolean {
  return path === BOOKING_PATH
}

function resolveScene(path: string): 'booking_assistant' | 'customer_service' {
  return isBookingPath(path) ? 'booking_assistant' : 'customer_service'
}

function resolveSessionKey(path: string): string {
  return isBookingPath(path) ? BOOKING_SESSION_KEY : CUSTOMER_SESSION_KEY
}

function resolveHistoryStorageKey(path: string): string {
  return isBookingPath(path) ? BOOKING_HISTORY_STORAGE_KEY : CUSTOMER_HISTORY_STORAGE_KEY
}

function resolveDefaultWelcome(path: string): string {
  if (isBookingPath(path)) {
    return '我是 HoteLink 的 AI 订房助手。\n\n告诉我城市、预算、位置或出行场景，我会先核对系统在线酒店和房型，再给出可点击的下一步。'
  }
  return '您好，我是 HoteLink 的智能助理。\n\n可以咨询预订、取消、退款、发票、会员权益等问题，我会结合当前账号可见信息为您整理答复。'
}

const isBookingMode = computed(() => isBookingPath(route.path))
const scene = computed(() => resolveScene(route.path))

const pageTitle = computed(() => (isBookingMode.value ? 'AI 订房助手' : 'AI 智能客服'))
const inputPlaceholder = computed(() => (
  isBookingMode.value
    ? '直接描述您的订房需求，我会帮您快速筛选酒店与房型...'
    : '直接咨询订单、退款、发票、会员等问题...'
))

const messages = ref<Msg[]>([
  createMessage('assistant', resolveDefaultWelcome(route.path)),
])

const bookingContext = ref<BookingContext>({})

// 动态快速问题：根据对话进度显示
const dynamicQuickQuestions = computed(() => {
  if (messages.value.length <= 1) {
    if (isBookingMode.value) {
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

watch(shouldShowQuickActions, (visible) => {
  if (visible) {
    quickActionsExpanded.value = false
  }
})

function isAssistantOptionsExpanded(messageId: string): boolean {
  return assistantOptionsExpanded.value[messageId] === true
}

function toggleAssistantOptions(messageId: string) {
  const expanded = !isAssistantOptionsExpanded(messageId)
  assistantOptionsExpanded.value = {
    ...assistantOptionsExpanded.value,
    [messageId]: expanded,
  }
  if (expanded && isNearBottom(260)) {
    scrollBottom()
  }
}

function isAssistantTraceExpanded(messageId: string): boolean {
  return assistantTraceExpanded.value[messageId] === true
}

function setAssistantTraceExpanded(messageId: string, expanded: boolean) {
  assistantTraceExpanded.value = {
    ...assistantTraceExpanded.value,
    [messageId]: expanded,
  }
}

function toggleAssistantTrace(messageId: string) {
  const expanded = !isAssistantTraceExpanded(messageId)
  setAssistantTraceExpanded(messageId, expanded)
}

function attachAssistantTrace(message: Msg, trace: AssistantTrace | null, options?: { expanded?: boolean }) {
  if (!trace) return
  message.trace = trace
  if (options?.expanded === true) {
    setAssistantTraceExpanded(message.id, true)
  }
}

function formatTraceMetric(metric: AssistantTrace['metrics'][number]): string {
  if (metric.label === '需确认') return `${metric.value} 项需确认`
  if (['入口', '城市', '候选酒店', '房型'].includes(metric.label)) {
    return `${metric.value} 个${metric.label}`
  }
  return `${metric.label} ${metric.value}`
}

function resolveTraceCollapsedLabel(trace: AssistantTrace): string {
  const parts = ['已完成分析']
  const primaryMetric = trace.metrics.find((metric) => ['入口', '城市', '候选酒店', '房型'].includes(metric.label))
    || trace.metrics[0]
  if (trace.facts.length) {
    parts.push(`${trace.facts.length} 条依据`)
  }
  if (primaryMetric) {
    parts.push(formatTraceMetric(primaryMetric))
  } else if (trace.stages.length) {
    parts.push(`${trace.stages.length} 步`)
  }
  return parts.join(' · ')
}

function resolveTraceStageDotClass(tone: AssistantTraceStage['tone']): string {
  if (tone === 'lookup') {
    return 'bg-sky-400/70'
  }
  if (tone === 'guardrail') {
    return 'bg-emerald-400/70'
  }
  return 'bg-slate-400/70'
}

function buildConversationSummarySnippet(items: Msg[]): string {
  const lines = items
    .filter((item) => !item.loading && !item.content.startsWith(SUMMARY_PREFIX))
    .map((item) => {
      const roleLabel = item.role === 'user' ? '用户' : '助手'
      const compact = item.content.replace(/\s+/g, ' ').trim().slice(0, 70)
      return `${roleLabel}: ${compact}`
    })
    .filter((line) => line.length > 0)
  return lines.join('\n')
}

function compressConversationIfNeeded() {
  const validMessages = messages.value.filter((item) => !item.loading)
  if (validMessages.length <= COMPRESS_MESSAGE_THRESHOLD) return

  const splitIndex = Math.max(validMessages.length - COMPRESS_KEEP_RECENT, 1)
  const olderMessages = validMessages.slice(0, splitIndex)
  const recentMessages = validMessages.slice(splitIndex)
  const summaryChunk = buildConversationSummarySnippet(olderMessages)
  const previousSummary = conversationSummary.value.trim()
  conversationSummary.value = [previousSummary, summaryChunk].filter(Boolean).join('\n')

  const summaryMessage = createMessage(
    'assistant',
    `${SUMMARY_PREFIX}\n已自动压缩 ${olderMessages.length} 条较早消息，后续会基于摘要继续为你服务。`
  )
  messages.value = [summaryMessage, ...recentMessages]
}

// 用短标签替代 emoji，保持 AI 动作卡片与系统整体风格一致。
function getOptionCode(type: string): string {
  const codeMap: Record<string, string> = {
    'navigate_booking': '订',
    'navigate_hotel': '店',
    'navigate_order_list': '单',
    'navigate_order_detail': '详',
    'navigate_payment': '付',
    'navigate_cancel_order': '退',
    'navigate_invoice': '票',
    'navigate_notification': '知',
    'navigate_help': '?',
    'navigate_ai_booking': '订',
    'navigate_ai_customer_service': '服',
    'navigate_reviews': '评',
    'select_city': '城',
    'select_hotel': '店',
    'select_radius': '距',
    'clarify_poi': '位',
    'select_price': '价',
    'select_rating': '分',
    'select_feature': '选',
    'check_availability': '查',
    'confirm': '确',
  }
  return codeMap[type] || '>'
}

function resolveOptionBadgeClass(option: AssistantOption): string {
  if (option.requires_confirmation) {
    return 'bg-amber-50 text-amber-700 ring-1 ring-amber-100'
  }
  if (isRecommendedOption(option)) {
    return 'bg-brand/10 text-brand ring-1 ring-brand/15'
  }
  return 'bg-slate-100 text-slate-500 ring-1 ring-slate-200/70'
}

function isRecommendedOption(option: AssistantOption): boolean {
  return Number(option.priority ?? 99) <= 25
}

function resolveAssistantOptions(options?: AssistantOption[]): AssistantOption[] {
  if (!Array.isArray(options) || !options.length) return []
  return [...options].sort((a, b) => Number(a.priority ?? 99) - Number(b.priority ?? 99))
}

function resolveOptionRoute(option: AssistantOption): string {
  const target = option.route || option.target
  return typeof target === 'string' ? target : ''
}

function resolveAssistantSceneFromPath(path: string): 'booking_assistant' | 'customer_service' | null {
  if (path === BOOKING_PATH) return 'booking_assistant'
  if (path === '/ai-chat') return 'customer_service'
  return null
}

function resolveOptionQuery(option: AssistantOption): Record<string, string> {
  const query = option.query || option.params || {}
  if (!query || typeof query !== 'object') return {}
  const normalized: Record<string, string> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue
    normalized[key] = String(value)
  }
  return normalized
}

async function confirmBeforeNavigate(option: AssistantOption): Promise<boolean> {
  if (!option.requires_confirmation) return true
  const message = option.type === 'navigate_cancel_order'
    ? '将跳转到订单详情并打开取消流程，确认继续吗？'
    : `将执行「${option.label}」，确认继续吗？`
  return confirmDialog(message)
}

// 焦点时的处理
function onInputFocus() {
  // 可用于显示更多建议或提示
}

function closeHistoryPanel() {
  showHistoryPanel.value = false
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

function saveCurrentChatToHistoryForPath(path: string) {
  if (messages.value.length <= 1) return // 只有欢迎词，不保存

  const userMessages = messages.value.filter(m => m.role === 'user')
  if (userMessages.length === 0) return // 没有用户消息，不保存

  // 历史摘要统一取首条用户诉求，避免抽屉里出现换行、空白和过长文本。
  const preview = buildChatHistoryPreview(messages.value)
  const history: ChatHistory = {
    timestamp: Date.now(),
    messages: [...messages.value],
    preview,
    messageCount: messages.value.length,
    bookingContext: { ...bookingContext.value },
    backendSessionId: backendSessionId.value,
  }

  const existing = loadHistoriesForPath(path)
  existing.unshift(history) // 新聊天放在最前面
  if (existing.length > 20) existing.pop() // 最多保留20条历史

  localStorage.setItem(resolveHistoryStorageKey(path), JSON.stringify(existing))
  if (path === route.path) {
    chatHistories.value = existing
  }
}

// 保存当前聊天到历史
function saveCurrentChatToHistory() {
  saveCurrentChatToHistoryForPath(route.path)
}

function loadHistoriesForPath(path: string): ChatHistory[] {
  const raw = localStorage.getItem(resolveHistoryStorageKey(path))
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

// 从存储加载历史
function loadHistories(): ChatHistory[] {
  return loadHistoriesForPath(route.path)
}

// 恢复历史聊天
function restoreHistory(idx: number) {
  const history = chatHistories.value[idx]
  if (!history) return

  messages.value = normalizeMessages(history.messages).filter(m => !m.loading)
  bookingContext.value = isBookingMode.value ? { ...history.bookingContext } : {}
  backendSessionId.value = Number.isFinite(Number(history.backendSessionId)) ? Number(history.backendSessionId) : null
  assistantTraceExpanded.value = {}
  showHistoryPanel.value = false
  scrollBottom()

  // 关闭菜单
  showMenu.value = false
}

// 删除历史聊天
function deleteHistory(idx: number) {
  const remaining = chatHistories.value.filter((_, i) => i !== idx)
  chatHistories.value = remaining
  localStorage.setItem(resolveHistoryStorageKey(route.path), JSON.stringify(remaining))
}

// 确认清空
function confirmClear() {
  showClearConfirm.value = true
  showMenu.value = false
}

// 清空当前聊天
function clearChat() {
  resetActiveStream({ invalidate: true })
  messages.value = [
    createMessage('assistant', resolveDefaultWelcome(route.path)),
  ]
  bookingContext.value = {}
  backendSessionId.value = null
  conversationSummary.value = ''
  assistantOptionsExpanded.value = {}
  assistantTraceExpanded.value = {}
  quickActionsExpanded.value = false
  input.value = ''
  showClearConfirm.value = false
  scrollBottom()
}

function saveSessionStateForPath(path: string) {
  const payload = {
    messages: messages.value,
    bookingContext: bookingContext.value,
    backendSessionId: backendSessionId.value,
    conversationSummary: conversationSummary.value,
  }
  sessionStorage.setItem(resolveSessionKey(path), JSON.stringify(payload))
}

function saveSessionState() {
  saveSessionStateForPath(route.path)
}

function restoreSessionStateForPath(path: string) {
  const raw = sessionStorage.getItem(resolveSessionKey(path))
  if (!raw) return false
  try {
    const parsed = JSON.parse(raw) as {
      messages?: Msg[]
      bookingContext?: BookingContext
      backendSessionId?: number | null
      conversationSummary?: string
    }
    const restoredMessages = normalizeMessages(parsed.messages)
    if (restoredMessages.length) {
      messages.value = restoredMessages.filter((m) => !m.loading)
    }
    if (parsed.bookingContext && typeof parsed.bookingContext === 'object') {
      bookingContext.value = parsed.bookingContext
    }
    backendSessionId.value = Number.isFinite(Number(parsed.backendSessionId)) ? Number(parsed.backendSessionId) : null
    conversationSummary.value = typeof parsed.conversationSummary === 'string' ? parsed.conversationSummary : ''
    return true
  } catch {
    return false
  }
}

function restoreSessionState() {
  return restoreSessionStateForPath(route.path)
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
  if (!isBookingMode.value) return false
  if (contextPatch) return true
  if (!bookingContext.value.intent) return false
  const value = message.trim()
  if (value.length <= 10) return true
  return ['订', '预订', '房型', '入住', '酒店', '城市', '地点', '地区'].some(keyword => value.includes(keyword))
}

function updateUserSendState(messageId: string, state: 'sending' | 'failed' | 'sent') {
  const target = messages.value.find((item) => item.id === messageId && item.role === 'user')
  if (target) {
    target.sendState = state
  }
}

function getActiveAssistantMessage(): Msg | null {
  const messageId = activeAssistantMessageId.value
  if (!messageId) return null
  return messages.value.find((item) => item.id === messageId && item.role === 'assistant') || null
}

function flushTypingResolvers() {
  if (!activeTypingResolvers.length) return
  const resolvers = [...activeTypingResolvers]
  activeTypingResolvers = []
  for (const resolve of resolvers) {
    resolve()
  }
}

function waitForAssistantTypingDrain(): Promise<void> {
  if (!activeTypingQueue.length && activeTypingTimer === null) {
    return Promise.resolve()
  }
  return new Promise((resolve) => {
    activeTypingResolvers.push(resolve)
  })
}

function clearAssistantTypingState() {
  if (activeTypingTimer !== null) {
    window.clearTimeout(activeTypingTimer)
    activeTypingTimer = null
  }
  activeTypingQueue = []
  activeTypingMessageId = null
  flushTypingResolvers()
}

function runAssistantTypingLoop() {
  if (activeTypingTimer !== null || !activeTypingQueue.length || !activeTypingMessageId) {
    if (!activeTypingQueue.length && activeTypingTimer === null) {
      flushTypingResolvers()
    }
    return
  }

  const pendingCount = activeTypingQueue.length
  activeTypingTimer = window.setTimeout(() => {
    activeTypingTimer = null

    const messageId = activeTypingMessageId
    if (!messageId) {
      flushTypingResolvers()
      return
    }

    const assistantMessage = messages.value.find((item) => item.id === messageId && item.role === 'assistant') || null
    if (!assistantMessage) {
      clearAssistantTypingState()
      return
    }

    const stickToBottom = isNearBottom()
    const burstSize = resolveAssistantTypingBurstSize(activeTypingQueue.length)
    const nextText = activeTypingQueue.splice(0, burstSize).join('')
    assistantMessage.content += nextText

    if (stickToBottom) {
      scrollBottom('auto')
    } else {
      showScrollToBottom.value = true
    }

    if (activeTypingQueue.length) {
      runAssistantTypingLoop()
      return
    }

    flushTypingResolvers()
  }, resolveAssistantTypingDelayMs(pendingCount))
}

// 前端把 SSE chunk 再拆成细粒度字符，模拟类似 ChatGPT 的连续输出体验。
function queueAssistantTyping(messageId: string, chunk: string) {
  const segments = splitAssistantStreamText(chunk)
  if (!segments.length) return
  activeTypingMessageId = messageId
  activeTypingQueue.push(...segments)
  runAssistantTypingLoop()
}

function finalizeInterruptedMessage() {
  const assistantMessage = getActiveAssistantMessage()
  if (!assistantMessage) return
  assistantMessage.loading = false
  assistantMessage.stopped = true
  if (!assistantMessage.content.trim()) {
    assistantMessage.content = '已停止回复'
  }
}

function invalidateActiveStream() {
  activeStreamToken.value += 1
}

function resetActiveStream(options?: { invalidate?: boolean }) {
  if (options?.invalidate) {
    invalidateActiveStream()
  }
  clearAssistantTypingState()
  if (activeUserMessageId.value) {
    updateUserSendState(activeUserMessageId.value, 'sent')
  }
  finalizeInterruptedMessage()
  activeStreamController.value?.abort()
  activeStreamController.value = null
  activeUserMessageId.value = null
  activeAssistantMessageId.value = null
  sending.value = false
}

function stopGenerating() {
  if (!sending.value) return
  clearAssistantTypingState()
  updateUserSendState(activeUserMessageId.value || '', 'sent')
  finalizeInterruptedMessage()
  invalidateActiveStream()
  activeStreamController.value?.abort()
  activeStreamController.value = null
  activeUserMessageId.value = null
  activeAssistantMessageId.value = null
  sending.value = false
  showToast('已停止 AI 回复', 'info')
  scrollBottom()
}

function getDistanceToBottom(): number {
  const el = chatBox.value
  if (!el) return 0
  return el.scrollHeight - el.scrollTop - el.clientHeight
}

function isNearBottom(threshold = 120): boolean {
  return getDistanceToBottom() <= threshold
}

function handleChatScroll() {
  showScrollToBottom.value = !isNearBottom()
}

// 将列表滚动到容器底部
function scrollBottom(behavior: ScrollBehavior = 'smooth') {
  nextTick(() => {
    if (chatBox.value) {
      chatBox.value.scrollTo({ top: chatBox.value.scrollHeight, behavior })
      showScrollToBottom.value = false
    }
  })
}

async function retryFailedMessage(message: Msg) {
  if (message.role !== 'user' || message.sendState !== 'failed' || sending.value) return
  const accepted = await confirmDialog('这条消息发送失败，是否重新发送？')
  if (!accepted) return
  await sendMessage(message.content, undefined, message.id)
}

async function handleAssistantOption(option: AssistantOption) {
  const routePath = resolveOptionRoute(option)
  if (routePath) {
    const optionQuery = resolveOptionQuery(option)
    const targetScene = resolveAssistantSceneFromPath(routePath)
    const hasAskQuery = Boolean(optionQuery.ask && String(optionQuery.ask).trim())
    if (targetScene && targetScene === scene.value && routePath === route.path && !hasAskQuery) {
      showToast(targetScene === 'booking_assistant' ? '当前已在 AI 订房助手' : '当前已在 AI 智能客服', 'info')
      return
    }
    const accepted = await confirmBeforeNavigate(option)
    if (!accepted) return
    await router.push({ path: routePath, query: optionQuery })
    showToast(`已打开「${option.label}」`, 'success')
    return
  }
  if ((option.action_type || '').toLowerCase() === 'send_message') {
    await sendMessage(option.label, option.payload)
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
async function sendMessage(text?: string, contextPatch?: Record<string, unknown>, retryMessageId?: string) {
  const msg = (text || input.value).trim()
  if (!msg || sending.value) return

  let userMessageId = retryMessageId || ''
  if (retryMessageId) {
    const retryMessage = messages.value.find((item) => item.id === retryMessageId && item.role === 'user')
    if (!retryMessage) return
    updateUserSendState(retryMessageId, 'sending')
  } else {
    compressConversationIfNeeded()
    const userMessage = createMessage('user', msg, { sendState: 'sending' })
    messages.value.push(userMessage)
    userMessageId = userMessage.id
    scrollBottom()
  }
  activeUserMessageId.value = userMessageId

  const carryBookingContext = isBookingMode.value && shouldCarryBookingContext(msg, contextPatch)
  const nextBookingContext = carryBookingContext ? mergeBookingContext(contextPatch) : undefined
  input.value = ''

  // Loading placeholder until first token arrives
  const placeholderMessage = createMessage('assistant', '', { loading: true })
  messages.value.push(placeholderMessage)
  activeAssistantMessageId.value = placeholderMessage.id
  clearAssistantTypingState()
  scrollBottom()
  sending.value = true
  const requestToken = activeStreamToken.value + 1
  activeStreamToken.value = requestToken
  const controller = new AbortController()
  activeStreamController.value = controller

  let receivedAny = false
  let pendingBookingAssistant: BookingAssistant | null = null
  let pendingAssistantTrace: AssistantTrace | null = null

  try {
    for await (const event of userAiApi.chatStream({
      scene: scene.value,
      question: msg,
      hotel_id: nextBookingContext?.selected_hotel_id || undefined,
      session_id: backendSessionId.value || undefined,
      booking_context: isBookingMode.value ? nextBookingContext : undefined,
      conversation_summary: conversationSummary.value || undefined,
    }, { signal: controller.signal })) {
      if (requestToken !== activeStreamToken.value) return
      if (event.type === 'meta') {
        // 先消费元数据，保证过程卡片和快捷动作能先于正文显示。
        pendingBookingAssistant = event.booking_assistant && typeof event.booking_assistant === 'object'
          ? event.booking_assistant as unknown as BookingAssistant
          : null
        const incomingSessionId = Number(event.session_id)
        if (Number.isFinite(incomingSessionId) && incomingSessionId > 0) {
          backendSessionId.value = incomingSessionId
        }
        if (isBookingMode.value && pendingBookingAssistant?.context) {
          bookingContext.value = { ...pendingBookingAssistant.context }
        }
        pendingAssistantTrace = normalizeAssistantTrace(event.agent_state, pendingBookingAssistant)
        const assistantMessage = getActiveAssistantMessage()
        if (assistantMessage) {
          assistantMessage.bookingAssistant = pendingBookingAssistant
          attachAssistantTrace(assistantMessage, pendingAssistantTrace, { expanded: assistantMessage.loading === true })
          scrollBottom('auto')
        }
        continue
      }

      const chunk = typeof event.content === 'string' ? event.content : ''
      const isDone = event.done === true || event.type === 'done'
      const incomingSessionId = Number(event.session_id)
      if (Number.isFinite(incomingSessionId) && incomingSessionId > 0) {
        backendSessionId.value = incomingSessionId
      }
      const assistantMessage = getActiveAssistantMessage()
      if (!assistantMessage) throw new Error('missing assistant message')
      assistantMessage.bookingAssistant = pendingBookingAssistant
      attachAssistantTrace(assistantMessage, pendingAssistantTrace)
      if (chunk) {
        receivedAny = true
        queueAssistantTyping(assistantMessage.id, chunk)
      }
      if (isDone) {
        await waitForAssistantTypingDrain()
        assistantMessage.loading = false
        if (assistantMessage.trace) {
          setAssistantTraceExpanded(assistantMessage.id, false)
        }
        break
      }
    }
    const assistantMessage = getActiveAssistantMessage()
    const hasInteractivePayload = !!assistantMessage?.bookingAssistant?.options?.length || !!assistantMessage?.trace
    if ((!receivedAny && !hasInteractivePayload) || !assistantMessage) throw new Error('no reply')
    assistantMessage.loading = false
    assistantMessage.bookingAssistant = pendingBookingAssistant
    attachAssistantTrace(assistantMessage, pendingAssistantTrace)
    if (!assistantMessage.content.trim() && !assistantMessage.bookingAssistant?.options?.length) {
      assistantMessage.content = '我先把可确认的信息整理到这里，您可以继续补充问题。'
    }
    updateUserSendState(userMessageId, 'sent')
    if (!isBookingMode.value || (!pendingBookingAssistant && !carryBookingContext)) {
      bookingContext.value = {}
    }
  } catch (err) {
    if (requestToken !== activeStreamToken.value) return
    if (err instanceof DOMException && err.name === 'AbortError') {
      finalizeInterruptedMessage()
      updateUserSendState(userMessageId, 'sent')
      showToast('已停止 AI 回复', 'info')
      return
    }
    if (receivedAny) {
      await waitForAssistantTypingDrain()
    }
    if (!receivedAny) {
      messages.value.pop()
    } else {
      const assistantMessage = getActiveAssistantMessage()
      if (assistantMessage) {
        assistantMessage.loading = false
        attachAssistantTrace(assistantMessage, pendingAssistantTrace)
        if (!assistantMessage.content.trim()) {
          assistantMessage.content = '抱歉，这次回复中断了，请重试。'
        }
      }
    }
    updateUserSendState(userMessageId, 'failed')
    showToast('消息发送失败，可点击右侧重发', 'warning')
    if (!isBookingMode.value || !carryBookingContext) {
      bookingContext.value = {}
    }
  } finally {
    if (requestToken === activeStreamToken.value) {
      sending.value = false
    }
    if (activeStreamToken.value === requestToken) {
      clearAssistantTypingState()
      activeStreamController.value = null
      activeUserMessageId.value = null
      activeAssistantMessageId.value = null
    }
    scrollBottom()
  }
}

function initializeCurrentModeState() {
  resetActiveStream({ invalidate: true })
  const restored = restoreSessionState()
  if (!restored) {
    messages.value = [createMessage('assistant', resolveDefaultWelcome(route.path))]
    bookingContext.value = {}
    backendSessionId.value = null
    conversationSummary.value = ''
  }
  if (!isBookingMode.value) {
    bookingContext.value = {}
  }
  assistantOptionsExpanded.value = {}
  assistantTraceExpanded.value = {}
  quickActionsExpanded.value = false
  chatHistories.value = loadHistories()
  showScrollToBottom.value = false
}

async function consumeAskQueryIfNeeded() {
  const ask = typeof route.query.ask === 'string' ? route.query.ask.trim() : ''
  if (!ask) return
  const askMode = typeof route.query.ask_mode === 'string' ? route.query.ask_mode.trim() : ''
  // 首页引导问题只在“欢迎语 + 空会话”时自动发送，避免覆盖用户已有聊天上下文。
  const canAutoSend = askMode !== 'new_only' || shouldAutoSendEntryAsk({
    messages: messages.value,
    backendSessionId: backendSessionId.value,
    conversationSummary: conversationSummary.value,
    bookingContext: bookingContext.value,
  })
  if (canAutoSend) {
    await sendMessage(ask)
  }
  const nextQuery = { ...route.query }
  delete nextQuery.ask
  delete nextQuery.ask_mode
  await router.replace({ path: route.path, query: nextQuery })
}

onMounted(async () => {
  initializeCurrentModeState()
  scrollBottom()
  await consumeAskQueryIfNeeded()
  window.addEventListener('beforeunload', handleBeforeUnload)
})

watch(() => route.path, async (nextPath, prevPath) => {
  if (nextPath === prevPath) return
  resetActiveStream({ invalidate: true })
  saveCurrentChatToHistoryForPath(prevPath)
  saveSessionStateForPath(prevPath)
  showMenu.value = false
  showHistoryPanel.value = false
  showClearConfirm.value = false
  input.value = ''
  initializeCurrentModeState()
  scrollBottom()
  await consumeAskQueryIfNeeded()
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

onBeforeUnmount(() => {
  resetActiveStream({ invalidate: true })
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

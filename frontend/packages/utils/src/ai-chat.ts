export interface AssistantTraceStage {
  id: string
  title: string
  items: string[]
  tone: 'analysis' | 'lookup' | 'guardrail'
}

export interface AssistantTraceMetric {
  label: string
  value: string
}

export interface AssistantTrace {
  mode: string
  title: string
  statusTitle: string
  summary: string
  facts: string[]
  metrics: AssistantTraceMetric[]
  stages: AssistantTraceStage[]
}

interface RawAssistantTraceItem {
  id: string
  title?: string
  label?: string
  content?: string
  detail?: string
  description?: string
}

const TRACE_FACT_LIMIT = 4
const TRACE_METRIC_LIMIT = 4
const TRACE_STAGE_ITEM_LIMIT = 3
const OPTION_DETAIL_LIMIT = 3
const HISTORY_PREVIEW_LIMIT = 72
const HOTEL_OPTION_META_LIMIT = 4
const HOTEL_OPTION_DESCRIPTION_PATTERN = /^(?<city>[^|]+?)\s*\|\s*(?<star>\d+)星\s*\|\s*评分(?<rating>\d+(?:\.\d+)?)\s*\|\s*¥?(?<price>\d+(?:\.\d+)?)起/u

export interface AssistantOptionMetaChip {
  key: 'city' | 'star' | 'rating' | 'price'
  text: string
  tone: 'default' | 'accent'
}

export interface AssistantEntryAskState {
  messages?: Array<{ role?: unknown; content?: unknown }>
  backendSessionId?: unknown
  conversationSummary?: unknown
  bookingContext?: unknown
}

function normalizeString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function normalizeDisplayScalar(value: unknown): string {
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return ''
}

function normalizeStringArray(raw: unknown, limit: number): string[] {
  if (!Array.isArray(raw)) return []

  const result: string[] = []
  const seen = new Set<string>()
  for (const item of raw) {
    const value = normalizeString(item)
    if (!value || seen.has(value)) continue
    seen.add(value)
    result.push(value)
    if (result.length >= limit) break
  }
  return result
}

function hasMeaningfulObjectValue(raw: unknown): boolean {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return false

  return Object.values(raw as Record<string, unknown>).some((value) => {
    if (typeof value === 'string') return value.trim().length > 0
    if (typeof value === 'number') return Number.isFinite(value)
    if (typeof value === 'boolean') return value
    if (Array.isArray(value)) return value.length > 0
    return value !== null && value !== undefined
  })
}

function normalizeAssistantOptionHotelSummary(raw: unknown): {
  city: string
  star: string
  rating: string
  minPrice: string
} | null {
  if (!raw || typeof raw !== 'object') return null

  const record = raw as Record<string, unknown>
  const city = normalizeDisplayScalar(record.city)
  const star = normalizeDisplayScalar(record.star)
  const rating = normalizeDisplayScalar(record.rating)
  const minPrice = normalizeDisplayScalar(record.min_price ?? record.minPrice)
  if (!city || !star || !rating || !minPrice) {
    return null
  }

  return {
    city,
    star,
    rating,
    minPrice,
  }
}

function parseAssistantOptionHotelSummary(description: unknown): {
  city: string
  star: string
  rating: string
  minPrice: string
} | null {
  const normalized = normalizeString(description)
  if (!normalized) return null

  const match = HOTEL_OPTION_DESCRIPTION_PATTERN.exec(normalized)
  if (!match?.groups) return null

  return {
    city: normalizeString(match.groups.city),
    star: normalizeString(match.groups.star),
    rating: normalizeString(match.groups.rating),
    minPrice: normalizeString(match.groups.price),
  }
}

function normalizeTraceFacts(raw: unknown): string[] {
  if (!Array.isArray(raw)) return []
  return raw.map((item) => normalizeString(item)).filter(Boolean).slice(0, TRACE_FACT_LIMIT)
}

function normalizeTraceMetrics(raw: unknown): AssistantTraceMetric[] {
  if (!Array.isArray(raw)) return []

  return raw.flatMap((item) => {
    if (!item || typeof item !== 'object') return []
    const record = item as Record<string, unknown>
    const label = normalizeString(record.label)
    const value = normalizeString(record.value)
    if (!label || !value) return []
    return [{ label, value }]
  }).slice(0, TRACE_METRIC_LIMIT)
}

function normalizeStageItems(raw: unknown): RawAssistantTraceItem[] {
  if (!Array.isArray(raw)) return []

  return raw.flatMap((item) => {
    if (!item || typeof item !== 'object') return []
    const record = item as Record<string, unknown>
    return [{
      id: normalizeString(record.id) || `${normalizeString(record.title) || normalizeString(record.label)}:${normalizeString(record.content) || normalizeString(record.detail) || normalizeString(record.description)}`,
      title: normalizeString(record.title),
      label: normalizeString(record.label),
      content: normalizeString(record.content),
      detail: normalizeString(record.detail),
      description: normalizeString(record.description),
    }]
  })
}

function normalizeTraceStage(raw: unknown): AssistantTraceStage | null {
  if (!raw || typeof raw !== 'object') return null
  const record = raw as Record<string, unknown>
  const title = normalizeString(record.title)
  const tone = normalizeString(record.tone)
  const items = Array.isArray(record.items)
    ? record.items.map((item) => normalizeString(item)).filter(Boolean)
    : []

  if (!title || !items.length) return null

  return {
    id: normalizeString(record.id) || title,
    title,
    items: items.slice(0, TRACE_STAGE_ITEM_LIMIT),
    tone: tone === 'lookup' || tone === 'guardrail' ? tone : 'analysis',
  }
}

function normalizeStoredTrace(raw: unknown): AssistantTrace | null {
  if (!raw || typeof raw !== 'object') return null
  const record = raw as Record<string, unknown>
  const looksStoredTrace = Array.isArray(record.stages)
    || typeof record.title === 'string'
    || typeof record.statusTitle === 'string'
  if (!looksStoredTrace) return null

  const stages = Array.isArray(record.stages)
    ? record.stages
        .map((item) => normalizeTraceStage(item))
        .filter((item): item is AssistantTraceStage => item !== null)
    : []

  const summary = normalizeString(record.summary)
  if (!summary && !stages.length) return null

  return {
    mode: normalizeString(record.mode),
    title: normalizeString(record.title),
    statusTitle: normalizeString(record.statusTitle),
    summary,
    facts: normalizeTraceFacts(record.facts),
    metrics: normalizeTraceMetrics(record.metrics),
    stages,
  }
}

function buildTraceStage(
  id: string,
  title: string,
  tone: AssistantTraceStage['tone'],
  rawItems: RawAssistantTraceItem[],
  selectors: Array<(item: RawAssistantTraceItem) => string>,
): AssistantTraceStage | null {
  const items = rawItems
    .map((item) => {
      for (const selector of selectors) {
        const value = selector(item)
        if (value) return value
      }
      return ''
    })
    .filter(Boolean)
    .slice(0, TRACE_STAGE_ITEM_LIMIT)

  if (!items.length) return null

  return {
    id,
    title,
    tone,
    items,
  }
}

function resolveAssistantTraceStatusTitle(mode: string, phase: string): string {
  if (mode === 'booking_assistant') {
    if (phase === 'switch_to_customer_service') return '正在切换到客服助手'
    if (phase === 'select_room_type') return '正在整理可预订房型'
    if (phase === 'select_hotel') return '正在筛选符合需求的酒店'
    if (phase === 'select_city') return '正在理解用户需求'
    return '正在收集相关信息和服务'
  }

  if (phase === 'quick_actions') {
    return '正在收集相关信息和服务'
  }
  return '正在理解用户需求'
}

/**
 * Normalize the backend trace payload into a compact UI model.
 *
 * @param raw - Raw `agent_state` payload emitted by the backend stream meta event.
 * @param bookingAssistant - Optional structured booking-assistant payload from the same meta event.
 * @returns A user-facing trace model, or `null` when the payload has no meaningful content.
 */
export function normalizeAssistantTrace(
  raw: unknown,
  bookingAssistant?: { phase?: unknown } | null,
): AssistantTrace | null {
  const stored = normalizeStoredTrace(raw)
  if (stored) return stored

  if (!raw || typeof raw !== 'object') return null

  const record = raw as Record<string, unknown>
  const mode = normalizeString(record.mode)
  const title = normalizeString(record.display_name) || normalizeString(record.displayName)
  const summary = normalizeString(record.summary)
  const phase = normalizeString(record.phase) || normalizeString(bookingAssistant?.phase)

  const thinking = normalizeStageItems(record.thinking)
  const toolSteps = normalizeStageItems(record.tool_steps ?? record.toolSteps)
  const guardrails = normalizeStageItems(record.guardrails)
  const facts = normalizeTraceFacts(record.facts)
  const metrics = normalizeTraceMetrics(record.metrics)

  const stages = [
    buildTraceStage(
      'thinking',
      '理解需求并拆解工作',
      'analysis',
      thinking,
      [(item) => item.content || '', (item) => item.title || ''],
    ),
    buildTraceStage(
      'tool_steps',
      '正在收集相关信息和服务',
      'lookup',
      toolSteps,
      [(item) => item.detail || '', (item) => item.label || ''],
    ),
    buildTraceStage(
      'guardrails',
      '处理边界与确认条件',
      'guardrail',
      guardrails,
      [(item) => item.description || '', (item) => item.label || ''],
    ),
  ].filter((item): item is AssistantTraceStage => item !== null)

  if (!summary && !stages.length) return null

  return {
    mode,
    title: title || (mode === 'booking_assistant' ? 'AI 订房助手' : 'AI 智能客服'),
    statusTitle: resolveAssistantTraceStatusTitle(mode, phase),
    summary,
    facts,
    metrics,
    stages,
  }
}

/**
 * Split stream text into rendering-safe characters for the typewriter effect.
 *
 * @param text - Raw chunk text received from the SSE stream.
 * @returns Characters that can be appended incrementally to the visible response.
 */
export function splitAssistantStreamText(text: string): string[] {
  return Array.from(text || '')
}

/**
 * Decide how many characters to reveal per animation frame.
 *
 * @param pendingCount - Current number of buffered characters waiting to render.
 * @returns The next burst size for the typewriter loop.
 */
export function resolveAssistantTypingBurstSize(pendingCount: number): number {
  if (pendingCount >= 120) return 6
  if (pendingCount >= 60) return 4
  if (pendingCount >= 24) return 3
  if (pendingCount >= 8) return 2
  return 1
}

/**
 * Decide the delay between typewriter frames.
 *
 * @param pendingCount - Current number of buffered characters waiting to render.
 * @returns Frame delay in milliseconds.
 */
export function resolveAssistantTypingDelayMs(pendingCount: number): number {
  if (pendingCount >= 120) return 6
  if (pendingCount >= 60) return 10
  if (pendingCount >= 24) return 14
  if (pendingCount >= 8) return 18
  return 24
}

/**
 * Normalize assistant option badges for compact action-card rendering.
 *
 * @param option - Raw assistant option returned by `booking_assistant.options[]`.
 * @returns Short, de-duplicated badges that can be displayed as chips.
 */
export function normalizeAssistantOptionBadges(option: { badges?: unknown } | null | undefined): string[] {
  return normalizeStringArray(option?.badges, OPTION_DETAIL_LIMIT)
}

/**
 * Normalize assistant option evidence lines without exposing internal prompts.
 *
 * @param option - Raw assistant option returned by `booking_assistant.options[]`.
 * @returns User-facing evidence lines such as distance or matched tag hints.
 */
export function normalizeAssistantOptionHighlights(
  option: { highlights?: unknown; match_reason?: unknown } | null | undefined,
): string[] {
  const highlights = normalizeStringArray(option?.highlights, OPTION_DETAIL_LIMIT)
  const reason = normalizeString(option?.match_reason)
  if (!reason || highlights.includes(reason)) {
    return highlights
  }
  return [reason, ...highlights].slice(0, OPTION_DETAIL_LIMIT)
}

/**
 * Normalize hotel option metadata into wrap-safe chips for mobile recommendation cards.
 *
 * @param option - Raw assistant option returned by `booking_assistant.options[]`.
 * @returns Ordered metadata chips for city, star, rating, and reference price.
 */
export function normalizeAssistantOptionHotelMeta(
  option: { hotel_summary?: unknown; description?: unknown } | null | undefined,
): AssistantOptionMetaChip[] {
  const summary = normalizeAssistantOptionHotelSummary(option?.hotel_summary)
    || parseAssistantOptionHotelSummary(option?.description)
  if (!summary) return []

  const chips: AssistantOptionMetaChip[] = [
    { key: 'city', text: summary.city, tone: 'default' },
    { key: 'star', text: `${summary.star}星`, tone: 'default' },
    { key: 'rating', text: `评分${summary.rating}`, tone: 'default' },
    { key: 'price', text: `¥${summary.minPrice}起`, tone: 'accent' },
  ]
  return chips.slice(0, HOTEL_OPTION_META_LIMIT)
}

/**
 * Decide whether an entry ask should auto-send into the current assistant session.
 *
 * @param state - Local session snapshot for the current assistant page.
 * @returns `true` only when the conversation is still a fresh welcome state.
 */
export function shouldAutoSendEntryAsk(state: AssistantEntryAskState | null | undefined): boolean {
  const backendSessionId = Number(state?.backendSessionId)
  if (Number.isFinite(backendSessionId) && backendSessionId > 0) {
    return false
  }
  if (normalizeString(state?.conversationSummary)) {
    return false
  }
  if (hasMeaningfulObjectValue(state?.bookingContext)) {
    return false
  }

  const messages = Array.isArray(state?.messages)
    ? state.messages.filter((message) => message && typeof message === 'object')
    : []
  if (!messages.length) {
    return true
  }
  if (messages.length > 1) {
    return false
  }

  return normalizeString(messages[0]?.role) === 'assistant'
}

/**
 * Normalize a chat-history preview into a compact single-paragraph summary.
 *
 * @param preview - Raw preview text captured from a local chat history item.
 * @param maxLength - Maximum number of visible characters to keep.
 * @returns A trimmed preview suitable for compact history cards.
 */
export function normalizeChatHistoryPreview(
  preview: unknown,
  maxLength = HISTORY_PREVIEW_LIMIT,
): string {
  const normalized = normalizeString(preview).replace(/\s+/g, ' ').trim()
  if (!normalized) return ''

  const safeLimit = Math.max(12, Math.floor(Number(maxLength) || HISTORY_PREVIEW_LIMIT))
  if (normalized.length <= safeLimit) {
    return normalized
  }
  return `${normalized.slice(0, safeLimit).trimEnd()}...`
}

/**
 * Build a local-history preview from the first meaningful user message.
 *
 * @param messages - Stored chat messages from the current local session.
 * @param maxLength - Maximum number of visible characters to keep.
 * @returns A compact preview for history drawers and restore lists.
 */
export function buildChatHistoryPreview(
  messages: Array<{ role?: unknown; content?: unknown }>,
  maxLength = HISTORY_PREVIEW_LIMIT,
): string {
  const preview = messages.find((message) => normalizeString(message?.role) === 'user' && normalizeString(message?.content))
  return normalizeChatHistoryPreview(preview?.content, maxLength)
}

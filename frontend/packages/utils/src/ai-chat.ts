export interface AssistantTraceStage {
  id: string
  title: string
  items: string[]
  tone: 'analysis' | 'lookup' | 'guardrail'
}

export interface AssistantTrace {
  mode: string
  title: string
  statusTitle: string
  summary: string
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

function normalizeString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
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
    items,
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

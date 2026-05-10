import { describe, expect, it } from 'vitest'

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
} from './ai-chat'

describe('ai chat helpers', () => {
  it('normalizes booking trace payloads into display stages', () => {
    const trace = normalizeAssistantTrace({
      mode: 'booking_assistant',
      display_name: 'AI 订房助手',
      summary: '已锁定杭州，并按预算≤500元筛选，返回 3 个系统在线候选酒店。',
      facts: ['城市：杭州', '筛选条件：预算≤500元', '返回候选酒店：西湖店、滨江店、武林店'],
      metrics: [
        { label: '候选酒店', value: '3' },
        { label: '预算', value: '≤500' },
      ],
      thinking: [
        {
          id: 'extract-booking-slots',
          title: '提取订房条件',
          content: '已从当前消息和会话上下文提取：城市 杭州、预算≤500元。',
        },
      ],
      tool_steps: [
        {
          id: 'load-online-hotels',
          label: '查询在线酒店与房型',
          detail: '仅读取系统公开展示的在线酒店、房型与参考价格信息。',
        },
      ],
      guardrails: [
        {
          id: 'ownership',
          label: '查询范围受限',
          description: '只读取当前登录用户的订房上下文，以及系统公开展示的在线酒店、房型和价格信息。',
        },
      ],
    }, {
      phase: 'select_hotel',
    })

    expect(trace?.title).toBe('AI 订房助手')
    expect(trace?.statusTitle).toBe('正在筛选符合需求的酒店')
    expect(trace?.facts[0]).toBe('城市：杭州')
    expect(trace?.metrics[0]).toEqual({ label: '候选酒店', value: '3' })
    expect(trace?.stages[0].title).toBe('理解需求并拆解工作')
    expect(trace?.stages[1].items[0]).toContain('系统公开展示')
    expect(trace?.stages[2].tone).toBe('guardrail')
  })

  it('normalizes customer-service trace payloads and stored traces', () => {
    const liveTrace = normalizeAssistantTrace({
      mode: 'customer_service',
      display_name: 'AI 智能客服',
      summary: '已识别为取消订单诉求；关联订单 #12；整理了 4 个可执行入口。',
      facts: ['问题类型：取消订单', '订单范围：优先订单 #12', '可用入口：查看订单详情、取消订单'],
      metrics: [
        { label: '入口', value: '4' },
        { label: '订单', value: '#12' },
      ],
      thinking: [
        { id: 'classify-request', title: '识别问题类型', content: '先判断这是订单、支付、发票还是评价问题。' },
      ],
      tool_steps: [
        { id: 'load-user-context', label: '读取当前账号上下文', detail: '只读取当前账号最近订单、通知与评价作为参考。' },
      ],
    }, {
      phase: 'quick_actions',
    })

    expect(liveTrace?.statusTitle).toBe('正在收集相关信息和服务')
    expect(liveTrace?.facts).toContain('问题类型：取消订单')
    expect(liveTrace?.metrics[1]).toEqual({ label: '订单', value: '#12' })

    const storedTrace = normalizeAssistantTrace({
      mode: 'customer_service',
      title: 'AI 智能客服',
      statusTitle: '已完成分析',
      summary: '已保存的分析过程',
      facts: ['已保存依据'],
      metrics: [{ label: '入口', value: '2' }],
      stages: [
        {
          id: 'thinking',
          title: '理解需求并拆解工作',
          items: ['识别问题类型'],
          tone: 'analysis',
        },
      ],
    })

    expect(storedTrace?.summary).toBe('已保存的分析过程')
    expect(storedTrace?.facts).toEqual(['已保存依据'])
    expect(storedTrace?.metrics).toEqual([{ label: '入口', value: '2' }])
    expect(storedTrace?.stages).toHaveLength(1)
  })

  it('splits unicode stream text and adjusts typing speed by backlog size', () => {
    expect(splitAssistantStreamText('Hi🙂酒店')).toEqual(['H', 'i', '🙂', '酒', '店'])
    expect(resolveAssistantTypingBurstSize(4)).toBe(1)
    expect(resolveAssistantTypingBurstSize(80)).toBe(4)
    expect(resolveAssistantTypingDelayMs(4)).toBe(24)
    expect(resolveAssistantTypingDelayMs(140)).toBe(6)
  })

  it('keeps trace payloads compact and ignores non-display prompt fields', () => {
    const trace = normalizeAssistantTrace({
      mode: 'customer_service',
      display_name: 'AI 智能客服',
      summary: '已根据当前账号可见信息完成分析。',
      system_prompt: '这段系统提示词不能进入界面',
      facts: ['依据1', '依据2', '依据3', '依据4', '依据5'],
      metrics: [
        { label: '入口', value: '4' },
        { label: '订单', value: '#12' },
        { label: '需确认', value: '1' },
        { label: '通知', value: '2' },
        { label: '额外', value: '不展示' },
      ],
      thinking: [
        { id: 'a', content: '步骤1' },
        { id: 'b', content: '步骤2' },
        { id: 'c', content: '步骤3' },
        { id: 'd', content: '步骤4' },
      ],
    })

    expect(trace?.facts).toEqual(['依据1', '依据2', '依据3', '依据4'])
    expect(trace?.metrics).toHaveLength(4)
    expect(trace?.stages[0].items).toEqual(['步骤1', '步骤2', '步骤3'])
    expect(JSON.stringify(trace)).not.toContain('系统提示词')
  })

  it('normalizes assistant option evidence for compact cards', () => {
    const option = {
      badges: ['1.2km', '龙翔桥站', '1.2km', '', '额外不展示'],
      highlights: ['距龙翔桥站约1.20km（直线参考）', '标签/地址命中：近地铁'],
      match_reason: '距龙翔桥站约1.20km（直线参考）',
    }

    expect(normalizeAssistantOptionBadges(option)).toEqual(['1.2km', '龙翔桥站', '额外不展示'])
    expect(normalizeAssistantOptionHighlights(option)).toEqual([
      '距龙翔桥站约1.20km（直线参考）',
      '标签/地址命中：近地铁',
    ])
    expect(normalizeAssistantOptionHighlights({
      highlights: ['标签/地址命中：近地铁'],
      match_reason: '距凤起路站约0.80km（直线参考）',
    })).toEqual([
      '距凤起路站约0.80km（直线参考）',
      '标签/地址命中：近地铁',
    ])
  })

  it('normalizes hotel option metadata into mobile-safe chips', () => {
    expect(normalizeAssistantOptionHotelMeta({
      hotel_summary: {
        city: '杭州',
        star: 5,
        rating: '4.7',
        min_price: '1329.00',
      },
    })).toEqual([
      { key: 'city', text: '杭州', tone: 'default' },
      { key: 'star', text: '5星', tone: 'default' },
      { key: 'rating', text: '评分4.7', tone: 'default' },
      { key: 'price', text: '¥1329.00起', tone: 'accent' },
    ])

    expect(normalizeAssistantOptionHotelMeta({
      description: '杭州 | 4星 | 评分4.8 | ¥784.00起 | 距钱江路站约5.05km',
    })).toEqual([
      { key: 'city', text: '杭州', tone: 'default' },
      { key: 'star', text: '4星', tone: 'default' },
      { key: 'rating', text: '评分4.8', tone: 'default' },
      { key: 'price', text: '¥784.00起', tone: 'accent' },
    ])
  })

  it('builds compact local-history previews from user messages', () => {
    expect(buildChatHistoryPreview([
      { role: 'assistant', content: '欢迎使用 HoteLink' },
      { role: 'user', content: '  帮我找一下   杭州西湖附近  \n 适合商务出行的酒店  ' },
    ], 18)).toBe('帮我找一下 杭州西湖附近 适合商务出...')

    expect(buildChatHistoryPreview([
      { role: 'assistant', content: '只有欢迎语' },
    ])).toBe('')

    expect(normalizeChatHistoryPreview('  第一行\n第二行\t第三行  ', 40)).toBe('第一行 第二行 第三行')
  })

  it('auto-sends entry asks only for fresh conversations', () => {
    expect(shouldAutoSendEntryAsk({
      messages: [{ role: 'assistant', content: '欢迎使用 HoteLink AI' }],
      backendSessionId: null,
      conversationSummary: '',
      bookingContext: {},
    })).toBe(true)

    expect(shouldAutoSendEntryAsk({
      messages: [
        { role: 'assistant', content: '欢迎使用 HoteLink AI' },
        { role: 'user', content: '我想订上海的酒店' },
      ],
      backendSessionId: null,
      conversationSummary: '',
      bookingContext: {},
    })).toBe(false)

    expect(shouldAutoSendEntryAsk({
      messages: [{ role: 'assistant', content: '欢迎使用 HoteLink AI' }],
      backendSessionId: 88,
      conversationSummary: '',
      bookingContext: {},
    })).toBe(false)

    expect(shouldAutoSendEntryAsk({
      messages: [{ role: 'assistant', content: '欢迎使用 HoteLink AI' }],
      backendSessionId: null,
      conversationSummary: '',
      bookingContext: { selected_city: '上海' },
    })).toBe(false)
  })
})

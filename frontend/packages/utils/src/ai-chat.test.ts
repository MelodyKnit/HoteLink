import { describe, expect, it } from 'vitest'

import {
  normalizeAssistantTrace,
  resolveAssistantTypingBurstSize,
  resolveAssistantTypingDelayMs,
  splitAssistantStreamText,
} from './ai-chat'

describe('ai chat helpers', () => {
  it('normalizes booking trace payloads into display stages', () => {
    const trace = normalizeAssistantTrace({
      mode: 'booking_assistant',
      display_name: 'AI 订房助手',
      summary: '我会先识别城市、酒店和偏好条件，再只基于系统在线酒店与房型数据给出下一步。',
      thinking: [
        {
          id: 'extract-booking-slots',
          title: '提取订房条件',
          content: '识别城市、酒店关键词、预算、评分和地理位置偏好。',
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
    expect(trace?.stages[0].title).toBe('理解需求并拆解工作')
    expect(trace?.stages[1].items[0]).toContain('系统公开展示')
    expect(trace?.stages[2].tone).toBe('guardrail')
  })

  it('normalizes customer-service trace payloads and stored traces', () => {
    const liveTrace = normalizeAssistantTrace({
      mode: 'customer_service',
      display_name: 'AI 智能客服',
      summary: '我会先核对当前账号可用的订单与通知，再给出解释。',
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

    const storedTrace = normalizeAssistantTrace({
      mode: 'customer_service',
      title: 'AI 智能客服',
      statusTitle: '已完成分析',
      summary: '已保存的分析过程',
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
    expect(storedTrace?.stages).toHaveLength(1)
  })

  it('splits unicode stream text and adjusts typing speed by backlog size', () => {
    expect(splitAssistantStreamText('Hi🙂酒店')).toEqual(['H', 'i', '🙂', '酒', '店'])
    expect(resolveAssistantTypingBurstSize(4)).toBe(1)
    expect(resolveAssistantTypingBurstSize(80)).toBe(4)
    expect(resolveAssistantTypingDelayMs(4)).toBe(24)
    expect(resolveAssistantTypingDelayMs(140)).toBe(6)
  })
})

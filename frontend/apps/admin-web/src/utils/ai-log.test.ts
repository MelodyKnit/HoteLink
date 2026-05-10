import { describe, expect, it } from 'vitest'

import {
  AI_LOG_SOURCE_LABELS,
  AI_LOG_STATUS_LABELS,
  getAiLogStatusClass,
} from './ai-log'

describe('ai log helpers', () => {
  it('exposes labels for the new truthful observability statuses', () => {
    expect(AI_LOG_STATUS_LABELS.fallback).toBe('兜底')
    expect(AI_LOG_STATUS_LABELS.rule_based).toBe('规则')
    expect(AI_LOG_SOURCE_LABELS.rule_engine).toBe('规则引擎')
  })

  it('maps fallback and rule-based statuses to distinct badge styles', () => {
    expect(getAiLogStatusClass('fallback')).toContain('amber')
    expect(getAiLogStatusClass('rule_based')).toContain('sky')
    expect(getAiLogStatusClass('unknown')).toContain('slate')
  })
})

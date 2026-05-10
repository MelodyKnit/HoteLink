export const AI_LOG_STATUS_LABELS: Record<string, string> = {
  success: '成功',
  fallback: '兜底',
  rule_based: '规则',
  failed: '失败',
  timeout: '超时',
  quota_exceeded: '配额超限',
}

export const AI_LOG_SOURCE_LABELS: Record<string, string> = {
  llm: '模型生成',
  fallback: '兜底结果',
  rule_engine: '规则引擎',
}

/**
 * Resolve badge classes for AI log statuses without duplicating page-local mappings.
 */
export function getAiLogStatusClass(status: string): string {
  if (status === 'success') return 'bg-green-100 text-green-700'
  if (status === 'fallback') return 'bg-amber-100 text-amber-700'
  if (status === 'rule_based') return 'bg-sky-100 text-sky-700'
  if (status === 'failed') return 'bg-red-100 text-red-700'
  if (status === 'timeout') return 'bg-orange-100 text-orange-700'
  if (status === 'quota_exceeded') return 'bg-fuchsia-100 text-fuchsia-700'
  return 'bg-slate-100 text-slate-700'
}

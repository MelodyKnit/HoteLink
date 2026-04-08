<template>
  <!-- 取消/退款分支：单独展示 -->
  <div v-if="isCancelledBranch" class="w-full">
    <!-- 第一行：圆点 + 连线 -->
    <div class="flex items-center">
      <template v-for="(step, i) in normalSteps" :key="step.key">
        <div
          class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold"
          :class="isPassedInCancelled(i)
            ? 'border-slate-300 bg-slate-100 text-slate-400'
            : 'border-slate-200 bg-white text-slate-300'"
        >
          <svg v-if="isPassedInCancelled(i)" class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <div v-if="i < normalSteps.length - 1" class="mx-1 h-0.5 flex-1 bg-slate-200" />
      </template>
    </div>
    <!-- 第二行：标签（与圆点等宽对齐） -->
    <div class="mt-2 flex items-start">
      <template v-for="(step, i) in normalSteps" :key="step.key">
        <div class="w-8 flex-shrink-0 text-center text-[11px] leading-tight text-slate-400">{{ step.label }}</div>
        <div v-if="i < normalSteps.length - 1" class="mx-1 flex-1" />
      </template>
    </div>

    <!-- 取消/退款状态标签 -->
    <div class="mt-3 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-2.5">
      <span class="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-sm">✕</span>
      <div>
        <span class="text-sm font-semibold" :class="status === 'refunded' ? 'text-orange-600' : 'text-red-600'">
          {{ BRANCH_LABEL[status] || '已取消' }}
        </span>
        <span v-if="cancelledAt" class="ml-2 text-xs text-slate-400">{{ cancelledAt }}</span>
      </div>
    </div>
  </div>

  <!-- 正常流程 -->
  <div v-else class="w-full">
    <!-- 第一行：圆点 + 连线（items-center 保证严格水平对齐） -->
    <div class="flex items-center">
      <template v-for="(step, i) in normalSteps" :key="step.key">
        <!-- 圆点 -->
        <div
          class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold transition-all duration-300"
          :class="[stepClass(i), stepState(i) === 'current' ? 'ring-pulse' : '']"
        >
          <svg v-if="stepState(i) === 'done'" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <!-- 连线 -->
        <div
          v-if="i < normalSteps.length - 1"
          class="mx-1.5 h-0.5 flex-1 transition-all duration-500"
          :class="currentIndex > i ? 'bg-teal-400' : 'bg-slate-200'"
        />
      </template>
    </div>

    <!-- 第二行：标签 + 时间戳（与圆点等宽对齐，flex-1 spacer 对应连线） -->
    <div class="mt-2 flex items-start">
      <template v-for="(step, i) in normalSteps" :key="step.key">
        <div class="w-9 flex-shrink-0 flex flex-col items-center">
          <span
            class="text-center text-[11px] font-medium leading-tight"
            :class="stepState(i) === 'done' ? 'text-teal-600' : stepState(i) === 'current' ? 'text-teal-700 font-semibold' : 'text-slate-400'"
          >{{ step.label }}</span>
          <span
            v-if="timestamps?.[step.key] && stepState(i) !== 'upcoming'"
            class="mt-0.5 text-[10px] text-slate-400 text-center leading-tight"
          >{{ formatTs(timestamps[step.key]) }}</span>
        </div>
        <div v-if="i < normalSteps.length - 1" class="mx-1.5 flex-1" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
interface Props {
  status: string
  timestamps?: Record<string, string | undefined>
}
const props = withDefaults(defineProps<Props>(), { timestamps: undefined })

const normalSteps = [
  { key: 'pending_payment', label: '待支付' },
  { key: 'paid',            label: '已支付' },
  { key: 'confirmed',       label: '已确认' },
  { key: 'checked_in',      label: '已入住' },
  { key: 'completed',       label: '已完成' },
]

const BRANCH_LABEL: Record<string, string> = {
  cancelled:  '已取消',
  refunding:  '退款中',
  refunded:   '已退款',
}

const CANCELLED_BRANCHES = new Set(['cancelled', 'refunding', 'refunded'])

const isCancelledBranch = computed(() => CANCELLED_BRANCHES.has(props.status))

// 取消时"已通过"的步骤索引（到 paid 为止）
function isPassedInCancelled(i: number) {
  const passedKeys = new Set(['paid', 'confirmed', 'checked_in', 'completed'])
  if (props.status === 'cancelled') {
    // cancelled: 只保留在取消前已完成的状态
    // 判断：如果有 paid_at 就说明 paid 已过
    if (normalSteps[i].key === 'pending_payment') return true
    if (normalSteps[i].key === 'paid' && props.timestamps?.paid) return true
    if (normalSteps[i].key === 'confirmed' && props.timestamps?.confirmed) return true
    return false
  }
  return passedKeys.has(normalSteps[i].key)
}

const cancelledAt = computed(() => {
  const ts = props.timestamps?.cancelled || props.timestamps?.refunding || props.timestamps?.refunded
  return ts ? formatTs(ts) : ''
})

// 当前步骤在 normalSteps 中的索引
const currentIndex = computed(() => {
  const idx = normalSteps.findIndex(s => s.key === props.status)
  // 若状态不在正常流程中，按最后完成的往后推
  return idx >= 0 ? idx : normalSteps.length
})

type StepState = 'done' | 'current' | 'upcoming'

function stepState(i: number): StepState {
  if (i < currentIndex.value) return 'done'
  if (i === currentIndex.value) return 'current'
  return 'upcoming'
}

function stepClass(i: number): string {
  const s = stepState(i)
  if (s === 'done')    return 'border-teal-400 bg-teal-400 text-white'
  if (s === 'current') return 'border-teal-500 bg-white text-teal-600 shadow-md shadow-teal-100'
  return 'border-slate-200 bg-white text-slate-300'
}

function formatTs(ts: string | undefined): string {
  if (!ts) return ''
  // 兼容 ISO 8601 带微秒和时区偏移，只保留 MM-DD HH:mm
  // 例：2026-04-08T11:33:07.673390+08:00 → 04-08 11:33
  const match = ts.match(/\d{4}-(\d{2}-\d{2})[T ](\d{2}:\d{2})/)
  return match ? `${match[1]} ${match[2]}` : ts.slice(5, 16)
}
</script>

<style scoped>
/* box-shadow 脉冲：不影响盒模型，不会触发 overflow 滚动条，不被父级 overflow 裁剪 */
@keyframes ring-pulse {
  0%   { box-shadow: 0 0 0 0px rgba(45, 212, 191, 0.5); }
  60%  { box-shadow: 0 0 0 9px rgba(45, 212, 191, 0);   }
  100% { box-shadow: 0 0 0 0px rgba(45, 212, 191, 0);   }
}
.ring-pulse {
  animation: ring-pulse 1.6s ease-out infinite;
}
</style>

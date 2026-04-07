<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  modelValue?: string | number | null
  size?: 'sm' | 'md'
}>(), { size: 'md' })

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  'change': []
}>()

// ── State ─────────────────────────────────────────────────────────────────────
const isOpen = ref(false)
const containerRef = ref<HTMLDivElement>()
const hiddenSelectRef = ref<HTMLSelectElement>()
const parsedOptions = ref<{ value: string; label: string; disabled: boolean }[]>([])

// ── Option parsing (reads from hidden native <select>) ─────────────────────────
function readOptions() {
  if (!hiddenSelectRef.value) return
  parsedOptions.value = Array.from(hiddenSelectRef.value.options).map(opt => ({
    value: opt.value,
    label: opt.text,
    disabled: opt.disabled,
  }))
}

let mutationObserver: MutationObserver | null = null

// ── Lifecycle ──────────────────────────────────────────────────────────────────
onMounted(() => {
  readOptions()
  if (hiddenSelectRef.value) {
    mutationObserver = new MutationObserver(readOptions)
    mutationObserver.observe(hiddenSelectRef.value, {
      childList: true,
      subtree: true,
      characterData: true,
    })
  }
  document.addEventListener('mousedown', onClickOutside)
})

onUnmounted(() => {
  mutationObserver?.disconnect()
  document.removeEventListener('mousedown', onClickOutside)
})

// ── Computed ───────────────────────────────────────────────────────────────────
const selectedLabel = computed(() => {
  const val = String(props.modelValue ?? '')
  return parsedOptions.value.find(o => o.value === val)?.label ?? ''
})

// ── Handlers ───────────────────────────────────────────────────────────────────
function toggle() {
  isOpen.value = !isOpen.value
}

function choose(value: string) {
  emit('update:modelValue', value)
  emit('change')
  isOpen.value = false
}

function onClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') isOpen.value = false
}

// ── Container class ────────────────────────────────────────────────────────────
const containerClass = computed(() => (attrs as Record<string, unknown>).class ?? '')

import { useAttrs } from 'vue'
const attrs = useAttrs()
</script>

<template>
  <div ref="containerRef" :class="['relative', containerClass]">

    <!-- Hidden native <select> — used only for option parsing via MutationObserver -->
    <select
      ref="hiddenSelectRef"
      class="sr-only pointer-events-none"
      tabindex="-1"
      aria-hidden="true"
    >
      <slot />
    </select>

    <!-- Visible trigger button -->
    <button
      type="button"
      :class="[
        'flex w-full items-center justify-between rounded-lg border bg-white text-left',
        'transition-all duration-150 outline-none',
        isOpen
          ? 'border-brand ring-2 ring-brand/20'
          : 'border-gray-200 hover:border-gray-300',
        size === 'sm' ? 'px-3 py-1.5 text-sm' : 'px-3 py-2 text-sm',
      ]"
      @click="toggle"
      @keydown="onKeyDown"
    >
      <span :class="selectedLabel ? 'text-gray-700' : 'text-gray-400 italic'">
        {{ selectedLabel || '请选择…' }}
      </span>
      <!-- Chevron arrow — rotates when open -->
      <svg
        :class="[
          'ml-2 h-3.5 w-3.5 flex-shrink-0 transition-transform duration-200',
          isOpen ? 'rotate-180 text-brand' : 'text-gray-400',
        ]"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fill-rule="evenodd"
          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>

    <!-- Dropdown panel -->
    <Transition
      enter-active-class="transition duration-100 ease-out origin-top"
      enter-from-class="opacity-0 scale-y-95"
      enter-to-class="opacity-100 scale-y-100"
      leave-active-class="transition duration-75 ease-in origin-top"
      leave-from-class="opacity-100 scale-y-100"
      leave-to-class="opacity-0 scale-y-95"
    >
      <div
        v-if="isOpen"
        class="absolute left-0 top-full z-50 mt-1 w-full min-w-max overflow-hidden rounded-xl bg-white shadow-lg ring-1 ring-black/5"
        role="listbox"
      >
        <div class="max-h-56 overflow-y-auto py-1">
          <button
            v-for="opt in parsedOptions"
            :key="opt.value"
            type="button"
            role="option"
            :disabled="opt.disabled"
            :aria-selected="opt.value === String(modelValue)"
            :class="[
              'flex w-full items-center gap-2 px-3 py-2 text-sm transition-colors',
              opt.disabled
                ? 'cursor-not-allowed text-gray-300'
                : 'cursor-pointer',
              !opt.disabled && opt.value === String(modelValue)
                ? 'bg-brand/10 font-medium text-brand'
                : !opt.disabled
                  ? 'text-gray-700 hover:bg-gray-50'
                  : '',
            ]"
            @click="!opt.disabled && choose(opt.value)"
          >
            <!-- Checkmark for selected option -->
            <svg
              v-if="opt.value === String(modelValue)"
              class="h-3.5 w-3.5 flex-shrink-0 text-brand"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <span v-else class="w-3.5 flex-shrink-0" />
            {{ opt.label }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

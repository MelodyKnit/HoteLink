<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue: string
  available: string[]
  occupied: string[]
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isOpen = ref(false)
const containerRef = ref<HTMLDivElement>()

const filtered = computed(() => {
  const q = props.modelValue.trim().toLowerCase()
  const matchAvail = props.available.filter(r => !q || r.toLowerCase().includes(q))
  const matchOccup = props.occupied.filter(r => !q || r.toLowerCase().includes(q))
  return { available: matchAvail, occupied: matchOccup }
})

const hasItems = computed(() => filtered.value.available.length + filtered.value.occupied.length > 0)

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
  isOpen.value = true
}

function pick(room: string) {
  emit('update:modelValue', room)
  isOpen.value = false
}

function onFocus() {
  isOpen.value = true
}

function onClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<template>
  <div ref="containerRef" class="relative">
    <input
      :value="modelValue"
      :placeholder="placeholder || '例如：1808'"
      required
      autocomplete="off"
      class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
      @input="onInput"
      @focus="onFocus"
      @keydown.escape="isOpen = false"
    />
    <ul
      v-if="isOpen && hasItems"
      class="absolute z-50 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
    >
      <li v-if="filtered.available.length" class="px-3 py-1 text-xs font-semibold text-slate-400">空闲房间</li>
      <li
        v-for="r in filtered.available"
        :key="r"
        class="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-teal-50"
        @mousedown.prevent="pick(r)"
      >
        <span class="inline-block h-2 w-2 rounded-full bg-green-500" />
        <span>{{ r }}</span>
      </li>
      <li v-if="filtered.occupied.length" class="mt-1 border-t border-slate-100 px-3 py-1 text-xs font-semibold text-slate-400">已占用</li>
      <li
        v-for="r in filtered.occupied"
        :key="'occ-'+r"
        class="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm text-slate-400 hover:bg-red-50"
        @mousedown.prevent="pick(r)"
      >
        <span class="inline-block h-2 w-2 rounded-full bg-red-400" />
        <span class="line-through">{{ r }}</span>
      </li>
    </ul>
  </div>
</template>

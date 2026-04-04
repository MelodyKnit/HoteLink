<template>
  <div v-if="totalPages > 1" class="mt-4 flex items-center justify-between text-sm text-slate-500">
    <span>共 {{ total }} 条，第 {{ page }} / {{ totalPages }} 页</span>
    <div class="flex gap-1">
      <button
        class="rounded-lg border border-slate-200 px-3 py-1 transition-colors hover:bg-slate-100 disabled:opacity-40"
        :disabled="page <= 1"
        @click="$emit('change', page - 1)"
      >上一页</button>
      <button
        class="rounded-lg border border-slate-200 px-3 py-1 transition-colors hover:bg-slate-100 disabled:opacity-40"
        :disabled="page >= totalPages"
        @click="$emit('change', page + 1)"
      >下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

defineEmits<{ change: [page: number] }>()

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))
</script>

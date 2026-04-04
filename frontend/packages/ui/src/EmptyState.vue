<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <p class="text-4xl">📭</p>
    <p class="mt-3 text-sm text-slate-500">{{ message || '暂无数据' }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ message?: string }>()
</script>

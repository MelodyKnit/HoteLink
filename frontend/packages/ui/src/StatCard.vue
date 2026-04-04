<template>
  <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
    <div class="flex items-center justify-between">
      <p class="text-sm font-medium text-slate-500">{{ title }}</p>
      <span v-if="icon" class="text-xl">{{ icon }}</span>
    </div>
    <p class="mt-2 text-2xl font-bold text-slate-900">{{ value }}</p>
    <p v-if="subtitle" class="mt-1 text-xs text-slate-400">{{ subtitle }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  subtitle?: string
  icon?: string
}>()
</script>

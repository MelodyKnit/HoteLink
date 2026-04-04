<template>
  <div class="overflow-x-auto">
    <table class="w-full text-left text-sm">
      <thead>
        <tr class="border-b border-slate-200 text-xs font-semibold uppercase text-slate-500">
          <th v-for="col in columns" :key="col.key" class="px-4 py-3 whitespace-nowrap">{{ col.label }}</th>
          <th v-if="$slots.actions" class="px-4 py-3">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading" class="border-b border-slate-100">
          <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-8 text-center text-slate-400">加载中…</td>
        </tr>
        <tr v-else-if="!rows.length" class="border-b border-slate-100">
          <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-8 text-center text-slate-400">暂无数据</td>
        </tr>
        <tr v-for="(row, idx) in rows" :key="idx"
          class="border-b border-slate-100 transition-colors hover:bg-slate-50">
          <td v-for="col in columns" :key="col.key" class="px-4 py-3 whitespace-nowrap">
            <slot :name="'col-' + col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] ?? '-' }}
            </slot>
          </td>
          <td v-if="$slots.actions" class="px-4 py-3">
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  columns: { key: string; label: string }[]
  rows: Record<string, unknown>[]
  loading?: boolean
}>()
</script>

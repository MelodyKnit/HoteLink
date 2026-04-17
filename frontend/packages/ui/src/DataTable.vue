<template>
  <div class="overflow-x-auto">
    <table class="w-full min-w-max text-left text-sm">
      <thead>
        <tr class="border-b border-slate-200 text-xs font-semibold uppercase text-slate-500">
          <th
            v-for="col in columns"
            :key="col.key"
            class="whitespace-nowrap"
            :class="compact ? 'px-3 py-2.5' : 'px-4 py-3'"
          >
            <div v-if="col.sortField" class="flex select-none items-center gap-0.5">
              <button class="transition-colors hover:text-slate-700" @click="toggleSort(col.sortField)">{{ col.label }}</button>
              <div class="ml-0 flex flex-col leading-none">
                <button
                  class="text-[6px] leading-[6px] transition-colors"
                  :class="isSortActive(col.sortField, 'asc') ? 'text-teal-600' : 'text-slate-300 hover:text-slate-500'"
                  title="升序"
                  @click.stop="handleSort(col.sortField, 'asc')"
                >
                  ▲
                </button>
                <button
                  class="text-[6px] leading-[6px] transition-colors"
                  :class="isSortActive(col.sortField, 'desc') ? 'text-teal-600' : 'text-slate-300 hover:text-slate-500'"
                  title="降序"
                  @click.stop="handleSort(col.sortField, 'desc')"
                >
                  ▼
                </button>
              </div>
            </div>
            <span v-else>{{ col.label }}</span>
          </th>
          <th
            v-if="$slots.actions"
            class="whitespace-nowrap text-right"
            :class="compact ? 'w-[72px] px-2.5 py-2.5' : 'w-[92px] px-4 py-3'"
          >操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading" class="border-b border-slate-100">
          <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-8 text-center text-slate-400">加载中…</td>
        </tr>
        <tr v-else-if="!rows.length" class="border-b border-slate-100">
          <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-8 text-center text-slate-400">暂无数据</td>
        </tr>
        <tr v-for="(row, idx) in rows" :key="idx" class="border-b border-slate-100 transition-colors hover:bg-slate-50">
          <td
            v-for="col in columns"
            :key="col.key"
            class="whitespace-nowrap"
            :class="compact ? 'px-3 py-2.5' : 'px-4 py-3'"
          >
            <slot :name="'col-' + col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] ?? '-' }}
            </slot>
          </td>
          <td
            v-if="$slots.actions"
            class="whitespace-nowrap text-right"
            :class="compact ? 'w-[72px] px-2.5 py-2.5' : 'w-[92px] px-4 py-3'"
          >
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  columns: { key: string; label: string; sortField?: string }[]
  rows: Record<string, unknown>[]
  loading?: boolean
  sortValue?: string
  compact?: boolean
}>()

const compact = props.compact ?? false

const emit = defineEmits<{
  'sort-change': [value: string]
}>()

type SortDirection = 'asc' | 'desc'

function isSortActive(field: string, direction: SortDirection): boolean {
  const expected = direction === 'asc' ? field : `-${field}`
  return props.sortValue === expected
}

function handleSort(field: string, direction: SortDirection) {
  const nextOrdering = direction === 'asc' ? field : `-${field}`
  if (nextOrdering === props.sortValue) return
  emit('sort-change', nextOrdering)
}

function toggleSort(field: string) {
  if (props.sortValue === field) {
    handleSort(field, 'desc')
    return
  }
  handleSort(field, 'asc')
}
</script>

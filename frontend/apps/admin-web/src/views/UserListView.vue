<template>
  <section>
    <PageHeader title="用户管理" subtitle="管理平台注册用户" />

    <div class="mb-4 flex flex-wrap gap-3">
      <input v-model="keyword" placeholder="用户名/手机号/昵称" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="loadList" />
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-avatar="{ value }">
          <img v-if="value" :src="String(value)" class="h-8 w-8 rounded-full object-cover" />
          <span v-else class="inline-block h-8 w-8 rounded-full bg-slate-200" />
        </template>
        <template #col-gender="{ value }">{{ value === 'male' ? '男' : value === 'female' ? '女' : '未知' }}</template>
        <template #col-role="{ value }">
          <StatusBadge :label="value === 'admin' ? '管理员' : '普通用户'" :type="value === 'admin' ? 'info' : 'default'" />
        </template>
        <template #col-status="{ value }">
          <StatusBadge :label="value === 'active' ? '正常' : '禁用'" :type="value === 'active' ? 'success' : 'danger'" />
        </template>
        <template #actions="{ row }">
          <button v-if="row.status === 'active'" class="text-sm text-red-600 hover:underline" @click="changeStatus(row, 'disabled')">禁用</button>
          <button v-else class="text-sm text-green-600 hover:underline" @click="changeStatus(row, 'active')">启用</button>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '@hotelink/api'
import { PageHeader, DataTable, StatusBadge, Pagination } from '@hotelink/ui'

const columns = [
  { key: 'avatar', label: '头像' },
  { key: 'username', label: '用户名' },
  { key: 'nickname', label: '昵称' },
  { key: 'mobile', label: '手机号' },
  { key: 'gender', label: '性别' },
  { key: 'role', label: '角色' },
  { key: 'member_level', label: '会员等级' },
  { key: 'points', label: '积分' },
  { key: 'status', label: '状态' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
  if (keyword.value) params.keyword = keyword.value
  const res = await userApi.list(params)
  if (res.code === 0 && res.data) {
    const d = res.data as unknown as { items: Record<string, unknown>[]; total: number }
    list.value = d.items || []
    total.value = d.total || 0
  }
  loading.value = false
}

// 处理 changeStatus 业务流程。
async function changeStatus(row: Record<string, unknown>, status: string) {
  const label = status === 'active' ? '启用' : '禁用'
  if (!confirm(`确认${label}该用户？`)) return
  await userApi.changeStatus({ user_id: row.id as number, status })
  loadList()
}

onMounted(loadList)
</script>

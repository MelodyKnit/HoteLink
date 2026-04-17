<template>
  <section>
    <PageHeader title="用户管理" subtitle="管理平台注册用户" />

    <div class="mb-4 flex flex-wrap gap-3">
      <input v-model="keyword" placeholder="用户名/手机号/昵称" class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500" @keyup.enter="loadList" />
      <SelectField v-model="ordering" size="sm" @change="onSortChange">
        <option value="-id">ID 最新优先</option>
        <option value="id">ID 最旧优先</option>
        <option value="user__username">用户名 A→Z</option>
        <option value="-user__username">用户名 Z→A</option>
        <option value="nickname">昵称 A→Z</option>
        <option value="-nickname">昵称 Z→A</option>
        <option value="mobile">手机号升序</option>
        <option value="-mobile">手机号降序</option>
        <option value="gender">性别升序</option>
        <option value="-gender">性别降序</option>
        <option value="role">角色升序</option>
        <option value="-role">角色降序</option>
        <option value="member_level">会员等级升序</option>
        <option value="-member_level">会员等级降序</option>
        <option value="points">积分从低到高</option>
        <option value="-points">积分从高到低</option>
        <option value="status">状态升序</option>
        <option value="-status">状态降序</option>
      </SelectField>
      <button class="rounded-lg bg-slate-100 px-3 py-2 text-sm hover:bg-slate-200" @click="loadList">搜索</button>
    </div>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading" :sort-value="ordering" @sort-change="onTableSortChange">
        <template #col-avatar="{ value }">
          <img v-if="value" :src="String(value)" class="h-8 w-8 rounded-full object-cover" />
          <span v-else class="inline-block h-8 w-8 rounded-full bg-slate-200" />
        </template>
        <template #col-gender="{ value }">{{ value === 'male' ? '男' : value === 'female' ? '女' : '未知' }}</template>
        <template #col-role="{ value }">
          <StatusBadge
            :label="value === 'system_admin' ? '系统管理员' : value === 'hotel_admin' ? '酒店管理员' : '普通用户'"
            :type="value === 'system_admin' ? 'info' : value === 'hotel_admin' ? 'info' : 'default'"
          />
        </template>
        <template #col-member_level="{ value }">
          {{ memberLevelMap[String(value)] || value }}
        </template>
        <template #col-status="{ value }">
          <StatusBadge :label="value === 'active' ? '正常' : '禁用'" :type="value === 'active' ? 'success' : 'danger'" />
        </template>
        <template #actions="{ row }">
          <div class="flex gap-2">
            <button class="text-sm text-teal-600 hover:underline" @click="openEdit(row)">编辑</button>
            <button v-if="row.status === 'active'" class="text-sm text-red-600 hover:underline" @click="changeStatus(row, 'disabled')">禁用</button>
            <button v-else class="text-sm text-green-600 hover:underline" @click="changeStatus(row, 'active')">启用</button>
            <button class="text-sm text-amber-600 hover:underline" @click="resetPassword(row)">重置密码</button>
          </div>
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <ModalDialog :visible="showEdit" title="编辑用户" size="md" @close="showEdit = false">
      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium">昵称</label>
          <input v-model="editForm.nickname" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="请输入昵称" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">手机号</label>
          <input v-model="editForm.mobile" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="选填，填写 11 位手机号" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">会员等级</label>
          <SelectField v-model="editForm.member_level" class="w-full">
            <option value="normal">普通会员</option>
            <option value="silver">银卡会员</option>
            <option value="gold">金卡会员</option>
            <option value="platinum">铂金会员</option>
            <option value="diamond">钻石会员</option>
          </SelectField>
        </div>
      </div>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showEdit = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="handleEdit">保存</button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { userApi } from '@hotelink/api'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, SelectField, useToast, useConfirm } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

const columns = [
  { key: 'avatar', label: '头像' },
  { key: 'username', label: '用户名', sortField: 'user__username' },
  { key: 'nickname', label: '昵称', sortField: 'nickname' },
  { key: 'mobile', label: '手机号', sortField: 'mobile' },
  { key: 'gender', label: '性别', sortField: 'gender' },
  { key: 'role', label: '角色', sortField: 'role' },
  { key: 'member_level', label: '会员等级', sortField: 'member_level' },
  { key: 'points', label: '积分', sortField: 'points' },
  { key: 'status', label: '状态', sortField: 'status' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const ordering = ref('-id')

const memberLevelMap: Record<string, string> = {
  normal: '普通会员', silver: '银卡会员', gold: '金卡会员', platinum: '铂金会员', diamond: '钻石会员',
}

function patchUserRow(userId: number, patch: Record<string, unknown>) {
  list.value = list.value.map((item) => (Number(item.id) === userId ? { ...item, ...patch } : item))
}

function onSortChange() {
  page.value = 1
  loadList()
}

function onTableSortChange(nextOrdering: string) {
  if (ordering.value === nextOrdering) return
  ordering.value = nextOrdering
  onSortChange()
}

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value, ordering: ordering.value }
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
  if (!await confirmDialog(`确认${label}该用户？`, { type: status === 'active' ? 'warning' : 'danger' })) return
  try {
    const res = await userApi.changeStatus({ user_id: row.id as number, status })
    if (res.code === 0) {
      showToast(`用户已${label}`, 'success')
      patchUserRow(row.id as number, { status })
    } else {
      showToast(res.message || `${label}失败`, 'error')
    }
  } catch {
    showToast(`${label}失败，请重试`, 'error')
  }
}

const showEdit = ref(false)
const editForm = reactive({ user_id: 0, nickname: '', mobile: '', member_level: 'normal' })

function openEdit(row: Record<string, unknown>) {
  editForm.user_id = row.id as number
  editForm.nickname = String(row.nickname || '')
  editForm.mobile = String(row.mobile || '')
  editForm.member_level = String(row.member_level || 'normal')
  showEdit.value = true
}

async function handleEdit() {
  try {
    const res = await userApi.update(editForm)
    if (res.code === 0) {
      showToast('用户信息已更新', 'success')
      showEdit.value = false
      patchUserRow(editForm.user_id, {
        member_level: editForm.member_level,
        mobile: editForm.mobile,
        nickname: editForm.nickname,
      })
    } else {
      showToast(res.message || '更新失败', 'error')
    }
  } catch {
    showToast('更新失败，请重试', 'error')
  }
}

async function resetPassword(row: Record<string, unknown>) {
  if (!await confirmDialog(`确认将「${row.nickname || row.username}」的密码重置为 Abc123456？`, { type: 'warning' })) return
  try {
    const res = await userApi.resetPassword(row.id as number)
    if (res.code === 0) {
      showToast('密码已重置为 Abc123456', 'success')
    } else {
      showToast(res.message || '重置失败', 'error')
    }
  } catch {
    showToast('重置失败，请重试', 'error')
  }
}

onMounted(loadList)
</script>

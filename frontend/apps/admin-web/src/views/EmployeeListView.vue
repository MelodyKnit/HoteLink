<template>
  <section>
    <PageHeader title="员工管理" subtitle="管理系统管理员和酒店管理员账号">
      <template #actions>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreate">添加员工</button>
      </template>
    </PageHeader>

    <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <DataTable :columns="columns" :rows="list" :loading="loading">
        <template #col-role="{ value }">
          <StatusBadge :label="value === 'system_admin' ? '系统管理员' : value === 'hotel_admin' ? '酒店管理员' : String(value)" :type="value === 'system_admin' ? 'info' : 'default'" />
        </template>
        <template #col-status="{ value }">
          <StatusBadge :label="value === 'active' ? '正常' : '禁用'" :type="value === 'active' ? 'success' : 'danger'" />
        </template>
      </DataTable>
      <Pagination :page="page" :page-size="pageSize" :total="total" class="px-4 pb-4" @change="p => { page = p; loadList() }" />
    </div>

    <ModalDialog :visible="showCreate" title="添加员工" size="md" @close="showCreate = false">
      <form class="space-y-4" @submit.prevent="handleCreate">
        <div>
          <label class="mb-1 block text-sm font-medium">用户名</label>
          <input v-model="form.username" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">密码</label>
          <input v-model="form.password" type="password" required minlength="8" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">姓名</label>
          <input v-model="form.name" required class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">手机号</label>
          <input v-model="form.mobile" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">角色</label>
          <SelectField v-model="form.role" required class="w-full">
            <option value="hotel_admin">酒店管理员</option>
            <option value="system_admin">系统管理员</option>
          </SelectField>
        </div>
      </form>
      <template #footer>
        <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" @click="showCreate = false">取消</button>
        <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="handleCreate">创建</button>
      </template>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { employeeApi } from '@hotelink/api'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, SelectField, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'username', label: '用户名' },
  { key: 'nickname', label: '姓名' },
  { key: 'mobile', label: '手机号' },
  { key: 'role', label: '角色' },
  { key: 'status', label: '状态' },
]

const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showCreate = ref(false)
const form = reactive({ username: '', password: '', name: '', mobile: '', role: 'hotel_admin' })

// 加载 List 相关数据。
async function loadList() {
  loading.value = true
  try {
    const res = await employeeApi.list({ page: page.value, page_size: pageSize.value })
    if (res.code === 0 && res.data) {
      const d = res.data as unknown as { items: Record<string, unknown>[]; total: number }
      list.value = d.items || []
      total.value = d.total || 0
    } else {
      showToast(res.message || '加载员工列表失败', 'error')
    }
  } catch {
    showToast('加载员工列表失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

// 打开 Create 相关界面。
function openCreate() {
  form.username = ''
  form.password = ''
  form.name = ''
  form.mobile = ''
  form.role = 'hotel_admin'
  showCreate.value = true
}

// 处理 Create 交互逻辑。
async function handleCreate() {
  try {
    const res = await employeeApi.create(form)
    if (res.code === 0) {
      showToast('员工创建成功', 'success')
      showCreate.value = false
      loadList()
    } else {
      showToast(res.message || '创建失败', 'error')
    }
  } catch {
    showToast('创建失败，请重试', 'error')
  }
}

onMounted(loadList)
</script>

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
          <input
            v-model="form.username"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="formErrors.username ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-slate-300 focus:border-teal-500'"
            placeholder="建议 3-30 位，支持中英文和数字"
            @input="clearFormError('username')"
            @blur="validateField('username')"
          />
          <p v-if="formErrors.username" class="mt-1 text-xs text-red-500">{{ formErrors.username }}</p>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="formErrors.password ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-slate-300 focus:border-teal-500'"
            placeholder="至少 8 位"
            @input="clearFormError('password')"
            @blur="validateField('password')"
          />
          <div class="mt-2">
            <div class="h-2 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full transition-all" :class="passwordStrengthBarClass" :style="{ width: `${passwordStrength.percentage}%` }" />
            </div>
            <p class="mt-1 text-xs" :class="passwordStrengthTextClass">密码强度：{{ passwordStrength.label }}，{{ passwordStrength.hint }}</p>
          </div>
          <p v-if="formErrors.password" class="mt-1 text-xs text-red-500">{{ formErrors.password }}</p>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">姓名</label>
          <input
            v-model="form.name"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="formErrors.name ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-slate-300 focus:border-teal-500'"
            placeholder="请输入员工姓名"
            @input="clearFormError('name')"
            @blur="validateField('name')"
          />
          <p v-if="formErrors.name" class="mt-1 text-xs text-red-500">{{ formErrors.name }}</p>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">手机号</label>
          <input
            v-model="form.mobile"
            class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition"
            :class="formErrors.mobile ? 'border-red-300 bg-red-50/70 focus:border-red-400' : 'border-slate-300 focus:border-teal-500'"
            placeholder="选填，填写 11 位手机号"
            @input="handleMobileInput"
            @blur="validateField('mobile')"
          />
          <p v-if="formErrors.mobile" class="mt-1 text-xs text-red-500">{{ formErrors.mobile }}</p>
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
import { computed, ref, reactive, onMounted } from 'vue'
import { employeeApi } from '@hotelink/api'
import { PageHeader, DataTable, StatusBadge, ModalDialog, Pagination, SelectField, useToast } from '@hotelink/ui'
import { extractApiError, extractApiFieldErrors, getPasswordStrength, isValidChineseMobile, validatePassword, validateUsername } from '@hotelink/utils'

type EmployeeField = 'username' | 'password' | 'name' | 'mobile'

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
const formErrors = ref<Partial<Record<EmployeeField, string>>>({})

const passwordStrength = computed(() => getPasswordStrength(form.password, 8))
const passwordStrengthBarClass = computed(() => {
  switch (passwordStrength.value.level) {
    case 'weak':
      return 'bg-red-400'
    case 'fair':
      return 'bg-amber-400'
    case 'good':
      return 'bg-emerald-400'
    case 'strong':
      return 'bg-emerald-500'
    default:
      return 'bg-slate-200'
  }
})
const passwordStrengthTextClass = computed(() => {
  switch (passwordStrength.value.level) {
    case 'weak':
      return 'text-red-500'
    case 'fair':
      return 'text-amber-600'
    case 'good':
    case 'strong':
      return 'text-emerald-600'
    default:
      return 'text-slate-400'
  }
})

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
  formErrors.value = {}
  showCreate.value = true
}

function clearFormError(field: EmployeeField) {
  if (formErrors.value[field]) {
    formErrors.value = { ...formErrors.value, [field]: undefined }
  }
}

function handleMobileInput() {
  form.mobile = form.mobile.replace(/\D/g, '').slice(0, 11)
  clearFormError('mobile')
}

function getFieldError(field: EmployeeField): string {
  switch (field) {
    case 'username':
      return validateUsername(form.username, { minLength: 3, maxLength: 30 })
    case 'password':
      return validatePassword(form.password, { minLength: 8 })
    case 'name':
      if (!form.name.trim()) return '请输入员工姓名'
      return form.name.trim().length > 100 ? '姓名不能超过 100 个字符' : ''
    case 'mobile':
      if (!form.mobile.trim()) return ''
      return isValidChineseMobile(form.mobile) ? '' : '请输入有效的 11 位手机号'
    default:
      return ''
  }
}

function validateField(field: EmployeeField) {
  formErrors.value = {
    ...formErrors.value,
    [field]: getFieldError(field) || undefined,
  }
}

function validateForm(): boolean {
  const nextErrors: Partial<Record<EmployeeField, string>> = {}
  form.username = form.username.trim()
  form.name = form.name.trim()

  ;(['username', 'password', 'name', 'mobile'] as EmployeeField[]).forEach((field) => {
    const message = getFieldError(field)
    if (message) {
      nextErrors[field] = message
    }
  })

  formErrors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

// 处理 Create 交互逻辑。
async function handleCreate() {
  if (!validateForm()) {
    showToast(Object.values(formErrors.value).find(Boolean) || '请检查员工信息', 'warning')
    return
  }

  try {
    const res = await employeeApi.create(form)
    if (res.code === 0) {
      showToast('员工创建成功', 'success')
      showCreate.value = false
      loadList()
    } else {
      formErrors.value = {
        ...formErrors.value,
        ...extractApiFieldErrors(res, {
          mobile: '手机号',
          name: '姓名',
          password: '密码',
          username: '用户名',
        }),
      }
      showToast(extractApiError(res, '创建失败，请检查填写内容'), 'error')
    }
  } catch {
    showToast('创建失败，请重试', 'error')
  }
}

onMounted(loadList)
</script>

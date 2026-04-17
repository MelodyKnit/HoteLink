<template>
  <section>
    <PageHeader title="系统设置" subtitle="平台配置与安全操作" />

    <div v-if="loading" class="text-center py-20 text-slate-400">加载中…</div>
    <div v-else class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div class="space-y-6">
        <div class="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
          <form class="space-y-6" @submit.prevent="handleSave">
            <div class="space-y-4">
              <div>
                <h3 class="text-base font-semibold text-slate-800">基础信息</h3>
                <p class="mt-1 text-sm text-slate-500">这些内容会出现在管理端和用户端的基础展示区域。</p>
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-1 block text-sm font-medium">平台名称</label>
                  <input v-model="form.platform_name" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium">管理端名称</label>
                  <input v-model="form.admin_name" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
              </div>
            </div>

            <div class="space-y-4 rounded-2xl bg-slate-50/80 p-5">
              <div>
                <h3 class="text-base font-semibold text-slate-800">联系与服务</h3>
                <p class="mt-1 text-sm text-slate-500">这些信息会用于客服入口、订单通知和系统提醒。</p>
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-1 block text-sm font-medium">客服电话</label>
                  <input v-model="form.support_phone" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium">客服邮箱</label>
                  <input v-model="form.support_email" type="email" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium">服务时间</label>
                <input v-model="form.business_hours" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="例如：09:00-18:00" />
              </div>
            </div>

            <div class="space-y-4 rounded-2xl bg-slate-50/80 p-5">
              <div>
                <h3 class="text-base font-semibold text-slate-800">运营规则与公告</h3>
                <p class="mt-1 text-sm text-slate-500">控制订单自动取消规则，并配置一条对外可见的系统公告。</p>
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-1 block text-sm font-medium">订单自动取消时间（分钟）</label>
                  <input v-model.number="form.order_auto_cancel_minutes" type="number" min="1" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium">平台公告</label>
                <textarea v-model="form.platform_notice" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="例如：春节期间客服时间调整为..."></textarea>
              </div>
            </div>

            <div class="flex justify-end gap-3">
              <button type="button" class="rounded-lg border border-slate-300 px-6 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50" @click="loadSettings" :disabled="saving">恢复当前值</button>
              <button type="submit" class="rounded-lg bg-teal-600 px-6 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving">
                {{ saving ? '保存中…' : '保存设置' }}
              </button>
            </div>
          </form>
          <p v-if="saved" class="mt-3 text-center text-sm text-green-600">保存成功</p>
        </div>

        <div class="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-red-200">
          <h3 class="text-base font-semibold text-red-600">危险操作：系统重置</h3>
          <p class="mt-1 text-sm text-slate-500">
            此操作将清除所有业务数据（酒店、房型、订单、用户、评价等），仅保留管理员账号。操作不可逆！
          </p>
          <div class="mt-4 flex items-end gap-3">
            <div class="flex-1">
              <label class="mb-1 block text-sm font-medium text-red-600">输入 RESET 确认重置</label>
              <input v-model="resetConfirm" class="w-full rounded-lg border border-red-300 px-3 py-2 text-sm outline-none focus:border-red-500" placeholder="请输入 RESET" />
            </div>
            <button
              class="rounded-lg bg-red-600 px-6 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="resetConfirm !== 'RESET' || resetting"
              @click="handleReset"
            >
              {{ resetting ? '重置中…' : '确认重置' }}
            </button>
          </div>
          <p v-if="resetMessage" class="mt-3 text-sm" :class="resetSuccess ? 'text-green-600' : 'text-red-600'">{{ resetMessage }}</p>
        </div>
      </div>
      <div class="space-y-6 lg:sticky lg:top-6 lg:self-start">
        <div class="rounded-2xl bg-slate-900 p-6 text-white shadow-sm">
          <p class="text-xs uppercase tracking-wider text-slate-400">配置概览</p>
          <div class="mt-4 space-y-3 text-sm">
            <div class="flex items-center justify-between gap-4">
              <span class="text-slate-400">平台名称</span>
              <span class="text-right font-medium">{{ form.platform_name || '—' }}</span>
            </div>
            <div class="flex items-center justify-between gap-4">
              <span class="text-slate-400">客服电话</span>
              <span class="text-right font-medium">{{ form.support_phone || '—' }}</span>
            </div>
            <div class="flex items-center justify-between gap-4">
              <span class="text-slate-400">客服邮箱</span>
              <span class="text-right font-medium">{{ form.support_email || '—' }}</span>
            </div>
            <div class="flex items-center justify-between gap-4">
              <span class="text-slate-400">服务时间</span>
              <span class="text-right font-medium">{{ form.business_hours || '—' }}</span>
            </div>
            <div class="flex items-center justify-between gap-4">
              <span class="text-slate-400">自动取消</span>
              <span class="text-right font-medium">{{ form.order_auto_cancel_minutes }} 分钟</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { settingsApi, adminSystemApi } from '@hotelink/api'
import { extractApiError } from '@hotelink/utils'
import { PageHeader, useToast, useConfirm } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

const loading = ref(true)
const saving = ref(false)
const saved = ref(false)
const form = reactive({
  platform_name: '',
  admin_name: '',
  support_phone: '',
  support_email: '',
  business_hours: '',
  platform_notice: '',
  order_auto_cancel_minutes: 30,
})

const resetConfirm = ref('')
const resetting = ref(false)
const resetMessage = ref('')
const resetSuccess = ref(false)

async function loadSettings() {
  loading.value = true
  try {
    const res = await settingsApi.get()
    if (res.code === 0 && res.data) {
      const d = res.data as Record<string, unknown>
      form.platform_name = (d.platform_name as string) || ''
      form.admin_name = (d.admin_name as string) || ''
      form.support_phone = (d.support_phone as string) || ''
      form.support_email = (d.support_email as string) || ''
      form.business_hours = (d.business_hours as string) || ''
      form.platform_notice = (d.platform_notice as string) || ''
      form.order_auto_cancel_minutes = (d.order_auto_cancel_minutes as number) || 30
    } else {
      showToast(res.message || '加载设置失败', 'error')
    }
  } catch {
    showToast('加载设置失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  saved.value = false
  try {
    const res = await settingsApi.update(form)
    if (res.code === 0) {
      saved.value = true
      showToast('设置保存成功', 'success')
      setTimeout(() => { saved.value = false }, 2000)
    } else {
      showToast(extractApiError(res, '保存设置失败'), 'error')
    }
  } catch {
    showToast('保存设置失败，请重试', 'error')
  } finally {
    saving.value = false
  }
}

async function handleReset() {
  if (resetConfirm.value !== 'RESET') return
  if (!await confirmDialog('最后确认：此操作将清除所有业务数据且不可逆，是否继续？', { type: 'danger', title: '危险操作' })) return
  resetting.value = true
  resetMessage.value = ''
  try {
    const res = await adminSystemApi.reset('RESET')
    if (res.code === 0 && res.data) {
      resetSuccess.value = true
      resetMessage.value = res.data.message || '系统已重置'
      resetConfirm.value = ''
      showToast('系统重置成功', 'success')
    } else {
      resetSuccess.value = false
      resetMessage.value = res.message || '重置失败'
      showToast(res.message || '重置失败', 'error')
    }
  } catch {
    resetSuccess.value = false
    resetMessage.value = '重置请求失败，请检查网络连接'
    showToast('重置请求失败', 'error')
  }
  resetting.value = false
}

onMounted(loadSettings)
</script>

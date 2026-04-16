<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-bold text-gray-800">优惠券管理</h2>
      <button @click="showCreate = true" class="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark">
        + 创建优惠券
      </button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-3 gap-4">
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs text-gray-400">有效模板</p>
        <p class="mt-1 text-2xl font-bold text-brand">{{ stats.active }}</p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs text-gray-400">总发行量</p>
        <p class="mt-1 text-2xl font-bold text-gray-800">{{ stats.totalIssued }}</p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs text-gray-400">已领取</p>
        <p class="mt-1 text-2xl font-bold text-orange-500">{{ stats.totalClaimed }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-hidden rounded-xl bg-white shadow-sm">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-xs text-gray-500">
          <tr>
            <th class="px-4 py-3 text-left">名称</th>
            <th class="px-4 py-3 text-left">类型</th>
            <th class="px-4 py-3 text-left">面额/折扣</th>
            <th class="px-4 py-3 text-left">门槛</th>
            <th class="px-4 py-3 text-left">库存</th>
            <th class="px-4 py-3 text-left">积分成本</th>
            <th class="px-4 py-3 text-left">等级要求</th>
            <th class="px-4 py-3 text-left">有效期</th>
            <th class="px-4 py-3 text-left">状态</th>
            <th class="px-4 py-3 text-left">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="tpl in templates" :key="tpl.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-800">{{ tpl.name }}</td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-0.5 text-xs" :class="tpl.coupon_type === 'cash' ? 'bg-green-50 text-green-600' : 'bg-orange-50 text-orange-600'">
                {{ tpl.coupon_type === 'cash' ? '满减券' : '折扣券' }}
              </span>
            </td>
            <td class="px-4 py-3">
              {{ tpl.coupon_type === 'cash' ? `¥${tpl.amount}` : `${tpl.discount}折` }}
            </td>
            <td class="px-4 py-3 text-gray-500">{{ tpl.min_amount > 0 ? `满¥${tpl.min_amount}` : '无门槛' }}</td>
            <td class="px-4 py-3">{{ tpl.claimed_count }}/{{ tpl.total_count }}</td>
            <td class="px-4 py-3">{{ tpl.points_cost > 0 ? `${tpl.points_cost}积分` : '免费' }}</td>
            <td class="px-4 py-3 text-gray-500">{{ levelLabel(tpl.required_level) }}</td>
            <td class="px-4 py-3 text-xs text-gray-400">{{ tpl.valid_start }} ~ {{ tpl.valid_end }}</td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-0.5 text-xs" :class="tpl.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'">
                {{ tpl.status === 'active' ? '有效' : '已下架' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <button v-if="tpl.status === 'active'" @click="toggleStatus(tpl, 'inactive')" class="text-xs text-red-500 hover:underline">下架</button>
              <button v-else @click="toggleStatus(tpl, 'active')" class="text-xs text-brand hover:underline">上架</button>
            </td>
          </tr>
          <tr v-if="templates.length === 0">
            <td colspan="10" class="px-4 py-12 text-center text-gray-400">暂无优惠券模板</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCreate = false">
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-bold text-gray-800">创建优惠券</h3>
        <div class="space-y-3">
          <div>
            <label class="mb-1 block text-xs text-gray-500">券名称</label>
            <input v-model="form.name" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs text-gray-500">类型</label>
              <SelectField v-model="form.coupon_type" class="w-full">
                <option value="cash">满减券</option>
                <option value="discount">折扣券</option>
              </SelectField>
            </div>
            <div v-if="form.coupon_type === 'cash'">
              <label class="mb-1 block text-xs text-gray-500">减免金额(¥)</label>
              <input v-model.number="form.amount" type="number" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
            <div v-else>
              <label class="mb-1 block text-xs text-gray-500">折扣(如9=9折)</label>
              <input v-model.number="form.discount" type="number" step="0.1" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs text-gray-500">最低消费(¥)</label>
              <input v-model.number="form.min_amount" type="number" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-500">发行数量</label>
              <input v-model.number="form.total_count" type="number" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs text-gray-500">积分成本(0=免费)</label>
              <input v-model.number="form.points_cost" type="number" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-500">会员等级要求</label>
              <SelectField v-model="form.required_level" class="w-full">
                <option value="">不限</option>
                <option value="silver">銀卡会员</option>
                <option value="gold">金卡会员</option>
                <option value="platinum">铂金会员</option>
                <option value="diamond">钒石会员</option>
              </SelectField>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="mb-1 block text-xs text-gray-500">有效天数</label>
              <input v-model.number="form.valid_days" type="number" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-500">活动开始</label>
              <input v-model="form.valid_start" type="date" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-500">活动结束</label>
              <input v-model="form.valid_end" type="date" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
          </div>
          <div v-if="createError" class="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{{ createError }}</div>
        </div>
        <div class="mt-5 flex justify-end gap-3">
          <button @click="showCreate = false" class="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">取消</button>
          <button @click="handleCreate" :disabled="creating" class="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50">
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminCouponApi } from '@hotelink/api'
import { SelectField, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const templates = ref<any[]>([])
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')

const today = new Date().toISOString().slice(0, 10)
const form = ref({
  name: '',
  coupon_type: 'cash',
  amount: 50,
  discount: 9.5,
  min_amount: 200,
  total_count: 100,
  points_cost: 0,
  required_level: '',
  valid_days: 30,
  valid_start: today,
  valid_end: '',
  per_user_limit: 1,
})

const stats = computed(() => {
  const active = templates.value.filter(t => t.status === 'active').length
  const totalIssued = templates.value.reduce((s: number, t: any) => s + (t.total_count || 0), 0)
  const totalClaimed = templates.value.reduce((s: number, t: any) => s + (t.claimed_count || 0), 0)
  return { active, totalIssued, totalClaimed }
})

const levelLabels: Record<string, string> = {
  '': '不限',
  silver: '银卡',
  gold: '金卡',
  platinum: '铂金',
  diamond: '钻石',
}
function levelLabel(level: string) { return levelLabels[level || ''] || '不限' }

async function loadData() {
  try {
    const res = await adminCouponApi.list({ page_size: 100 })
    if (res.code === 0 && res.data) {
      templates.value = (res.data as any).items || []
    } else {
      showToast(res.message || '优惠券模板加载失败', 'error')
    }
  } catch {
    showToast('优惠券模板加载失败，请检查网络后重试', 'error')
  }
}

async function handleCreate() {
  createError.value = ''
  if (!form.value.name.trim()) { createError.value = '请输入券名称'; return }
  if (!form.value.valid_start || !form.value.valid_end) { createError.value = '请设置活动日期'; return }
  creating.value = true
  try {
    const res = await adminCouponApi.create(form.value as any)
    if (res.code === 0) {
      showToast('优惠券创建成功', 'success')
      showCreate.value = false
      await loadData()
    } else {
      createError.value = res.message || '创建失败'
      showToast(createError.value, 'error')
    }
  } catch {
    createError.value = '网络错误'
    showToast('创建优惠券失败，请检查网络后重试', 'error')
  } finally {
    creating.value = false
  }
}

async function toggleStatus(tpl: any, status: string) {
  try {
    const res = await adminCouponApi.update({ template_id: tpl.id, status })
    if (res.code === 0) {
      showToast(status === 'active' ? '已上架' : '已下架', 'success')
      await loadData()
    } else {
      showToast(res.message || '操作失败', 'error')
    }
  } catch {
    showToast('操作失败，请重试', 'error')
  }
}

onMounted(loadData)
</script>

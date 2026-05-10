<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-slate-800">会员管理</h2>
        <p class="text-xs text-slate-400">共 {{ totalUsers }} 位会员</p>
      </div>
      <button @click="loadData" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50">🔄 刷新</button>
    </div>

    <div v-if="loading && !levels.length" class="py-20 text-center text-sm text-slate-400">加载中…</div>

    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
        <p class="text-xs text-slate-400">会员总数</p>
        <p class="mt-1 text-2xl font-bold text-slate-800">{{ totalUsers.toLocaleString() }}</p>
        <p class="mt-2 text-xs text-slate-400">仅统计普通用户会员体系</p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm ring-1 ring-amber-100">
        <p class="text-xs text-amber-600/70">会员积分总量</p>
        <p class="mt-1 text-2xl font-bold text-amber-700">{{ totalMemberPoints.toLocaleString() }}</p>
        <p class="mt-2 text-xs text-slate-400">成长值，用于等级升级且不扣减</p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm ring-1 ring-teal-100">
        <p class="text-xs text-teal-600/70">消费积分余额</p>
        <p class="mt-1 text-2xl font-bold text-teal-700">{{ totalConsumePoints.toLocaleString() }}</p>
        <p class="mt-2 text-xs text-slate-400">可用于优惠券或礼品兑换</p>
      </div>
    </div>

    <!-- Level Overview -->
    <div class="grid grid-cols-2 gap-4 md:grid-cols-5">
      <div v-for="lv in levels" :key="lv.level"
        class="rounded-xl p-4 text-white shadow-sm"
        :class="levelGradients[lv.level] || 'bg-slate-500'">
        <p class="text-xs opacity-80">{{ lv.label }}</p>
        <p class="mt-1 text-2xl font-bold">{{ lv.count }}</p>
        <p class="mt-2 text-xs opacity-80">≥ {{ levelThreshold(lv).toLocaleString() }} 会员积分</p>
      </div>
    </div>

    <!-- Rules -->
    <div class="rounded-xl bg-white p-6 shadow-sm">
      <h3 class="mb-4 font-semibold text-slate-800">会员权益体系</h3>
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th class="px-4 py-3 text-left">等级</th>
            <th class="px-4 py-3 text-left">会员积分门槛</th>
            <th class="px-4 py-3 text-left">消费折扣</th>
            <th class="px-4 py-3 text-left">消费积分倍率</th>
            <th class="px-4 py-3 text-left">当前人数</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-50">
          <tr v-for="lv in levels" :key="lv.level" class="hover:bg-slate-50">
            <td class="px-4 py-3">
              <span class="font-medium text-slate-800">{{ levelIcons[lv.level] }} {{ lv.label }}</span>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ levelThreshold(lv).toLocaleString() }}</td>
            <td class="px-4 py-3">
              <span v-if="lv.discount_rate < 1" class="rounded-full bg-red-50 px-2 py-0.5 text-xs text-red-600">
                {{ (lv.discount_rate * 100).toFixed(0) }}折
              </span>
              <span v-else class="text-slate-400">无</span>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full bg-brand/10 px-2 py-0.5 text-xs text-brand">{{ lv.points_multiplier }}x</span>
            </td>
            <td class="px-4 py-3 font-medium text-slate-800">{{ lv.count }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Rules description -->
    <div class="rounded-xl bg-white p-6 shadow-sm">
      <h3 class="mb-3 font-semibold text-slate-800">积分规则</h3>
      <div class="space-y-2 text-sm text-slate-600">
        <p>📌 支付成功后同时获得会员积分与消费积分，基础规则为每消费 <strong>10元</strong> 获得 <strong>1分</strong>，并受会员倍率加成</p>
        <p>📌 会员积分是累计成长值，只用于等级升级，不会因取消订单回收、兑换优惠券或礼品而扣减</p>
        <p>📌 消费积分是可用余额，可用于兑换优惠券，后续可扩展到礼品兑换；订单取消时只回收消费积分</p>
        <p>📌 评价订单可额外获得消费积分，会员等级根据会员积分门槛自动升级且不会降级</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminMemberApi } from '@hotelink/api'
import type { AdminMemberLevelOverview } from '@hotelink/api'
import { useToast } from '@hotelink/ui'

const { showToast } = useToast()

const loading = ref(false)
const levels = ref<AdminMemberLevelOverview[]>([])
const totalUsers = ref(0)
const totalMemberPoints = ref(0)
const totalConsumePoints = ref(0)

const levelGradients: Record<string, string> = {
  normal: 'bg-gradient-to-r from-slate-500 to-slate-600',
  silver: 'bg-gradient-to-r from-slate-400 to-slate-500',
  gold: 'bg-gradient-to-r from-yellow-600 to-amber-500',
  platinum: 'bg-gradient-to-r from-purple-600 to-indigo-500',
  diamond: 'bg-gradient-to-r from-amber-500 to-yellow-400',
}

const levelIcons: Record<string, string> = {
  normal: '🌱',
  silver: '🥈',
  gold: '🥇',
  platinum: '💎',
  diamond: '👑',
}

function levelThreshold(lv: AdminMemberLevelOverview) {
  return Number(lv.member_points_threshold ?? lv.threshold ?? 0)
}

async function loadData() {
  loading.value = true
  try {
    const res = await adminMemberApi.overview()
    if (res.code === 0 && res.data) {
      levels.value = res.data.levels || []
      totalUsers.value = res.data.total_users || 0
      totalMemberPoints.value = res.data.total_member_points || 0
      totalConsumePoints.value = res.data.total_consume_points || 0
    } else {
      showToast((res as any).message || '加载会员数据失败', 'error')
    }
  } catch {
    showToast('加载会员数据失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

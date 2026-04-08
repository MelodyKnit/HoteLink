<template>
  <div class="space-y-6">
    <h2 class="text-lg font-bold text-gray-800">会员管理</h2>

    <!-- Level Overview -->
    <div class="grid grid-cols-5 gap-4">
      <div v-for="lv in levels" :key="lv.level"
        class="rounded-xl p-4 text-white shadow-sm"
        :class="levelGradients[lv.level] || 'bg-gray-500'">
        <p class="text-xs opacity-80">{{ lv.label }}</p>
        <p class="mt-1 text-2xl font-bold">{{ lv.count }}</p>
        <p class="mt-2 text-xs opacity-80">≥ {{ lv.threshold.toLocaleString() }} 积分</p>
      </div>
    </div>

    <!-- Rules -->
    <div class="rounded-xl bg-white p-6 shadow-sm">
      <h3 class="mb-4 font-semibold text-gray-800">会员权益体系</h3>
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-xs text-gray-500">
          <tr>
            <th class="px-4 py-3 text-left">等级</th>
            <th class="px-4 py-3 text-left">积分门槛</th>
            <th class="px-4 py-3 text-left">消费折扣</th>
            <th class="px-4 py-3 text-left">积分倍率</th>
            <th class="px-4 py-3 text-left">当前人数</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="lv in levels" :key="lv.level" class="hover:bg-gray-50">
            <td class="px-4 py-3">
              <span class="font-medium text-gray-800">{{ levelIcons[lv.level] }} {{ lv.label }}</span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ lv.threshold.toLocaleString() }}</td>
            <td class="px-4 py-3">
              <span v-if="lv.discount_rate < 1" class="rounded-full bg-red-50 px-2 py-0.5 text-xs text-red-600">
                {{ (lv.discount_rate * 100).toFixed(0) }}折
              </span>
              <span v-else class="text-gray-400">无</span>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full bg-brand/10 px-2 py-0.5 text-xs text-brand">{{ lv.points_multiplier }}x</span>
            </td>
            <td class="px-4 py-3 font-medium text-gray-800">{{ lv.count }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Rules description -->
    <div class="rounded-xl bg-white p-6 shadow-sm">
      <h3 class="mb-3 font-semibold text-gray-800">积分规则</h3>
      <div class="space-y-2 text-sm text-gray-600">
        <p>📌 每消费 <strong>10元</strong> 获得 <strong>1积分</strong>（支付成功后自动到账）</p>
        <p>📌 积分获取受会员倍率加成，高等级会员获得更多积分</p>
        <p>📌 评价订单可额外获得 <strong>10积分</strong></p>
        <p>📌 积分可用于兑换优惠券</p>
        <p>📌 会员等级根据累计积分自动升级，不会降级</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminMemberApi } from '@hotelink/api'
import { useToast } from '@hotelink/ui'

const { showToast } = useToast()

const levels = ref<any[]>([])
const totalUsers = ref(0)

const levelGradients: Record<string, string> = {
  normal: 'bg-gradient-to-r from-gray-500 to-gray-600',
  silver: 'bg-gradient-to-r from-gray-400 to-gray-500',
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

async function loadData() {
  try {
    const res = await adminMemberApi.overview()
    if (res.code === 0 && res.data) {
      levels.value = (res.data as any).levels || []
      totalUsers.value = (res.data as any).total_users || 0
    } else {
      showToast((res as any).message || '加载会员数据失败', 'error')
    }
  } catch {
    showToast('加载会员数据失败，请检查网络', 'error')
  }
}

onMounted(loadData)
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">我的收藏</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-4 pb-24 md:pb-4">
      <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

      <div v-if="loading" class="flex justify-center py-20">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
      </div>

      <div v-else-if="hotels.length === 0" class="py-20 text-center">
        <p class="text-4xl">❤️</p>
        <p class="mt-2 text-sm text-gray-400">还没有收藏酒店</p>
        <router-link to="/hotels" class="mt-3 inline-block rounded-full bg-brand px-5 py-2 text-sm text-white">去逛逛</router-link>
      </div>

      <div v-else class="space-y-3">
        <div v-for="hotel in hotels" :key="hotel.id"
          class="flex gap-3 overflow-hidden rounded-2xl bg-white p-3 shadow-sm">
          <router-link :to="`/hotels/${hotel.id}`" class="h-24 w-28 flex-shrink-0 overflow-hidden rounded-xl">
            <img :src="hotel.cover_thumb || hotel.cover || 'https://placehold.co/280x240/0f766e/white?text=Hotel'" class="h-full w-full object-cover" loading="lazy" decoding="async" />
          </router-link>
          <div class="flex flex-1 flex-col justify-between">
            <div>
              <router-link :to="`/hotels/${hotel.id}`" class="text-sm font-semibold text-gray-800 hover:text-brand">{{ hotel.name }}</router-link>
              <p class="mt-0.5 text-xs text-gray-400">{{ hotel.star_level }}星 · {{ hotel.city }}</p>
              <p class="text-xs text-gray-400">{{ hotel.address }}</p>
            </div>
            <div class="flex items-end justify-between">
              <span class="text-base font-bold text-orange-600">¥{{ hotel.min_price || '--' }}<span class="text-xs font-normal text-gray-400">起</span></span>
              <button @click="removeFav(hotel.id)" class="rounded-lg px-2 py-1 text-xs text-red-400 hover:bg-red-50">取消收藏</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userFavoriteApi } from '@hotelink/api'
import { buildImageThumbUrl } from '@hotelink/utils'

const loading = ref(true)
const hotels = ref<any[]>([])
const error = ref('')

function normalizeFavoriteItem(item: any) {
  const rawHotel = item?.hotel && typeof item.hotel === 'object' ? item.hotel : item
  const hotelId = Number(rawHotel?.id ?? item?.hotel_id ?? item?.id)
  const cover = String(rawHotel?.cover_image || rawHotel?.cover || '')
  return {
    id: Number.isFinite(hotelId) && hotelId > 0 ? hotelId : 0,
    name: rawHotel?.name || '',
    city: rawHotel?.city || '',
    address: rawHotel?.address || '',
    star_level: Number(rawHotel?.star_level ?? rawHotel?.star ?? 0),
    min_price: rawHotel?.min_price ?? '--',
    cover,
    cover_thumb: buildImageThumbUrl(cover, 224, 192) || rawHotel?.cover_thumb || cover,
  }
}

// 删除 Fav 数据。
async function removeFav(id: number) {
  try {
    const res = await userFavoriteApi.remove(id)
    if (res.code === 0) hotels.value = hotels.value.filter(h => h.id !== id)
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    const res = await userFavoriteApi.list()
    if (res.code === 0 && res.data) {
      const rawItems = (res.data as any).items || res.data || []
      hotels.value = Array.isArray(rawItems)
        ? rawItems.map(normalizeFavoriteItem).filter((item) => item.id > 0)
        : []
    }
  } catch {
    hotels.value = []
    error.value = '收藏数据加载失败，请稍后重试'
  } finally { loading.value = false }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">我的评价</h1>
    </header>

    <div class="mx-auto max-w-2xl px-4 py-4 pb-24 md:pb-4">
      <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

      <div v-if="loading" class="flex justify-center py-20">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
      </div>

      <div v-else-if="reviews.length === 0" class="py-20 text-center">
        <p class="text-4xl">📝</p>
        <p class="mt-2 text-sm text-gray-400">暂无评价记录</p>
      </div>

      <div v-else class="space-y-3">
        <div v-for="r in reviews" :key="r.id" class="rounded-2xl bg-white p-4 shadow-sm">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-800">{{ r.hotel_name }}</p>
              <p class="text-xs text-gray-400">{{ r.room_type_name }}</p>
            </div>
            <span class="flex items-center gap-1 text-sm font-bold text-yellow-500">{{ r.score }}★</span>
          </div>
          <p class="mt-2 text-sm text-gray-600">{{ r.content }}</p>
          <div v-if="r.images?.length" class="mt-2 flex gap-2 overflow-x-auto">
            <img v-for="(img, i) in r.images" :key="i" :src="img" class="h-16 w-16 flex-shrink-0 rounded-lg object-cover" />
          </div>
          <div class="mt-2 flex items-center justify-between text-xs text-gray-400">
            <span>{{ r.created_at }}</span>
            <span v-if="r.reply" class="text-brand">商家已回复</span>
          </div>
          <div v-if="r.reply" class="mt-2 rounded-xl bg-gray-50 p-3 text-xs text-gray-500">
            <span class="font-medium text-gray-700">商家回复：</span>{{ r.reply }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userReviewApi } from '@hotelink/api'

const loading = ref(true)
const reviews = ref<any[]>([])
const error = ref('')

onMounted(async () => {
  try {
    const res = await userReviewApi.list({ page: 1, page_size: 50 })
    if (res.code === 0 && res.data) reviews.value = (res.data as any).items || []
    else reviews.value = []
  } catch {
    reviews.value = []
    error.value = '评价数据加载失败，请稍后重试'
  } finally { loading.value = false }
})
</script>

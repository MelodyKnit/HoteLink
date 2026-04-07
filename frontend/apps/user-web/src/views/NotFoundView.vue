<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto flex max-w-md flex-col items-center rounded-3xl bg-white p-8 text-center shadow-sm ring-1 ring-slate-200">
      <p class="text-xs font-semibold uppercase tracking-[0.28em] text-teal-600">404</p>
      <h1 class="mt-3 text-2xl font-bold text-slate-900">页面不存在</h1>
      <p class="mt-2 text-sm leading-6 text-slate-500">
        抱歉，您访问的页面可能已下线或链接错误。
      </p>

      <div class="mt-8 grid w-full gap-3">
        <button
          class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          @click="goBack"
        >
          返回上一页
        </button>
        <button
          class="w-full rounded-2xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-700"
          @click="goHome"
        >
          返回主页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push('/')
}

function goHome() {
  router.push('/')
}
</script>

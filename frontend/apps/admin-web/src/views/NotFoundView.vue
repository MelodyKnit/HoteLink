<template>
  <section class="rounded-2xl bg-white p-10 text-center shadow-sm ring-1 ring-slate-200">
    <p class="text-xs font-semibold uppercase tracking-[0.28em] text-teal-600">404</p>
    <h1 class="mt-3 text-2xl font-bold text-slate-900">页面不存在</h1>
    <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
      当前地址没有对应的管理页面，请返回上一步或回到管理首页。
    </p>

    <div class="mx-auto mt-8 grid max-w-sm gap-3 sm:grid-cols-2">
      <button
        class="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        @click="goBack"
      >
        返回上一页
      </button>
      <button
        class="rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-700"
        @click="goHome"
      >
        返回主页
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push('/admin')
}

function goHome() {
  router.push('/admin')
}
</script>

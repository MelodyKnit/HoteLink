<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <div class="grid min-h-screen lg:grid-cols-[260px_1fr]">
      <aside class="bg-slate-900 px-6 py-8 text-white">
        <p class="text-xl font-semibold">HoteLink Admin</p>
        <p class="mt-2 text-sm text-slate-300">酒店管理端基础框架已完成初始化</p>
      </aside>

      <main class="px-4 py-6 lg:px-8">
        <router-view />
      </main>
    </div>
  </div>
</template>

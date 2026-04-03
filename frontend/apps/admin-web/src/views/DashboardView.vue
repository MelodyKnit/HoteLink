<template>
  <section class="space-y-6">
    <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h1 class="text-2xl font-semibold">管理端应用已就绪</h1>
      <p class="mt-3 text-sm leading-6 text-slate-600">
        当前已完成管理端基础壳、路由、状态管理、Tailwind CSS、Less
        和图表依赖预埋，后续可以继续扩展房态总览、订单管理、入住退房和报表模块。
      </p>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <p class="text-lg font-semibold">ECharts 已预装</p>
        <p class="mt-3 text-sm leading-6 text-slate-600">
          已加入 `echarts` 与 `vue-echarts`，后续可直接接入入住率、营收趋势、订单来源等可视化图表。
        </p>
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <p class="text-lg font-semibold">适配策略</p>
        <p class="mt-3 text-sm leading-6 text-slate-600">
          管理端以 PC 优先，同时保留移动端抽屉导航和卡片式列表的扩展空间。
        </p>
      </div>
    </div>
  </section>
</template>

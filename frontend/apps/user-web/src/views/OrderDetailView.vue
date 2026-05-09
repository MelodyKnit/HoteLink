<template>
  <div class="min-h-screen bg-gray-50">
    <header class="sticky top-0 z-40 flex h-14 items-center border-b border-gray-100 bg-white/95 px-4 backdrop-blur">
      <button @click="$router.back()" class="mr-3 rounded-lg p-1 text-gray-600 hover:bg-gray-100">← 返回</button>
      <h1 class="text-sm font-semibold text-gray-800">订单详情</h1>
    </header>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
    </div>

    <div v-else class="mx-auto max-w-4xl px-4 py-6 pb-28 md:pb-8">
      <p v-if="error" class="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ error }}</p>

      <!-- Status -->
      <div class="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-100">
        <div class="bg-gradient-to-r from-brand via-teal-500 to-cyan-500 p-5 text-white sm:p-6">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-sm text-teal-50/90">订单状态</p>
              <h2 class="mt-1 text-2xl font-bold">{{ statusLabel(order.status) }}</h2>
              <p class="mt-2 text-xs text-teal-50/80">订单号：{{ order.order_no }}</p>
            </div>
            <div class="rounded-2xl bg-white/15 px-4 py-3 text-left backdrop-blur sm:text-right">
              <p class="text-xs text-teal-50/80">实付金额</p>
              <p class="mt-1 text-2xl font-bold">¥{{ displayAmount }}</p>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-3 divide-x divide-slate-100 px-4 py-4 text-center">
          <div>
            <p class="text-xs text-slate-400">入住</p>
            <p class="mt-1 text-sm font-semibold text-slate-800">{{ order.check_in_date || '-' }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-400">离店</p>
            <p class="mt-1 text-sm font-semibold text-slate-800">{{ order.check_out_date || '-' }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-400">晚数</p>
            <p class="mt-1 text-sm font-semibold text-slate-800">{{ stayNights }} 晚</p>
          </div>
        </div>
      </div>

      <!-- 订单进度条 -->
      <div class="mt-3 rounded-2xl bg-white p-5 shadow-sm">
        <OrderStepBar :status="order.status" :timestamps="{
          pending_payment: order.created_at,
          paid: order.paid_at,
          confirmed: order.confirmed_at,
          checked_in: order.checked_in_at,
          completed: order.completed_at,
          cancelled: order.cancelled_at,
        }" />
      </div>

      <div v-if="changeEvents.length" class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h4 class="font-semibold text-gray-800">订单变更轨迹</h4>
          <span v-if="hasRollbackEvent" class="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">存在回滚/纠正</span>
        </div>
        <div class="space-y-2.5">
          <div
            v-for="(item, index) in changeEvents"
            :key="`${item.type}-${index}`"
            class="rounded-xl border px-3 py-2"
            :class="item.type === 'rollback' ? 'border-amber-200 bg-amber-50/70' : item.type === 'warning' ? 'border-rose-200 bg-rose-50/70' : 'border-slate-200 bg-slate-50/80'"
          >
            <div class="mb-1 flex items-center gap-2">
              <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                :class="item.type === 'extend' ? 'bg-indigo-100 text-indigo-700' : item.type === 'switch' ? 'bg-cyan-100 text-cyan-700' : item.type === 'checkin' ? 'bg-emerald-100 text-emerald-700' : item.type === 'checkout' ? 'bg-orange-100 text-orange-700' : item.type === 'rollback' ? 'bg-amber-100 text-amber-700' : item.type === 'warning' ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'">
                {{ item.tag }}
              </span>
              <span class="text-xs text-gray-400">{{ item.time || '最近更新' }}</span>
            </div>
            <p class="text-sm leading-6 text-gray-700">{{ item.text }}</p>
          </div>
        </div>
      </div>

      <!-- Hotel & Room -->
      <div
        v-if="hotelDetailPath"
        class="mt-4 rounded-2xl bg-white p-5 shadow-sm transition hover:shadow-md cursor-pointer"
        role="link"
        tabindex="0"
        @click="openHotelDetail"
        @keydown.enter.prevent="openHotelDetail"
        @keydown.space.prevent="openHotelDetail"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="truncate font-semibold text-gray-800">{{ order.hotel_name }}</h3>
            <p class="mt-1 text-sm text-gray-500">{{ order.room_type_name }}</p>
          </div>
          <span class="shrink-0 rounded-full bg-brand/10 px-2.5 py-1 text-xs font-medium text-brand">点击查看酒店</span>
        </div>
        <div class="mt-3 grid grid-cols-2 gap-3 text-sm text-gray-600">
          <div>
            <p class="text-xs text-gray-400">入住日期</p>
            <p class="font-medium">{{ order.check_in_date }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400">离店日期</p>
            <p class="font-medium">{{ order.check_out_date }}</p>
          </div>
        </div>
        <div v-if="order.room_no" class="mt-2 text-sm text-gray-600">
          <span class="text-xs text-gray-400">房间号：</span>{{ order.room_no }}
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <a
            :href="`tel:${supportPhone}`"
            @click.stop
            class="inline-flex h-8 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
          >
            拨打客服电话
          </a>
          <button
            type="button"
            @click.stop="askAiCustomerService"
            class="inline-flex h-8 items-center justify-center rounded-lg border border-teal-200 bg-white px-3 text-xs font-medium text-teal-700 transition hover:bg-teal-50"
          >
            询问 AI 客服
          </button>
        </div>
        <p class="mt-3 text-xs text-gray-400">需要取消订单、修改信息或联系酒店时，可直接使用上方入口。</p>
      </div>

      <div v-else class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h3 class="font-semibold text-gray-800">{{ order.hotel_name }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ order.room_type_name }}</p>
        <div class="mt-3 grid grid-cols-2 gap-3 text-sm text-gray-600">
          <div>
            <p class="text-xs text-gray-400">入住日期</p>
            <p class="font-medium">{{ order.check_in_date }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400">离店日期</p>
            <p class="font-medium">{{ order.check_out_date }}</p>
          </div>
        </div>
        <div v-if="order.room_no" class="mt-2 text-sm text-gray-600">
          <span class="text-xs text-gray-400">房间号：</span>{{ order.room_no }}
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <a
            :href="`tel:${supportPhone}`"
            @click.stop
            class="inline-flex h-8 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
          >
            拨打客服电话
          </a>
          <button
            type="button"
            @click.stop="askAiCustomerService"
            class="inline-flex h-8 items-center justify-center rounded-lg border border-teal-200 bg-white px-3 text-xs font-medium text-teal-700 transition hover:bg-teal-50"
          >
            询问 AI 客服
          </button>
        </div>
        <p class="mt-3 text-xs text-gray-400">需要取消订单、修改信息或联系酒店时，可直接使用上方入口。</p>
      </div>

      <!-- Guest Info -->
      <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h4 class="mb-2 font-semibold text-gray-800">入住人信息</h4>
        <div class="space-y-1 text-sm text-gray-600">
          <p>姓名：{{ order.guest_name }}</p>
          <p>手机：{{ order.guest_mobile }}</p>
          <p v-if="order.guest_count">人数：{{ order.guest_count }}人</p>
          <p v-if="order.remark">备注：{{ order.remark }}</p>
        </div>
      </div>

      <!-- Payment -->
      <div class="mt-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
        <div class="mb-4 flex items-center justify-between">
          <h4 class="font-semibold text-gray-800">费用信息</h4>
          <span class="rounded-full bg-orange-50 px-3 py-1 text-xs font-medium text-orange-600">¥{{ displayAmount }}</span>
        </div>
        <div class="grid gap-3 text-sm text-gray-600 sm:grid-cols-2">
          <div class="rounded-xl bg-slate-50 px-3 py-2.5">
            <p class="text-xs text-gray-400">支付方式</p>
            <p class="mt-1 font-medium text-slate-800">{{ paymentMethodMap[order.payment_method] || order.payment_method || '待支付' }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2.5">
            <p class="text-xs text-gray-400">支付状态</p>
            <p class="mt-1 font-medium text-slate-800">{{ paymentStatusMap[order.payment_status] || order.payment_status || '-' }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2.5">
            <p class="text-xs text-gray-400">原价</p>
            <p class="mt-1 font-medium text-slate-800">¥{{ formatMoney(order.original_amount || 0) }}</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2.5">
            <p class="text-xs text-gray-400">优惠</p>
            <p class="mt-1 font-medium text-slate-800">¥{{ formatMoney((Number(order.member_discount_amount || 0) + Number(order.coupon_discount_amount || 0)) || order.discount_amount || 0) }}</p>
          </div>
        </div>
      </div>

      <!-- Invoice -->
      <div v-if="canOpenInvoice" class="mt-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h4 class="font-semibold text-gray-800">发票服务</h4>
              <span v-if="invoiceRequestForOrder" class="rounded-full px-2.5 py-1 text-xs font-medium" :class="invoiceStatusClass(invoiceRequestForOrder.status)">
                {{ invoiceStatusLabel(invoiceRequestForOrder) }}
              </span>
            </div>
            <p class="mt-1 text-sm text-gray-500">
              {{ invoiceRequestForOrder ? `已提交至「${invoiceRequestForOrder.title}」` : '当前订单已完成，可提交电子发票申请。' }}
            </p>
          </div>
          <button
            type="button"
            @click="openInvoiceModal"
            class="inline-flex h-10 items-center justify-center rounded-xl bg-brand px-4 text-sm font-semibold text-white transition hover:bg-brand-dark"
          >
            {{ invoiceRequestForOrder ? '查看发票' : '开发票' }}
          </button>
        </div>
      </div>

      <!-- Timeline -->
      <div v-if="order.timeline?.length" class="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <h4 class="mb-3 font-semibold text-gray-800">订单时间线</h4>
        <div class="space-y-3">
          <div v-for="(item, i) in order.timeline" :key="i" class="flex gap-3">
            <div class="flex flex-col items-center">
              <div class="h-2.5 w-2.5 rounded-full" :class="i === 0 ? 'bg-brand' : 'bg-gray-300'" />
              <div v-if="i < order.timeline.length - 1" class="h-full w-px bg-gray-200" />
            </div>
            <div class="pb-3">
              <p class="text-sm font-medium text-gray-800">{{ item.title }}</p>
              <p class="text-xs text-gray-400">{{ item.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="showActionBar" class="sticky bottom-16 z-20 mt-6 rounded-2xl bg-white/95 p-3 shadow-sm backdrop-blur md:bottom-4">
        <div class="flex flex-wrap gap-2">
          <button
            v-if="order.status === 'pending_payment'"
            @click="goToPay"
            class="inline-flex h-11 min-w-[120px] flex-1 items-center justify-center whitespace-nowrap rounded-xl bg-brand px-4 text-center text-sm font-semibold text-white transition hover:bg-brand-dark"
          >
            去支付
          </button>
          <button
            v-if="canCancel"
            @click="showCancelModal = true"
            class="inline-flex h-11 min-w-[120px] flex-1 items-center justify-center whitespace-nowrap rounded-xl border border-red-200 bg-red-50/30 px-4 text-center text-sm font-medium text-red-500 transition hover:bg-red-50"
          >
            取消订单
          </button>
          <button
            v-if="order.status === 'completed' && !order.has_review"
            @click="showReviewModal = true"
            class="inline-flex h-11 min-w-[120px] flex-1 items-center justify-center whitespace-nowrap rounded-xl bg-brand px-4 text-center text-sm font-semibold text-white transition hover:bg-brand-dark"
          >
            评价
          </button>
          <router-link
            v-if="showRebook && hotelDetailPath"
            :to="hotelDetailRoute"
            class="inline-flex h-11 min-w-[120px] flex-1 items-center justify-center whitespace-nowrap rounded-xl border border-brand/30 bg-brand/5 px-4 text-center text-sm font-medium text-brand transition hover:bg-brand/10"
          >
            再次预订
          </router-link>
        </div>
      </div>
    </div>

    <!-- 评价成功积分提示 -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-300" enter-from-class="opacity-0 translate-y-2" leave-active-class="transition duration-300" leave-to-class="opacity-0 translate-y-2">
        <div v-if="reviewSuccessMsg" class="fixed bottom-24 left-1/2 z-[60] -translate-x-1/2 rounded-full bg-green-600 px-5 py-2 text-sm text-white shadow-lg">
          {{ reviewSuccessMsg }}
        </div>
      </Transition>
    </Teleport>

    <!-- Cancel modal -->
    <Teleport to="body">
      <div v-if="showCancelModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showCancelModal = false">
        <div class="w-full max-w-sm rounded-2xl bg-white p-6">
          <h3 class="text-lg font-bold text-gray-900">取消订单</h3>
          <textarea v-model="cancelReason" rows="3" placeholder="请输入取消原因" class="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-brand" />
          <div class="mt-4 flex gap-3">
            <button @click="showCancelModal = false" class="flex-1 rounded-xl border py-2.5 text-sm text-gray-600 hover:bg-gray-50">取消</button>
            <button @click="handleCancel" :disabled="cancelling" class="flex-1 rounded-xl bg-red-500 py-2.5 text-sm text-white hover:bg-red-600 disabled:opacity-50">确认取消</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Invoice modal -->
    <Teleport to="body">
      <div v-if="showInvoiceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showInvoiceModal = false">
        <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h3 class="text-lg font-bold text-gray-900">开具电子发票</h3>
              <p class="mt-1 text-xs text-gray-400">订单 {{ order.order_no }} · ¥{{ displayAmount }}</p>
            </div>
            <button type="button" class="rounded-lg px-2 py-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600" @click="showInvoiceModal = false">×</button>
          </div>

          <div v-if="invoiceLoading" class="flex justify-center py-10">
            <div class="h-7 w-7 animate-spin rounded-full border-4 border-brand border-t-transparent" />
          </div>

          <div v-else-if="invoiceRequestForOrder" class="mt-5 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
            <div class="flex items-center justify-between gap-3">
              <p class="font-semibold text-emerald-900">{{ invoiceRequestForOrder.title }}</p>
              <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="invoiceStatusClass(invoiceRequestForOrder.status)">
                {{ invoiceStatusLabel(invoiceRequestForOrder) }}
              </span>
            </div>
            <div class="mt-3 grid gap-2 text-sm text-emerald-800">
              <p>接收邮箱：{{ invoiceRequestForOrder.email || '未填写' }}</p>
              <p>提交时间：{{ invoiceRequestForOrder.created_at }}</p>
              <p v-if="invoiceRequestForOrder.tax_no">税号：{{ invoiceRequestForOrder.tax_no }}</p>
            </div>
          </div>

          <div v-else class="mt-5 space-y-4">
            <div v-if="invoiceError" class="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-600">{{ invoiceError }}</div>

            <div v-if="invoiceTitles.length">
              <label class="text-sm font-medium text-gray-700">选择发票抬头</label>
              <SelectField v-model.number="selectedInvoiceTitleId" class="mt-2 w-full">
                <option :value="0">请选择抬头</option>
                <option v-for="title in invoiceTitles" :key="title.id" :value="title.id">
                  {{ title.title }} · {{ title.invoice_type === 'company' ? '企业' : '个人' }}
                </option>
              </SelectField>
              <p class="mt-2 text-xs text-gray-400">提交后后台会进入发票处理流程，同一订单不能重复申请。</p>
            </div>

            <div v-else class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-center">
              <p class="text-sm font-medium text-slate-700">暂无发票抬头</p>
              <p class="mt-1 text-xs text-slate-400">请先到发票管理添加个人或企业抬头。</p>
              <router-link to="/my/invoices" class="mt-3 inline-flex rounded-xl border border-brand/30 bg-brand/5 px-4 py-2 text-sm font-medium text-brand hover:bg-brand/10">
                去添加抬头
              </router-link>
            </div>
          </div>

          <div class="mt-5 flex gap-3">
            <button type="button" @click="showInvoiceModal = false" class="flex-1 rounded-xl border border-gray-200 py-2.5 text-sm text-gray-600 hover:bg-gray-50">关闭</button>
            <button
              v-if="!invoiceRequestForOrder && invoiceTitles.length"
              type="button"
              @click="handleInvoiceApply"
              :disabled="invoiceApplying"
              class="flex-1 rounded-xl bg-brand py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
            >
              {{ invoiceApplying ? '提交中…' : '提交开票' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Review modal -->
    <Teleport to="body">
      <div v-if="showReviewModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showReviewModal = false">
        <div class="w-full max-w-md rounded-2xl bg-white p-6 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-bold text-gray-900">评价入住体验</h3>
          <p class="mt-0.5 text-xs text-gray-400">{{ order.hotel_name }}</p>

          <!-- 星级评分 -->
          <div class="mt-4">
            <p class="mb-1.5 text-sm font-medium text-gray-700">总体评分</p>
            <div class="flex gap-1">
              <button v-for="s in 5" :key="s" type="button" @click="reviewScore = s"
                class="text-3xl leading-none transition-transform hover:scale-110"
                :class="s <= reviewScore ? 'text-yellow-400' : 'text-gray-200'">&#9733;</button>
              <span class="ml-2 self-center text-sm text-gray-500">{{ ['','很差','较差','一般','不错','很好'][reviewScore] }}</span>
            </div>
          </div>

          <!-- 评价内容 -->
          <div class="mt-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-700">评价内容</p>
              <span class="text-xs" :class="reviewCharCount >= 100 ? 'text-green-600 font-medium' : reviewCharCount >= 50 ? 'text-brand font-medium' : 'text-gray-400'">
                {{ reviewCharCount }}字
                <span v-if="reviewCharCount < 50">（50字起）</span>
              </span>
            </div>
            <textarea v-model="reviewContent" rows="4" maxlength="500"
              placeholder="分享您的入住体验，50字以上可获得积分奖励…"
              class="mt-1.5 w-full resize-none rounded-xl border border-gray-200 px-3 py-2.5 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
            <div class="mt-1 flex items-center justify-between">
              <div class="h-1 flex-1 overflow-hidden rounded-full bg-gray-100">
                <div class="h-full rounded-full transition-all duration-300"
                  :class="reviewCharCount >= 100 ? 'bg-green-500' : reviewCharCount >= 50 ? 'bg-brand' : 'bg-gray-300'"
                  :style="{ width: Math.min(reviewCharCount / 500 * 100, 100) + '%' }" />
              </div>
              <span class="ml-2 text-xs text-gray-400">{{ reviewCharCount }}/500</span>
            </div>
          </div>

          <!-- 图片上传 -->
          <div class="mt-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-700">上传图片 <span class="font-normal text-gray-400">（选填）</span></p>
              <span class="text-xs text-gray-400">{{ reviewImages.length }}/9</span>
            </div>
            <div class="mt-2 flex flex-wrap gap-2">
              <div v-for="(img, idx) in reviewImages" :key="idx" class="group relative h-20 w-20 overflow-hidden rounded-xl">
                <img :src="buildImageThumbUrl(img, 160, 160)" class="h-full w-full object-cover" loading="lazy" decoding="async" />
                <button type="button" @click="removeReviewImage(idx)"
                  class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition group-hover:opacity-100">
                  <span class="text-xl text-white">×</span>
                </button>
              </div>
              <label v-if="reviewImages.length < 9"
                class="flex h-20 w-20 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-gray-200 text-gray-400 transition hover:border-brand hover:text-brand"
                :class="uploadingImage ? 'opacity-50 pointer-events-none' : ''">
                <span class="text-2xl">{{ uploadingImage ? '…' : '+' }}</span>
                <span class="text-xs">添加图片</span>
                <input type="file" accept="image/*" multiple class="hidden" :disabled="uploadingImage" @change="handleReviewImageUpload" />
              </label>
            </div>
          </div>

          <!-- 积分预览 -->
          <div class="mt-4 rounded-xl bg-teal-50 px-3 py-2.5 text-xs text-teal-700">
            <p class="font-medium">可获积分：<span class="text-base font-bold text-brand">+{{ reviewPointsPreview }}</span> 分</p>
            <p class="mt-0.5 text-teal-600/70">50字→5分 · +图片→7分 · 100字+图片→10分（首次评价可奖励）</p>
          </div>

          <div class="mt-5 flex gap-3">
            <button type="button" @click="showReviewModal = false" class="flex-1 rounded-xl border border-gray-200 py-2.5 text-sm text-gray-600 hover:bg-gray-50">取消</button>
            <button type="button" @click="handleReview" :disabled="reviewing || !reviewContent.trim()"
              class="flex-1 rounded-xl bg-brand py-2.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-40">
              {{ reviewing ? '提交中…' : '提交评价' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { LocationQueryRaw } from 'vue-router'
import { userOrderApi, userReviewApi, commonApi, userInvoiceApi } from '@hotelink/api'
import type { InvoiceRequestItem, InvoiceTitleItem } from '@hotelink/api'
import { ORDER_STATUS_MAP, PAYMENT_METHOD_MAP, PAYMENT_STATUS_MAP, buildImageThumbUrl, extractApiError, formatMoney } from '@hotelink/utils'
import { OrderStepBar, SelectField, useToast } from '@hotelink/ui'

const { showToast } = useToast()

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.id)
const loading = ref(true)
const order = ref<any>({})
const error = ref('')

const showCancelModal = ref(false)
const cancelReason = ref('')
const cancelling = ref(false)

const showReviewModal = ref(false)
const reviewScore = ref(5)
const reviewContent = ref('')
const reviewImages = ref<string[]>([])
const reviewing = ref(false)
const uploadingImage = ref(false)
const reviewSuccessMsg = ref('')
const showInvoiceModal = ref(false)
const invoiceLoading = ref(false)
const invoiceApplying = ref(false)
const invoiceTitles = ref<InvoiceTitleItem[]>([])
const invoiceRequests = ref<InvoiceRequestItem[]>([])
const selectedInvoiceTitleId = ref(0)
const invoiceError = ref('')
let refreshTimer: number | null = null

const reviewCharCount = computed(() => reviewContent.value.trim().length)
const reviewPointsPreview = computed(() => {
  const len = reviewCharCount.value
  const hasImg = reviewImages.value.length > 0
  if (len >= 100 && hasImg) return 10
  if (len >= 50 && hasImg) return 7
  if (len >= 50) return 5
  return 0
})

const paymentMethodMap = PAYMENT_METHOD_MAP
const paymentStatusMap = PAYMENT_STATUS_MAP
const supportPhone = '4001234567'
const displayAmount = computed(() => formatMoney(order.value.pay_amount || order.value.total_amount || order.value.original_amount || 0))
const stayNights = computed(() => {
  const start = new Date(order.value.check_in_date)
  const end = new Date(order.value.check_out_date)
  const diff = end.getTime() - start.getTime()
  if (!Number.isFinite(diff) || diff <= 0) return 0
  return Math.max(1, Math.round(diff / 86400000))
})

// 根据状态值返回对应展示信息。
function statusLabel(s: string): string { return ORDER_STATUS_MAP[s]?.label || s || '未知' }
const canCancel = computed(() => ['pending_payment', 'paid', 'confirmed'].includes(order.value.status))
const canOpenInvoice = computed(() => order.value.status === 'completed')
const invoiceRequestForOrder = computed(() => invoiceRequests.value.find((item) => Number(item.order_id) === orderId))
const hotelDetailId = computed(() => {
  const parsed = Number(order.value.hotel_id ?? order.value.hotel ?? 0)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
})
const hotelDetailPath = computed(() => (hotelDetailId.value ? `/hotels/${hotelDetailId.value}` : ''))
// 订单详情跳转会携带 order_id，便于酒店已下线时展示历史订单关联信息。
const hotelDetailQuery = computed<LocationQueryRaw>(() => (
  hotelDetailId.value
    ? { from: 'order_detail', order_id: String(orderId) }
    : {}
))
const hotelDetailRoute = computed(() => (
  hotelDetailPath.value
    ? { path: hotelDetailPath.value, query: hotelDetailQuery.value }
    : '/'
))
const showRebook = computed(() => hotelDetailId.value > 0 && ['completed', 'cancelled', 'refunded'].includes(order.value.status))
const showActionBar = computed(() => (
  order.value.status === 'pending_payment'
  || canCancel.value
  || (order.value.status === 'completed' && !order.value.has_review)
  || showRebook.value
))

type ChangeEventType = 'extend' | 'switch' | 'checkin' | 'checkout' | 'rollback' | 'warning' | 'other'

interface ChangeEventItem {
  type: ChangeEventType
  tag: string
  text: string
  time?: string
}

function classifyChangeEvent(text: string): ChangeEventItem {
  const normalized = text.toLowerCase()
  if (normalized.includes('续住')) {
    return { type: 'extend', tag: '续住', text }
  }
  if (normalized.includes('换房')) {
    return { type: 'switch', tag: '换房', text }
  }
  if (normalized.includes('入住')) {
    return { type: 'checkin', tag: '入住', text }
  }
  if (normalized.includes('退房')) {
    return { type: 'checkout', tag: '退房', text }
  }
  if (normalized.includes('回滚') || normalized.includes('撤销') || normalized.includes('纠正') || normalized.includes('回退')) {
    return { type: 'rollback', tag: '回滚/纠正', text }
  }
  if (normalized.includes('异常')) {
    return { type: 'warning', tag: '异常', text }
  }
  return { type: 'other', tag: '变更', text }
}

const changeEvents = computed<ChangeEventItem[]>(() => {
  const events: ChangeEventItem[] = []

  const warning = String(order.value?.lifecycle_warning || '').trim()
  if (warning) {
    events.push({ type: 'warning', tag: '异常', text: warning, time: order.value?.updated_at })
  }

  const operatorRemark = String(order.value?.operator_remark || '').trim()
  if (operatorRemark) {
    const parts = operatorRemark
      .split(/[；;\n]+/)
      .map((item) => item.trim())
      .filter(Boolean)
    for (const part of parts) {
      const classified = classifyChangeEvent(part)
      events.push({ ...classified, time: order.value?.updated_at })
    }
  }

  return events
})

const hasRollbackEvent = computed(() => changeEvents.value.some((item) => item.type === 'rollback'))

function openHotelDetail() {
  if (!hotelDetailPath.value) return
  router.push(hotelDetailRoute.value)
}

function askAiCustomerService() {
  const ask = `我想咨询订单 ${order.value.order_no} 的取消和入住相关问题，请帮我看看。`
  router.push({
    path: '/ai-chat',
    query: {
      ask,
      source_scene: 'order_detail',
      intent: 'cancel_order',
      order_id: String(orderId),
      hotel_id: String(hotelDetailId.value || ''),
    },
  })
}

// 处理 goToPay 业务流程。
function goToPay() { router.push(`/payment/${orderId}`) }

function invoiceStatusLabel(invoice: InvoiceRequestItem): string {
  return invoice.status_label || (invoice.status === 'issued' ? '已开票' : invoice.status === 'cancelled' ? '已取消' : '待处理')
}

function invoiceStatusClass(status: InvoiceRequestItem['status']): string {
  if (status === 'issued') return 'bg-emerald-100 text-emerald-700'
  if (status === 'cancelled') return 'bg-slate-100 text-slate-600'
  return 'bg-amber-100 text-amber-700'
}

async function loadInvoiceCenter(options: { silent?: boolean } = {}) {
  invoiceLoading.value = true
  try {
    const res = await userInvoiceApi.list()
    if (res.code === 0 && res.data) {
      invoiceTitles.value = res.data.titles || []
      invoiceRequests.value = res.data.items || []
      if (!selectedInvoiceTitleId.value && invoiceTitles.value.length) {
        selectedInvoiceTitleId.value = invoiceTitles.value[0].id
      }
    } else if (!options.silent) {
      showToast(res.message || '发票信息加载失败', 'error')
    }
  } catch {
    if (!options.silent) {
      showToast('发票信息加载失败，请稍后重试', 'error')
    }
  } finally {
    invoiceLoading.value = false
  }
}

async function openInvoiceModal() {
  showInvoiceModal.value = true
  invoiceError.value = ''
  await loadInvoiceCenter({ silent: true })
}

async function handleInvoiceApply() {
  if (!selectedInvoiceTitleId.value) {
    invoiceError.value = '请选择发票抬头'
    showToast('请选择发票抬头', 'warning')
    return
  }

  invoiceApplying.value = true
  try {
    // Backend validates ownership, order status, and duplicate invoice requests.
    const res = await userInvoiceApi.apply({
      order_id: orderId,
      invoice_title_id: selectedInvoiceTitleId.value,
    })
    if (res.code === 0) {
      showToast('发票申请已提交', 'success')
      showInvoiceModal.value = false
      await loadInvoiceCenter({ silent: true })
    } else {
      invoiceError.value = extractApiError(res, '发票申请失败，请稍后重试')
      showToast(invoiceError.value, 'error')
    }
  } catch {
    invoiceError.value = '发票申请失败，请检查网络后重试'
    showToast(invoiceError.value, 'error')
  } finally {
    invoiceApplying.value = false
  }
}

function consumeAssistantActionQuery() {
  const source = typeof route.query.source === 'string' ? route.query.source : ''
  const action = typeof route.query.action === 'string' ? route.query.action : ''
  if (source !== 'ai') return

  if (action === 'cancel') {
    if (canCancel.value) {
      if (!cancelReason.value.trim()) {
        cancelReason.value = 'AI 助手协助发起取消'
      }
      showCancelModal.value = true
      showToast('已为您打开取消流程，请确认后提交', 'success')
    } else {
      showToast('当前订单状态不可取消，已为您展示订单详情', 'warning')
    }
  }

  const nextQuery: LocationQueryRaw = { ...route.query }
  delete nextQuery.source
  delete nextQuery.action
  delete nextQuery.intent
  delete nextQuery.order_id
  router.replace({ path: route.path, query: nextQuery })
}

async function handleReviewImageUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length) return
  uploadingImage.value = true
  try {
    for (const file of Array.from(files)) {
      if (reviewImages.value.length >= 9) break
      const res = await commonApi.upload(file, 'review')
      if (res.code === 0 && res.data) {
        reviewImages.value.push((res.data as any).file_url as string)
      } else {
        showToast(res.message || '图片上传失败，请重试', 'error')
      }
    }
    if (reviewImages.value.length > 0) {
      showToast('图片上传完成', 'success')
    }
  } catch {
    showToast('图片上传失败，请检查网络后重试', 'error')
  }
  uploadingImage.value = false
  ;(e.target as HTMLInputElement).value = ''
}

function removeReviewImage(idx: number) { reviewImages.value.splice(idx, 1) }

// 处理 Cancel 交互逻辑。
async function handleCancel() {
  cancelling.value = true
  try {
    const res = await userOrderApi.cancel({ order_id: orderId, reason: cancelReason.value || '用户取消' })
    if (res.code === 0) {
      showCancelModal.value = false
      showToast('订单已取消', 'success')
      // 重新拉取完整订单数据，确保 payment_status 等字段同步
      try {
        const detail = await userOrderApi.detail(orderId)
        if (detail.code === 0 && detail.data) {
          order.value = detail.data
        }
      } catch { /* fallback: 至少更新状态 */ }
      if (order.value.status !== 'cancelled') order.value.status = 'cancelled'
    } else {
      showToast(res.message || '取消订单失败，请重试', 'error')
    }
  } catch {
    showToast('取消订单失败，请检查网络后重试', 'error')
  }
  cancelling.value = false
}

// 处理 Review 交互逻辑。
async function handleReview() {
  if (!reviewContent.value.trim()) {
    showToast('请输入评价内容后再提交', 'warning')
    return
  }
  reviewing.value = true
  try {
    const res = await userReviewApi.create({
      order_id: orderId,
      score: reviewScore.value,
      content: reviewContent.value,
      images: reviewImages.value,
    })
    if (res.code === 0) {
      order.value.has_review = true
      showReviewModal.value = false
      reviewImages.value = []
      const pts = (res.data as any)?.points_awarded ?? 0
      if (pts > 0) {
        reviewSuccessMsg.value = `评价成功！奖励 +${pts} 积分`
        setTimeout(() => { reviewSuccessMsg.value = '' }, 4000)
      }
      showToast(pts > 0 ? `评价成功，奖励 +${pts} 积分` : '评价提交成功', 'success')
    } else {
      showToast(res.message || '评价提交失败，请稍后重试', 'error')
    }
  } catch {
    showToast('评价提交失败，请检查网络后重试', 'error')
  }
  reviewing.value = false
}

function refreshOrderIfVisible() {
  if (!document.hidden && !loading.value && orderId) {
    userOrderApi.detail(orderId)
      .then((res) => {
        if (res.code === 0 && res.data) {
          order.value = res.data
        }
      })
      .catch(() => {})
  }
}

onMounted(async () => {
  try {
    const res = await userOrderApi.detail(orderId)
    if (res.code === 0 && res.data) {
      order.value = res.data
      if (order.value.status === 'completed') {
        loadInvoiceCenter({ silent: true })
      }
      consumeAssistantActionQuery()
    } else {
      order.value = {}
      error.value = res.message || '订单详情加载失败，请稍后重试'
    }
  } catch {
    order.value = {}
    error.value = '订单详情加载失败，请稍后重试'
    showToast('订单详情加载失败，请稍后重试', 'error')
  } finally {
    loading.value = false
  }
})

onMounted(() => {
  window.addEventListener('focus', refreshOrderIfVisible)
  document.addEventListener('visibilitychange', refreshOrderIfVisible)
  refreshTimer = window.setInterval(refreshOrderIfVisible, 90000)
})

onBeforeUnmount(() => {
  window.removeEventListener('focus', refreshOrderIfVisible)
  document.removeEventListener('visibilitychange', refreshOrderIfVisible)
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

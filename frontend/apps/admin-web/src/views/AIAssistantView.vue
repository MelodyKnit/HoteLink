<template>
  <section>
    <PageHeader title="AI 助手" subtitle="智能分析、内容生成与运营洞察" />

    <!-- Tab 导航 -->
    <div class="mb-6 flex flex-wrap gap-2 border-b border-slate-200">
      <button
        v-for="tab in TABS"
        :key="tab.id"
        class="px-4 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
        :class="activeTab === tab.id
          ? 'border-teal-500 text-teal-600 bg-teal-50/60'
          : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-100'"
        @click="activeTab = tab.id"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- ① 营收报告分析 -->
    <div v-if="activeTab === 'report'" class="grid gap-6 lg:grid-cols-2">
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-sm font-semibold text-slate-700">📊 营收报告分析</h3>
        <form class="space-y-4" @submit.prevent="getReportSummary">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">酒店（可选）</label>
            <SelectField v-model="reportForm.hotel_id" class="w-full">
              <option value="">全部酒店</option>
              <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
            </SelectField>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-600">开始日期</label>
              <input v-model="reportForm.start_date" type="date" required class="input-field" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-600">结束日期</label>
              <input v-model="reportForm.end_date" type="date" required class="input-field" />
            </div>
          </div>
          <button type="submit" class="btn-primary w-full" :disabled="reportLoading">
            {{ reportLoading ? '分析中…' : '🔍 生成报告分析' }}
          </button>
        </form>
        <div v-if="reportResult" class="mt-4 rounded-xl bg-teal-50 p-4 text-sm text-teal-900 whitespace-pre-wrap leading-relaxed">{{ reportResult }}</div>
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-4 text-sm font-semibold text-slate-700">💬 评价总结分析</h3>
        <form class="space-y-4" @submit.prevent="getReviewSummary">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">酒店（可选）</label>
            <SelectField v-model="reviewForm.hotel_id" class="w-full">
              <option value="">全部酒店</option>
              <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
            </SelectField>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-600">开始日期</label>
              <input v-model="reviewForm.start_date" type="date" required class="input-field" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-600">结束日期</label>
              <input v-model="reviewForm.end_date" type="date" required class="input-field" />
            </div>
          </div>
          <button type="submit" class="btn-primary w-full bg-indigo-600 hover:bg-indigo-700" :disabled="reviewLoading">
            {{ reviewLoading ? '分析中…' : '🔍 生成评价总结' }}
          </button>
        </form>
        <div v-if="reviewResult" class="mt-4 rounded-xl bg-indigo-50 p-4 text-sm text-indigo-900 whitespace-pre-wrap leading-relaxed">{{ reviewResult }}</div>
      </div>
    </div>

    <!-- ② 智能定价建议 -->
    <div v-if="activeTab === 'pricing'" class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h3 class="mb-1 text-sm font-semibold text-slate-700">💰 AI 智能定价建议</h3>
      <p class="mb-4 text-xs text-slate-500">根据历史入住率、竞品价格和节假日因素，生成每日价格建议。</p>
      <form class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" @submit.prevent="getPricingSuggestion">
        <div class="sm:col-span-2 lg:col-span-1">
          <label class="mb-1 block text-xs font-medium text-slate-600">选择房型 <span class="text-red-500">*</span></label>
          <SelectField v-model="pricingForm.room_type_id" class="w-full" required>
            <option value="">请选择房型</option>
            <option v-for="rt in roomTypes" :key="rt.id" :value="rt.id">{{ rt.hotel_name }} - {{ rt.name }}</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">开始日期 <span class="text-red-500">*</span></label>
          <input v-model="pricingForm.start_date" type="date" required class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">结束日期 <span class="text-red-500">*</span></label>
          <input v-model="pricingForm.end_date" type="date" required class="input-field" />
        </div>
        <div class="flex items-center gap-2 pt-5">
          <input v-model="pricingForm.use_reasoning" type="checkbox" id="pricingReasoning" class="h-4 w-4 rounded border-slate-300 text-teal-600" />
          <label for="pricingReasoning" class="text-xs text-slate-600">深度推理模式（更准确但更慢）</label>
        </div>
        <div class="sm:col-span-2 lg:col-span-3">
          <button type="submit" class="btn-primary px-6" :disabled="pricingLoading">
            {{ pricingLoading ? '计算中…' : '💡 生成定价建议' }}
          </button>
        </div>
      </form>
      <div v-if="pricingResult" class="mt-6">
        <div class="mb-3 flex items-center gap-2">
          <span class="text-sm font-semibold text-slate-700">定价建议结果</span>
          <span class="rounded-full bg-teal-100 px-2 py-0.5 text-xs text-teal-700">{{ pricingResult.suggestions.length }} 天</span>
        </div>
        <div class="overflow-x-auto rounded-xl border border-slate-200">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th class="px-4 py-2.5 text-left font-medium">日期</th>
                <th class="px-4 py-2.5 text-right font-medium">建议价格</th>
                <th class="px-4 py-2.5 text-left font-medium">定价依据</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="s in pricingResult.suggestions" :key="s.date" class="hover:bg-slate-50">
                <td class="px-4 py-2.5 font-mono text-slate-700">{{ s.date }}</td>
                <td class="px-4 py-2.5 text-right font-semibold text-teal-700">¥{{ s.suggested_price }}</td>
                <td class="px-4 py-2.5 text-slate-500 text-xs">{{ s.reason }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ③ 深度经营报告（流式） -->
    <div v-if="activeTab === 'bizreport'" class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h3 class="mb-1 text-sm font-semibold text-slate-700">📈 深度经营报告</h3>
      <p class="mb-4 text-xs text-slate-500">多维度分析营收、订单、评价、会员等数据，生成 Markdown 格式完整报告（支持流式输出）。</p>
      <form class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" @submit.prevent="getBusinessReport">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">酒店（可选）</label>
          <SelectField v-model="bizForm.hotel_id" class="w-full">
            <option value="">全部酒店</option>
            <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">开始日期 <span class="text-red-500">*</span></label>
          <input v-model="bizForm.start_date" type="date" required class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">结束日期 <span class="text-red-500">*</span></label>
          <input v-model="bizForm.end_date" type="date" required class="input-field" />
        </div>
        <div class="flex items-end gap-2 pb-0.5">
          <div class="flex items-center gap-1.5">
            <input v-model="bizForm.use_reasoning" type="checkbox" id="bizReasoning" class="h-4 w-4 rounded" />
            <label for="bizReasoning" class="text-xs text-slate-600">深度推理</label>
          </div>
          <div class="flex items-center gap-1.5">
            <input v-model="bizForm.streaming" type="checkbox" id="bizStream" class="h-4 w-4 rounded" />
            <label for="bizStream" class="text-xs text-slate-600">流式输出</label>
          </div>
        </div>
        <div class="sm:col-span-2 lg:col-span-4">
          <div class="mb-2 flex flex-wrap gap-2">
            <span class="text-xs text-slate-500">分析维度：</span>
            <label v-for="d in DIMENSION_OPTIONS" :key="d.value" class="flex items-center gap-1.5 text-xs">
              <input v-model="bizForm.dimensions" type="checkbox" :value="d.value" class="h-3.5 w-3.5 rounded" />
              {{ d.label }}
            </label>
          </div>
          <button type="submit" class="btn-primary px-6" :disabled="bizLoading">
            {{ bizLoading ? '生成中…' : '📋 生成经营报告' }}
          </button>
        </div>
      </form>
      <div v-if="bizResult || bizStreaming" class="mt-6 rounded-xl bg-slate-50 p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium text-slate-600">📄 报告内容</span>
          <span v-if="bizStreaming" class="flex items-center gap-1 text-xs text-teal-600">
            <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-teal-500" />
            生成中...
          </span>
        </div>
        <pre class="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed font-mono max-h-[500px] overflow-y-auto">{{ bizResult }}</pre>
      </div>
    </div>

    <!-- ④ 评价情感分析 -->
    <div v-if="activeTab === 'sentiment'" class="grid gap-6 lg:grid-cols-5">
      <div class="lg:col-span-2 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-1 text-sm font-semibold text-slate-700">🎭 评价情感分析</h3>
        <p class="mb-4 text-xs text-slate-500">对单条评价进行 AI 情感分析，获取情感分值、标签和关键词。</p>
        <form class="space-y-4" @submit.prevent="getSentiment">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">选择评价</label>
            <SelectField v-model="sentimentForm.review_id" class="w-full">
              <option value="">快速选择最近评价</option>
              <option v-for="r in recentReviews" :key="r.id" :value="r.id">
                #{{ r.id }} {{ r.hotel_name }} - {{ r.score }}星 - {{ (r.content || '').slice(0, 20) }}…
              </option>
            </SelectField>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">或直接输入评价ID</label>
            <input v-model.number="sentimentForm.review_id" type="number" min="1" placeholder="评价 ID" class="input-field" />
          </div>
          <button type="submit" class="btn-primary w-full" :disabled="sentimentLoading">
            {{ sentimentLoading ? '分析中…' : '🔬 分析情感' }}
          </button>
        </form>
      </div>
      <div class="lg:col-span-3">
        <div v-if="sentimentResult" class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-slate-700">分析结果</span>
            <span
              class="rounded-full px-3 py-1 text-xs font-semibold"
              :class="{
                'bg-green-100 text-green-700': sentimentResult.label === 'positive',
                'bg-red-100 text-red-700': sentimentResult.label === 'negative',
                'bg-slate-100 text-slate-700': sentimentResult.label === 'neutral',
              }"
            >
              {{ { positive: '正面', negative: '负面', neutral: '中性' }[sentimentResult.label] || sentimentResult.label }}
            </span>
          </div>
          <!-- Score Bar -->
          <div>
            <div class="mb-1 flex justify-between text-xs text-slate-500">
              <span>情感得分</span>
              <span class="font-semibold text-slate-700">{{ sentimentResult.score.toFixed(2) }}</span>
            </div>
            <div class="h-2 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                class="h-full rounded-full transition-all"
                :class="sentimentResult.score >= 0.6 ? 'bg-green-500' : sentimentResult.score >= 0.4 ? 'bg-yellow-400' : 'bg-red-500'"
                :style="{ width: `${sentimentResult.score * 100}%` }"
              />
            </div>
          </div>
          <div>
            <p class="mb-2 text-xs font-medium text-slate-600">关键词</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="k in sentimentResult.keywords" :key="k" class="rounded-full bg-teal-50 px-2.5 py-1 text-xs text-teal-700">{{ k }}</span>
            </div>
          </div>
          <div>
            <p class="mb-2 text-xs font-medium text-slate-600">自动标签</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="t in sentimentResult.tags" :key="t" class="rounded-full bg-blue-50 px-2.5 py-1 text-xs text-blue-700">{{ t }}</span>
            </div>
          </div>
          <div>
            <p class="mb-1.5 text-xs font-medium text-slate-600">情感摘要</p>
            <p class="text-sm text-slate-700 leading-relaxed">{{ sentimentResult.summary }}</p>
          </div>
        </div>
        <div v-else class="flex h-48 items-center justify-center rounded-2xl border-2 border-dashed border-slate-200">
          <p class="text-sm text-slate-400">情感分析结果将在这里显示</p>
        </div>
      </div>
    </div>

    <!-- ⑤ 营销文案生成 -->
    <div v-if="activeTab === 'marketing'" class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h3 class="mb-1 text-sm font-semibold text-slate-700">✍️ AI 营销文案生成</h3>
      <p class="mb-4 text-xs text-slate-500">根据酒店特色和文案类型，批量生成适用于不同渠道的营销文案。</p>
      <form class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" @submit.prevent="getMarketingCopy">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">酒店（可选）</label>
          <SelectField v-model="marketingForm.hotel_id" class="w-full">
            <option value="">平台通用</option>
            <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">文案类型 <span class="text-red-500">*</span></label>
          <SelectField v-model="marketingForm.copy_type" class="w-full" required>
            <option value="">请选择</option>
            <option v-for="ct in COPY_TYPE_OPTIONS" :key="ct.value" :value="ct.value">{{ ct.label }}</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">文案风格</label>
          <SelectField v-model="marketingForm.style" class="w-full">
            <option value="formal">正式专业</option>
            <option value="casual">轻松活泼</option>
            <option value="literary">文艺清新</option>
            <option value="concise">简洁有力</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">目标受众</label>
          <input v-model="marketingForm.target_audience" type="text" placeholder="如：商务旅客、家庭出游..." class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">关键词（逗号分隔）</label>
          <input v-model="marketingForm.keywords_str" type="text" placeholder="如：豪华、景观、泳池" class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">补充信息</label>
          <input v-model="marketingForm.extra_notes" type="text" placeholder="活动详情、特别说明..." class="input-field" />
        </div>
        <div class="sm:col-span-2 lg:col-span-3">
          <button type="submit" class="btn-primary px-6" :disabled="marketingLoading">
            {{ marketingLoading ? '生成中…' : '✨ 生成营销文案' }}
          </button>
        </div>
      </form>
      <div v-if="marketingResult.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="(copy, i) in marketingResult" :key="i" class="rounded-xl border border-slate-200 p-4 hover:border-teal-300 transition-colors">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-xs font-semibold text-teal-700">{{ copy.title }}</span>
            <button @click="copyToClipboard(copy.content)" class="text-xs text-slate-400 hover:text-teal-600">📋 复制</button>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">{{ copy.content }}</p>
          <div v-if="copy.tags?.length" class="mt-3 flex flex-wrap gap-1">
            <span v-for="t in copy.tags" :key="t" class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ⑥ 内容生成 -->
    <div v-if="activeTab === 'content'" class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h3 class="mb-1 text-sm font-semibold text-slate-700">📝 AI 内容生成</h3>
      <p class="mb-4 text-xs text-slate-500">智能生成酒店/房型描述文案、SEO 关键词等内容，可多版本对比选优。</p>
      <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="getContent">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">内容类型 <span class="text-red-500">*</span></label>
          <SelectField v-model="contentForm.content_type" class="w-full">
            <option value="hotel_description">酒店描述</option>
            <option value="room_description">房型描述</option>
            <option value="seo_keywords">SEO 关键词</option>
          </SelectField>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">生成数量</label>
          <SelectField v-model.number="contentForm.count" class="w-full">
            <option :value="1">1 个版本</option>
            <option :value="2">2 个版本</option>
            <option :value="3">3 个版本（推荐）</option>
            <option :value="5">5 个版本</option>
          </SelectField>
        </div>
        <div class="sm:col-span-2">
          <label class="mb-1 block text-xs font-medium text-slate-600">背景信息（JSON 格式）</label>
          <textarea
            v-model="contentForm.context_str"
            rows="4"
            class="input-field font-mono text-xs"
            placeholder='{"name":"酒店名称","city":"上海","star":5,"features":["泳池","健身房"]}'
          />
        </div>
        <div class="sm:col-span-2">
          <button type="submit" class="btn-primary px-6" :disabled="contentLoading">
            {{ contentLoading ? '生成中…' : '📝 生成内容' }}
          </button>
        </div>
      </form>
      <div v-if="contentResult.length" class="mt-6 space-y-4">
        <div v-for="(item, i) in contentResult" :key="i" class="rounded-xl border border-slate-200 p-4">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-600">版本 {{ i + 1 }}</span>
            <button @click="copyToClipboard(item.content)" class="text-xs text-slate-400 hover:text-teal-600">📋 复制</button>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">{{ item.content }}</p>
          <div v-if="item.highlights?.length" class="mt-3 flex flex-wrap gap-1.5">
            <span v-for="h in item.highlights" :key="h" class="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs text-amber-700">⭐ {{ h }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ⑦ 异常检测 -->
    <div v-if="activeTab === 'anomaly'" class="grid gap-6 lg:grid-cols-2">
      <!-- 酒店运营异常 -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-1 text-sm font-semibold text-slate-700">🚨 酒店运营异常检测</h3>
        <p class="mb-4 text-xs text-slate-500">自动检测入住率过低、评分异常下降、取消率飙升等运营风险。</p>
        <form class="space-y-3" @submit.prevent="getAnomalyReport">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">酒店（可选）</label>
            <SelectField v-model="anomalyForm.hotel_id" class="w-full">
              <option value="">全部酒店</option>
              <option v-for="h in hotels" :key="h.id" :value="h.id">{{ h.name }}</option>
            </SelectField>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">分析日期（默认今日）</label>
            <input v-model="anomalyForm.date" type="date" class="input-field" />
          </div>
          <button type="submit" class="btn-primary w-full" :disabled="anomalyLoading">
            {{ anomalyLoading ? '检测中…' : '🔍 开始检测' }}
          </button>
        </form>
        <div v-if="anomalyResult" class="mt-4 space-y-3">
          <div
            v-for="(a, i) in anomalyResult.anomalies"
            :key="i"
            class="rounded-lg p-3 text-sm"
            :class="{ 'bg-red-50 border border-red-200': a.level === 'high', 'bg-amber-50 border border-amber-200': a.level === 'medium', 'bg-slate-50 border border-slate-200': a.level === 'low' }"
          >
            <div class="flex items-center gap-2 mb-1">
              <span class="font-semibold" :class="{ 'text-red-700': a.level === 'high', 'text-amber-700': a.level === 'medium', 'text-slate-600': a.level === 'low' }">
                {{ a.level === 'high' ? '🔴' : a.level === 'medium' ? '🟡' : '🟢' }} {{ a.type }}
              </span>
            </div>
            <p class="text-slate-600 text-xs leading-relaxed">{{ a.description }}</p>
          </div>
          <div v-if="anomalyResult.summary" class="rounded-lg bg-teal-50 p-3 text-xs text-teal-800 leading-relaxed">
            <p class="font-semibold mb-1">AI 综合建议</p>
            {{ anomalyResult.summary }}
          </div>
          <div v-if="!anomalyResult.anomalies.length" class="rounded-lg bg-green-50 p-3 text-sm text-green-700 text-center">
            ✅ 未检测到明显异常
          </div>
        </div>
      </div>

      <!-- 订单异常摘要 -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 class="mb-1 text-sm font-semibold text-slate-700">📦 订单异常摘要</h3>
        <p class="mb-4 text-xs text-slate-500">统计逾期未支付、异常取消、超时未入住等订单风险。</p>
        <form class="space-y-3" @submit.prevent="getOrderAnomalySummary">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">分析日期（默认今日）</label>
            <input v-model="orderAnomalyForm.date" type="date" class="input-field" />
          </div>
          <button type="submit" class="btn-primary w-full bg-orange-500 hover:bg-orange-600" :disabled="orderAnomalyLoading">
            {{ orderAnomalyLoading ? '统计中…' : '📊 获取摘要' }}
          </button>
        </form>
        <div v-if="orderAnomalyResult" class="mt-4 space-y-3">
          <div v-for="(a, i) in orderAnomalyResult.anomalies" :key="i" class="rounded-lg bg-orange-50 border border-orange-200 p-3">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-semibold text-orange-800">{{ a.type }}</span>
              <span class="rounded-full bg-orange-200 px-2 py-0.5 text-xs font-bold text-orange-800">{{ a.count }} 笔</span>
            </div>
          </div>
          <div v-if="orderAnomalyResult.summary" class="rounded-lg bg-orange-50 p-3 text-xs text-orange-800 leading-relaxed">
            <p class="font-semibold mb-1">AI 摘要</p>
            {{ orderAnomalyResult.summary }}
          </div>
          <div v-if="!orderAnomalyResult.anomalies.length" class="rounded-lg bg-green-50 p-3 text-sm text-green-700 text-center">
            ✅ 无订单异常
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { aiApi, hotelApi, roomTypeApi } from '@hotelink/api'
import { reviewApi } from '@hotelink/api'
import { PageHeader, SelectField, useToast } from '@hotelink/ui'

const { showToast } = useToast()

// ──────────────────────── Types ────────────────────────
interface HotelOption { id: number; name: string }
interface RoomTypeOption { id: number; name: string; hotel_name: string }
interface ReviewOption { id: number; hotel_name: string; score: number; content: string }

// ──────────────────────── Static config ────────────────────────
const TABS = [
  { id: 'report', icon: '📊', label: '报告分析' },
  { id: 'pricing', icon: '💰', label: '智能定价' },
  { id: 'bizreport', icon: '📈', label: '深度报告' },
  { id: 'sentiment', icon: '🎭', label: '情感分析' },
  { id: 'marketing', icon: '✍️', label: '营销文案' },
  { id: 'content', icon: '📝', label: '内容生成' },
  { id: 'anomaly', icon: '🚨', label: '异常检测' },
]
const DIMENSION_OPTIONS = [
  { value: 'revenue', label: '营收' },
  { value: 'orders', label: '订单' },
  { value: 'reviews', label: '评价' },
  { value: 'occupancy', label: '入住率' },
  { value: 'members', label: '会员' },
]
const COPY_TYPE_OPTIONS = [
  { value: 'hotel_promo', label: '酒店促销' },
  { value: 'holiday_promo', label: '节假日活动' },
  { value: 'member_activity', label: '会员专属' },
  { value: 'seasonal_promo', label: '季节促销' },
  { value: 'social_media', label: '社交媒体' },
]

// ──────────────────────── Shared state ────────────────────────
const activeTab = ref('report')
const today = new Date()
const thirtyDaysAgo = new Date(today.getTime() - 30 * 86400000)
const defaultStart = thirtyDaysAgo.toISOString().slice(0, 10)
const defaultEnd = today.toISOString().slice(0, 10)

const hotels = ref<HotelOption[]>([])
const roomTypes = ref<RoomTypeOption[]>([])
const recentReviews = ref<ReviewOption[]>([])

// ──────────────────────── Error helper ────────────────────────
function showApiError(res: { message?: string; data?: unknown }, fallback = '请求失败') {
  const d = res.data as Record<string, unknown> | null
  if (d?.errors) {
    const errs = d.errors as Record<string, string[]>
    const msg = Object.entries(errs).map(([k, v]) => `${k}: ${v.join(', ')}`).join('；')
    showToast(msg, 'error')
  } else {
    showToast(res.message || fallback, 'error')
  }
}

async function loadHotels() {
  try {
    const res = await hotelApi.list({ page: 1, page_size: 200 })
    if (res.code === 0 && res.data) {
      hotels.value = ((res.data as { items: HotelOption[] }).items || []).map((item: HotelOption) => ({ id: Number(item.id), name: String(item.name || '') }))
    } else {
      showToast(res.message || '酒店列表加载失败，请稍后重试', 'error')
    }
  } catch {
    showToast('酒店列表加载失败，请检查网络后重试', 'error')
  }
}
async function loadRoomTypes() {
  try {
    const res = await roomTypeApi.list({ page: 1, page_size: 200 })
    if (res.code === 0 && res.data) {
      roomTypes.value = ((res.data as { items: RoomTypeOption[] }).items || []).map((item: RoomTypeOption) => ({
        id: Number(item.id),
        name: String(item.name || ''),
        hotel_name: String((item as unknown as Record<string, unknown>).hotel_name || ''),
      }))
    } else {
      showToast(res.message || '房型列表加载失败，请稍后重试', 'error')
    }
  } catch {
    showToast('房型列表加载失败，请检查网络后重试', 'error')
  }
}
async function loadRecentReviews() {
  try {
    const res = await reviewApi.list({ page: 1, page_size: 50, ordering: '-created_at' })
    if (res.code === 0 && res.data) {
      recentReviews.value = ((res.data as { items: ReviewOption[] }).items || []).map((r: ReviewOption) => ({
        id: Number(r.id),
        hotel_name: String((r as unknown as Record<string, unknown>).hotel_name || ''),
        score: Number(r.score),
        content: String(r.content || ''),
      }))
    } else {
      showToast(res.message || '近期评价加载失败，请稍后重试', 'error')
    }
  } catch {
    showToast('近期评价加载失败，请检查网络后重试', 'error')
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).then(() => showToast('已复制到剪贴板', 'success'))
}

// ──────────────────────── Tab 1: Report / Review Summary ────────────────────────
const reportForm = reactive({ hotel_id: '' as string | number, start_date: defaultStart, end_date: defaultEnd })
const reportLoading = ref(false)
const reportResult = ref('')

async function getReportSummary() {
  if (!reportForm.start_date || !reportForm.end_date) { showToast('请选择日期范围', 'error'); return }
  reportLoading.value = true
  reportResult.value = ''
  try {
    const payload: Record<string, unknown> = { start_date: reportForm.start_date, end_date: reportForm.end_date }
    if (reportForm.hotel_id) payload.hotel_id = reportForm.hotel_id
    const res = await aiApi.reportSummary(payload)
    if (res.code === 0 && res.data) {
      reportResult.value = (res.data as Record<string, unknown>).summary as string || '暂无分析结果'
      showToast('报告分析完成', 'success')
    } else {
      showApiError(res, '报告分析失败')
    }
  } catch (e) {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    reportLoading.value = false
  }
}

const reviewForm = reactive({ hotel_id: '' as string | number, start_date: defaultStart, end_date: defaultEnd })
const reviewLoading = ref(false)
const reviewResult = ref('')

async function getReviewSummary() {
  if (!reviewForm.start_date || !reviewForm.end_date) { showToast('请选择日期范围', 'error'); return }
  reviewLoading.value = true
  reviewResult.value = ''
  try {
    const payload: Record<string, unknown> = { start_date: reviewForm.start_date, end_date: reviewForm.end_date }
    if (reviewForm.hotel_id) payload.hotel_id = reviewForm.hotel_id
    const res = await aiApi.reviewSummary(payload)
    if (res.code === 0 && res.data) {
      reviewResult.value = (res.data as Record<string, unknown>).summary as string || '暂无分析结果'
      showToast('评价总结已生成', 'success')
    } else {
      showApiError(res, '评价总结失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    reviewLoading.value = false
  }
}

// ──────────────────────── Tab 2: Pricing Suggestion ────────────────────────
const pricingForm = reactive({
  room_type_id: '' as string | number,
  start_date: defaultEnd,
  end_date: new Date(today.getTime() + 7 * 86400000).toISOString().slice(0, 10),
  use_reasoning: false,
})
const pricingLoading = ref(false)
const pricingResult = ref<{ suggestions: { date: string; suggested_price: number; reason: string }[] } | null>(null)

async function getPricingSuggestion() {
  if (!pricingForm.room_type_id) { showToast('请选择房型', 'error'); return }
  if (!pricingForm.start_date || !pricingForm.end_date) { showToast('请选择日期范围', 'error'); return }
  if (pricingForm.start_date > pricingForm.end_date) { showToast('开始日期不能晚于结束日期', 'error'); return }
  pricingLoading.value = true
  pricingResult.value = null
  try {
    const start = new Date(pricingForm.start_date)
    const end = new Date(pricingForm.end_date)
    const dates: string[] = []
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      dates.push(d.toISOString().slice(0, 10))
    }
    if (dates.length > 30) { showToast('日期范围不能超过 30 天', 'error'); return }
    const res = await aiApi.pricingSuggestion({
      room_type_id: Number(pricingForm.room_type_id),
      target_dates: dates,
      use_reasoning: pricingForm.use_reasoning,
    })
    if (res.code === 0 && res.data) {
      pricingResult.value = res.data as { suggestions: { date: string; suggested_price: number; reason: string }[] }
      showToast('定价建议已生成', 'success')
    } else {
      showApiError(res, '定价建议失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    pricingLoading.value = false
  }
}

// ──────────────────────── Tab 3: Business Report ────────────────────────
const bizForm = reactive({
  hotel_id: '' as string | number,
  start_date: defaultStart,
  end_date: defaultEnd,
  dimensions: ['revenue', 'orders', 'reviews'] as string[],
  use_reasoning: false,
  streaming: true,
})
const bizLoading = ref(false)
const bizStreaming = ref(false)
const bizResult = ref('')

async function getBusinessReport() {
  if (!bizForm.start_date || !bizForm.end_date) { showToast('请选择日期范围', 'error'); return }
  bizLoading.value = true
  bizResult.value = ''
  const payload = {
    hotel_id: bizForm.hotel_id ? Number(bizForm.hotel_id) : undefined,
    start_date: bizForm.start_date,
    end_date: bizForm.end_date,
    dimensions: bizForm.dimensions,
    use_reasoning: bizForm.use_reasoning,
  }
  try {
    if (bizForm.streaming) {
      bizStreaming.value = true
      try {
        for await (const event of aiApi.businessReportStream(payload)) {
          if (event.type === 'chunk') bizResult.value += event.content
          if (event.done) break
        }
        if (bizResult.value.trim()) {
          showToast('经营报告流式生成完成', 'success')
        }
      } finally {
        bizStreaming.value = false
      }
    } else {
      const res = await aiApi.businessReport(payload)
      if (res.code === 0 && res.data) {
        bizResult.value = (res.data as { report: string }).report || '暂无内容'
        showToast('经营报告已生成', 'success')
      } else {
        showApiError(res, '报告生成失败')
      }
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    bizLoading.value = false
  }
}

// ──────────────────────── Tab 4: Sentiment Analysis ────────────────────────
const sentimentForm = reactive({ review_id: '' as string | number })
const sentimentLoading = ref(false)
const sentimentResult = ref<{ score: number; label: string; keywords: string[]; tags: string[]; summary: string } | null>(null)

async function getSentiment() {
  if (!sentimentForm.review_id) { showToast('请选择或输入评价 ID', 'error'); return }
  sentimentLoading.value = true
  sentimentResult.value = null
  try {
    const res = await aiApi.reviewSentiment(Number(sentimentForm.review_id))
    if (res.code === 0 && res.data) {
      sentimentResult.value = (res.data as { result: { score: number; label: string; keywords: string[]; tags: string[]; summary: string } }).result
      showToast('情感分析完成', 'success')
    } else {
      showApiError(res, '情感分析失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    sentimentLoading.value = false
  }
}

// ──────────────────────── Tab 5: Marketing Copy ────────────────────────
const marketingForm = reactive({
  hotel_id: '' as string | number,
  copy_type: '',
  style: 'formal',
  keywords_str: '',
  target_audience: '',
  extra_notes: '',
})
const marketingLoading = ref(false)
const marketingResult = ref<{ title: string; content: string; tags: string[] }[]>([])

async function getMarketingCopy() {
  if (!marketingForm.copy_type) { showToast('请选择文案类型', 'error'); return }
  marketingLoading.value = true
  marketingResult.value = []
  try {
    const res = await aiApi.marketingCopy({
      hotel_id: marketingForm.hotel_id ? Number(marketingForm.hotel_id) : undefined,
      copy_type: marketingForm.copy_type,
      style: marketingForm.style,
      keywords: marketingForm.keywords_str ? marketingForm.keywords_str.split(/[,，]/).map((k: string) => k.trim()).filter(Boolean) : [],
      target_audience: marketingForm.target_audience,
      extra_notes: marketingForm.extra_notes,
    })
    if (res.code === 0 && res.data) {
      marketingResult.value = (res.data as { copies: { title: string; content: string; tags: string[] }[] }).copies || []
      if (!marketingResult.value.length) showToast('AI 未生成文案，请稍后重试', 'error')
      else showToast('营销文案已生成', 'success')
    } else {
      showApiError(res, '文案生成失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    marketingLoading.value = false
  }
}

// ──────────────────────── Tab 6: Content Generate ────────────────────────
const contentForm = reactive({ content_type: 'hotel_description', count: 3, context_str: '' })
const contentLoading = ref(false)
const contentResult = ref<{ content: string; highlights: string[] }[]>([])

async function getContent() {
  let contextObj: Record<string, unknown> = {}
  if (contentForm.context_str.trim()) {
    try {
      contextObj = JSON.parse(contentForm.context_str)
    } catch {
      showToast('背景信息 JSON 格式错误，请检查格式', 'error')
      return
    }
  }
  contentLoading.value = true
  contentResult.value = []
  try {
    const res = await aiApi.contentGenerate({
      content_type: contentForm.content_type,
      context: contextObj,
      count: contentForm.count,
    })
    if (res.code === 0 && res.data) {
      contentResult.value = (res.data as { results: { content: string; highlights: string[] }[] }).results || []
      if (!contentResult.value.length) showToast('AI 未生成内容，请稍后重试', 'error')
      else showToast('内容生成完成', 'success')
    } else {
      showApiError(res, '内容生成失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    contentLoading.value = false
  }
}

// ──────────────────────── Tab 7: Anomaly ────────────────────────
const anomalyForm = reactive({ hotel_id: '' as string | number, date: '' })
const anomalyLoading = ref(false)
type AnomalyResult = { anomalies: { type: string; level: string; description: string; value: unknown; threshold: unknown }[]; summary: string }
const anomalyResult = ref<AnomalyResult | null>(null)

async function getAnomalyReport() {
  anomalyLoading.value = true
  anomalyResult.value = null
  try {
    const res = await aiApi.anomalyReport({
      hotel_id: anomalyForm.hotel_id ? Number(anomalyForm.hotel_id) : undefined,
      date: anomalyForm.date || undefined,
    })
    if (res.code === 0 && res.data) {
      anomalyResult.value = res.data as AnomalyResult
      showToast('异常检测完成', 'success')
    } else {
      showApiError(res, '异常检测失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    anomalyLoading.value = false
  }
}

const orderAnomalyForm = reactive({ date: '' })
const orderAnomalyLoading = ref(false)
type OrderAnomalyResult = { anomalies: { type: string; count: number }[]; summary: string }
const orderAnomalyResult = ref<OrderAnomalyResult | null>(null)

async function getOrderAnomalySummary() {
  orderAnomalyLoading.value = true
  orderAnomalyResult.value = null
  try {
    const res = await aiApi.orderAnomalySummary(orderAnomalyForm.date ? { date: orderAnomalyForm.date } : undefined)
    if (res.code === 0 && res.data) {
      orderAnomalyResult.value = res.data as OrderAnomalyResult
      showToast('订单异常统计已生成', 'success')
    } else {
      showApiError(res, '订单异常统计失败')
    }
  } catch {
    showToast('网络请求失败，请检查连接', 'error')
  } finally {
    orderAnomalyLoading.value = false
  }
}

onMounted(() => {
  loadHotels()
  loadRoomTypes()
  loadRecentReviews()
})
</script>

<style scoped>
.input-field {
  @apply w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-400 focus:ring-1 focus:ring-teal-400;
}
.btn-primary {
  @apply rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>

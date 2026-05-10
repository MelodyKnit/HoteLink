<template>
  <section>
    <PageHeader title="支付网关" subtitle="管理模拟支付、微信、支付宝与其它支付平台接入" />

    <div v-if="loading" class="py-20 text-center text-slate-400">加载中…</div>

    <div v-else class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div class="space-y-6">
        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 class="text-base font-semibold text-slate-900">模拟支付开关</h3>
              <p class="mt-1 text-sm text-slate-500">演示环境可保留模拟支付；若要强制走真实支付链路，可在这里关闭。</p>
            </div>
            <label class="relative inline-flex cursor-pointer items-center self-start md:self-auto">
              <input v-model="mockEnabled" type="checkbox" class="peer sr-only" @change="saveMockSetting" />
              <div class="h-6 w-11 rounded-full bg-slate-200 transition after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-teal-600 peer-checked:after:translate-x-full"></div>
            </label>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 class="text-base font-semibold text-slate-900">网关列表</h3>
              <p class="mt-1 text-sm text-slate-500">每个网关都可以单独启停、配置沙箱与支付场景，前端会根据这里的配置展示对应支付入口。</p>
            </div>
            <button class="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700" @click="openCreateModal()">
              + 新增网关
            </button>
          </div>

          <div v-if="gateways.length === 0" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-400">
            暂无支付网关，先添加微信支付、支付宝或其它平台配置。
          </div>

          <div v-else class="space-y-4">
            <article
              v-for="gateway in gateways"
              :key="gateway.name"
              class="rounded-2xl border p-5 transition"
              :class="gateway.enabled ? 'border-slate-200 bg-white' : 'border-slate-200 bg-slate-50/70'"
            >
              <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <h4 class="text-base font-semibold text-slate-900">{{ gateway.label }}</h4>
                    <StatusBadge :label="providerTypeLabel(gateway.provider_type)" type="info" />
                    <StatusBadge v-if="gateway.enabled" label="已启用" type="success" />
                    <StatusBadge v-else label="未启用" type="default" />
                    <StatusBadge v-if="gateway.sandbox" label="沙箱/联调" type="warning" />
                    <StatusBadge v-if="!gateway.is_configured" label="待补齐参数" type="warning" />
                  </div>
                  <p class="mt-1 text-xs text-slate-500">标识：{{ gateway.name }} · 方法：{{ paymentMethodLabel(gateway.payment_method) }} · 优先级：{{ gateway.priority }}</p>

                  <div class="mt-4 grid gap-3 md:grid-cols-2">
                    <div class="rounded-xl bg-slate-50 px-3 py-2.5">
                      <p class="text-xs text-slate-400">支付场景</p>
                      <p class="mt-1 text-sm font-medium text-slate-800">{{ formatScenes(gateway.scenes) }}</p>
                    </div>
                    <div class="rounded-xl bg-slate-50 px-3 py-2.5">
                      <p class="text-xs text-slate-400">回调地址</p>
                      <p class="mt-1 break-all text-sm font-medium text-slate-800">{{ gateway.notify_url || '未配置' }}</p>
                    </div>
                    <div class="rounded-xl bg-slate-50 px-3 py-2.5">
                      <p class="text-xs text-slate-400">网关地址</p>
                      <p class="mt-1 break-all text-sm font-medium text-slate-800">{{ gateway.gateway_url || '未配置' }}</p>
                    </div>
                    <div class="rounded-xl bg-slate-50 px-3 py-2.5">
                      <p class="text-xs text-slate-400">托管收银台</p>
                      <p class="mt-1 break-all text-sm font-medium text-slate-800">{{ gateway.checkout_url || '未配置' }}</p>
                    </div>
                  </div>

                  <div class="mt-4 flex flex-wrap gap-2">
                    <span
                      v-for="tag in configuredSecretLabels(gateway)"
                      :key="tag"
                      class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600"
                    >
                      {{ tag }}已配置
                    </span>
                  </div>

                  <div v-if="gateway.missing_required_labels.length" class="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-800">
                    仍需补齐：{{ gateway.missing_required_labels.join('、') }}
                  </div>
                </div>

                <div class="flex shrink-0 items-center gap-2 lg:pl-4">
                  <button class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-200" @click="openEditModal(gateway)">
                    编辑
                  </button>
                  <button class="rounded-lg bg-red-50 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-100" @click="removeGateway(gateway)">
                    删除
                  </button>
                </div>
              </div>
            </article>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div class="mb-3 flex items-center justify-between gap-3">
            <div>
              <h3 class="text-base font-semibold text-slate-900">快捷模板</h3>
              <p class="mt-1 text-sm text-slate-500">基于官方接入信息预填常用字段，减少首次配置成本。</p>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="template in builtinTemplates"
              :key="template.name"
              class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 transition hover:border-teal-500 hover:bg-teal-50 hover:text-teal-700"
              @click="openCreateModal(template)"
            >
              {{ template.label }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 lg:sticky lg:top-6 lg:self-start">
        <div class="rounded-2xl bg-slate-900 p-6 text-white shadow-sm">
          <p class="text-xs uppercase tracking-wider text-slate-400">联动说明</p>
          <div class="mt-4 space-y-3 text-sm text-slate-200">
            <p>用户端支付页会只展示这里启用且配置完整的支付方式。</p>
            <p>关闭模拟支付后，待支付订单只能走真实网关动作协议。</p>
            <p>微信与支付宝当前会把商户参数、场景和回调信息下发给前端，方便接入真实 SDK 或收银台。</p>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <p class="text-xs uppercase tracking-wider text-slate-400">现状统计</p>
          <div class="mt-4 space-y-3 text-sm text-slate-700">
            <div class="flex items-center justify-between gap-3">
              <span>已启用网关</span>
              <span class="font-semibold">{{ enabledCount }}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span>已配置完成</span>
              <span class="font-semibold">{{ configuredCount }}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span>模拟支付</span>
              <span class="font-semibold">{{ mockEnabled ? '开启' : '关闭' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4 py-6 backdrop-blur-[2px]" @click.self="closeModal">
        <div class="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200">
          <div class="mb-4 flex items-start justify-between gap-4">
            <div>
              <h3 class="text-base font-semibold text-slate-900">{{ editingName ? '编辑支付网关' : '新增支付网关' }}</h3>
              <p class="mt-1 text-sm text-slate-500">真实密钥不会回显；留空表示保留当前已保存的秘密字段。</p>
            </div>
            <button type="button" class="rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-700" @click="closeModal">
              关闭
            </button>
          </div>

          <form class="space-y-5" @submit.prevent="saveGateway">
            <div class="grid gap-4 md:grid-cols-2">
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">网关标识</label>
                <input v-model="form.name" :disabled="!!editingName" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 disabled:bg-slate-100" placeholder="wechat_main" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">显示名称</label>
                <input v-model="form.label" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="微信支付主商户" />
              </div>
            </div>

            <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">支付平台</label>
                <SelectField v-model="form.provider_type" class="w-full">
                  <option value="wechat">微信支付</option>
                  <option value="alipay">支付宝</option>
                  <option value="custom">其它支付平台</option>
                </SelectField>
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">运行状态</label>
                <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
                  <label
                    v-for="option in paymentGatewaySwitchMeta"
                    :key="option.key"
                    class="flex min-h-[68px] cursor-pointer items-center justify-between gap-3 rounded-xl border px-3 py-3 transition"
                    :class="
                      form[option.key]
                        ? option.tone === 'amber'
                          ? 'border-amber-200 bg-amber-50/80'
                          : 'border-teal-200 bg-teal-50/80'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    "
                  >
                    <div class="min-w-0">
                      <p class="text-sm font-medium text-slate-800">{{ option.label }}</p>
                      <p
                        class="mt-1 text-xs leading-5"
                        :class="
                          form[option.key]
                            ? option.tone === 'amber'
                              ? 'text-amber-700'
                              : 'text-teal-700'
                            : 'text-slate-500'
                        "
                      >
                        {{ option.description }}
                      </p>
                    </div>
                    <span class="relative inline-flex h-6 w-11 shrink-0 items-center">
                      <input v-model="form[option.key]" type="checkbox" class="peer sr-only" />
                      <span
                        class="absolute inset-0 rounded-full transition-colors"
                        :class="form[option.key] ? (option.tone === 'amber' ? 'bg-amber-500' : 'bg-teal-600') : 'bg-slate-200'"
                      ></span>
                      <span class="absolute left-[2px] top-[2px] h-5 w-5 rounded-full bg-white shadow-sm transition-transform" :class="form[option.key] ? 'translate-x-5' : ''"></span>
                    </span>
                  </label>
                </div>
              </div>
            </div>

            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700">支付场景</label>
              <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                <label
                  v-for="scene in currentSceneOptions"
                  :key="scene"
                  class="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
                >
                  <input v-model="form.scenes" type="checkbox" :value="scene" class="accent-teal-600" />
                  {{ sceneLabel(scene) }}
                </label>
              </div>
            </div>

            <div class="grid gap-4 md:grid-cols-3">
              <div class="md:col-span-2">
                <label class="mb-1 block text-sm font-medium text-slate-700">网关地址</label>
                <input v-model="form.gateway_url" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="https://..." />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">优先级</label>
                <input v-model.number="form.priority" type="number" min="0" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
              </div>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">异步回调地址</label>
                <input v-model="form.notify_url" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="https://domain/api/v1/..." />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">回调签名密钥</label>
                <input v-model="form.notify_secret" type="password" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('notify_secret')" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">同步返回地址</label>
                <input v-model="form.return_url" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="https://domain/payment/result" />
              </div>
            </div>

            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700">托管收银台地址（可选）</label>
              <input v-model="form.checkout_url" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="如果有托管收银台，可填写实际跳转地址" />
            </div>

            <div class="rounded-2xl bg-slate-50/80 p-5">
              <h4 class="text-sm font-semibold text-slate-800">基础接入信息</h4>
              <div class="mt-4 grid gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">App ID / 应用 ID</label>
                  <input v-model="form.app_id" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">{{ form.provider_type === 'wechat' ? '商户号' : '商户名称 / 备注' }}</label>
                  <input v-model="form.merchant_id" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
                <div v-if="form.provider_type === 'wechat'">
                  <label class="mb-1 block text-sm font-medium text-slate-700">商户名称</label>
                  <input v-model="form.merchant_name" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
                <div v-if="form.provider_type === 'wechat'">
                  <label class="mb-1 block text-sm font-medium text-slate-700">商户证书序列号</label>
                  <input v-model="form.merchant_cert_serial_no" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" />
                </div>
                <div v-if="form.provider_type === 'alipay'">
                  <label class="mb-1 block text-sm font-medium text-slate-700">签名算法</label>
                  <input v-model="form.sign_type" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="RSA2" />
                </div>
                <div v-if="form.provider_type === 'alipay'">
                  <label class="mb-1 block text-sm font-medium text-slate-700">字符集</label>
                  <input v-model="form.charset" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="utf-8" />
                </div>
              </div>
            </div>

            <div v-if="form.provider_type === 'wechat'" class="rounded-2xl bg-slate-50/80 p-5">
              <h4 class="text-sm font-semibold text-slate-800">微信支付密钥与证书</h4>
              <div class="mt-4 grid gap-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">API v3 Key</label>
                  <input v-model="form.api_v3_key" type="password" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('api_v3_key')" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">商户私钥</label>
                  <textarea v-model="form.merchant_private_key" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('merchant_private_key')"></textarea>
                </div>
                <div class="grid gap-4 md:grid-cols-2">
                  <div>
                    <label class="mb-1 block text-sm font-medium text-slate-700">商户证书</label>
                    <textarea v-model="form.merchant_certificate" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('merchant_certificate')"></textarea>
                  </div>
                  <div>
                    <label class="mb-1 block text-sm font-medium text-slate-700">微信支付平台证书</label>
                    <textarea v-model="form.platform_certificate" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('platform_certificate')"></textarea>
                  </div>
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">微信支付平台公钥（可选）</label>
                  <textarea v-model="form.platform_public_key" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('platform_public_key')"></textarea>
                </div>
              </div>
            </div>

            <div v-else-if="form.provider_type === 'alipay'" class="rounded-2xl bg-slate-50/80 p-5">
              <h4 class="text-sm font-semibold text-slate-800">支付宝密钥配置</h4>
              <div class="mt-4 grid gap-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">应用私钥</label>
                  <textarea v-model="form.app_private_key" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('app_private_key')"></textarea>
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">支付宝公钥</label>
                  <textarea v-model="form.alipay_public_key" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" :placeholder="secretPlaceholder('alipay_public_key')"></textarea>
                </div>
              </div>
            </div>

            <div class="rounded-2xl bg-slate-50/80 p-5">
              <h4 class="text-sm font-semibold text-slate-800">扩展参数与说明</h4>
              <div class="mt-4 grid gap-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">网关说明</label>
                  <textarea v-model="form.description" rows="3" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500" placeholder="例如：直营微信公众号支付、财务联调专用等。"></textarea>
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">extra JSON（可选）</label>
                  <textarea v-model="extraJson" rows="5" class="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs outline-none focus:border-teal-500" placeholder='{"sub_appid":"..."}'></textarea>
                </div>
              </div>
            </div>

            <div class="flex justify-end gap-3">
              <button type="button" class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50" @click="closeModal">取消</button>
              <button type="submit" class="rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white hover:bg-teal-700" :disabled="saving">
                {{ saving ? '保存中…' : '保存网关' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { paymentGatewayApi, type BuiltinPaymentTemplate, type PaymentGatewayItem, type PaymentGatewayProviderType } from '@hotelink/api'
import { extractApiError, PAYMENT_GATEWAY_SWITCH_META, PAYMENT_METHOD_MAP, suggestUniquePaymentGatewayName } from '@hotelink/utils'
import { PageHeader, SelectField, StatusBadge, useConfirm, useToast } from '@hotelink/ui'

const { showToast } = useToast()
const { confirm: confirmDialog } = useConfirm()

const loading = ref(true)
const saving = ref(false)
const showModal = ref(false)
const editingName = ref('')
const mockEnabled = ref(true)
const gateways = ref<PaymentGatewayItem[]>([])
const builtinTemplates = ref<BuiltinPaymentTemplate[]>([])
const fieldLabels = ref<Record<string, string>>({})
const sceneLabels = ref<Record<string, string>>({})
const extraJson = ref('')

const form = reactive({
  name: '',
  label: '',
  provider_type: 'wechat' as PaymentGatewayProviderType,
  enabled: true,
  sandbox: false,
  priority: 100,
  description: '',
  scenes: [] as string[],
  gateway_url: '',
  checkout_url: '',
  notify_url: '',
  notify_secret: '',
  return_url: '',
  app_id: '',
  merchant_id: '',
  merchant_name: '',
  merchant_cert_serial_no: '',
  api_v3_key: '',
  merchant_private_key: '',
  merchant_certificate: '',
  platform_certificate: '',
  platform_public_key: '',
  app_private_key: '',
  alipay_public_key: '',
  sign_type: '',
  charset: '',
})

const currentTemplate = computed(() => builtinTemplates.value.find(item => item.provider_type === form.provider_type))
const currentSceneOptions = computed(() => currentTemplate.value?.supported_scenes || [])
const enabledCount = computed(() => gateways.value.filter(item => item.enabled).length)
const configuredCount = computed(() => gateways.value.filter(item => item.is_configured).length)
const paymentGatewaySwitchMeta = PAYMENT_GATEWAY_SWITCH_META

watch(() => form.provider_type, (providerType) => {
  const template = builtinTemplates.value.find(item => item.provider_type === providerType)
  if (!template) return
  form.scenes = form.scenes.filter(scene => template.supported_scenes.includes(scene))
  if (!form.scenes.length) {
    form.scenes = template.supported_scenes.slice(0, 1)
  }
  const defaults = template.default_values || {}
  if (!form.gateway_url && typeof defaults.gateway_url === 'string') {
    form.gateway_url = defaults.gateway_url
  }
  if (providerType === 'alipay') {
    if (!form.sign_type && typeof defaults.sign_type === 'string') form.sign_type = defaults.sign_type
    if (!form.charset && typeof defaults.charset === 'string') form.charset = defaults.charset
  }
})

function providerTypeLabel(type: string): string {
  if (type === 'wechat') return '微信支付'
  if (type === 'alipay') return '支付宝'
  return '其它平台'
}

function paymentMethodLabel(value: string): string {
  return PAYMENT_METHOD_MAP[value] || value
}

function sceneLabel(scene: string): string {
  return sceneLabels.value[scene] || scene
}

function formatScenes(scenes: string[]): string {
  return scenes.map(sceneLabel).join('、') || '未配置'
}

function configuredSecretLabels(gateway: PaymentGatewayItem): string[] {
  return Object.entries(gateway.secret_flags || {})
    .filter(([, configured]) => configured)
    .map(([field]) => fieldLabels.value[field] || field)
}

function secretPlaceholder(field: string): string {
  return gatewaySecretConfigured(field) ? `已保存${fieldLabels.value[field] || field}，留空则保持不变` : `请输入${fieldLabels.value[field] || field}`
}

function gatewaySecretConfigured(field: string): boolean {
  const target = gateways.value.find(item => item.name === editingName.value)
  return !!target?.secret_flags?.[field]
}

function resetForm() {
  editingName.value = ''
  Object.assign(form, {
    name: '',
    label: '',
    provider_type: 'wechat' as PaymentGatewayProviderType,
    enabled: true,
    sandbox: false,
    priority: 100,
    description: '',
    scenes: ['jsapi'],
    gateway_url: '',
    checkout_url: '',
    notify_url: '',
    notify_secret: '',
    return_url: '',
    app_id: '',
    merchant_id: '',
    merchant_name: '',
    merchant_cert_serial_no: '',
    api_v3_key: '',
    merchant_private_key: '',
    merchant_certificate: '',
    platform_certificate: '',
    platform_public_key: '',
    app_private_key: '',
    alipay_public_key: '',
    sign_type: '',
    charset: '',
  })
  extraJson.value = ''
}

function openCreateModal(template?: BuiltinPaymentTemplate) {
  resetForm()
  if (template) {
    form.provider_type = template.provider_type
    form.label = template.label
    form.name = suggestGatewayName(template.name)
    form.description = template.description
    form.scenes = template.supported_scenes.slice(0, 1)
    const defaults = template.default_values || {}
    form.gateway_url = typeof defaults.gateway_url === 'string' ? defaults.gateway_url : ''
    form.sign_type = typeof defaults.sign_type === 'string' ? defaults.sign_type : ''
    form.charset = typeof defaults.charset === 'string' ? defaults.charset : ''
  }
  showModal.value = true
}

function openEditModal(gateway: PaymentGatewayItem) {
  resetForm()
  editingName.value = gateway.name
  Object.assign(form, {
    name: gateway.name,
    label: gateway.label,
    provider_type: gateway.provider_type,
    enabled: gateway.enabled,
    sandbox: gateway.sandbox,
    priority: gateway.priority,
    description: gateway.description,
    scenes: [...gateway.scenes],
    gateway_url: gateway.gateway_url,
    checkout_url: gateway.checkout_url,
    notify_url: gateway.notify_url,
    notify_secret: '',
    return_url: gateway.return_url,
    app_id: gateway.app_id,
    merchant_id: gateway.merchant_id,
    merchant_name: gateway.merchant_name,
    merchant_cert_serial_no: gateway.merchant_cert_serial_no,
    sign_type: gateway.sign_type,
    charset: gateway.charset,
  })
  extraJson.value = gateway.extra && Object.keys(gateway.extra).length ? JSON.stringify(gateway.extra, null, 2) : ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function suggestGatewayName(base: string): string {
  return suggestUniquePaymentGatewayName(base, gateways.value.map(item => item.name))
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await paymentGatewayApi.get()
    if (res.code === 0 && res.data) {
      mockEnabled.value = res.data.mock_enabled
      gateways.value = res.data.gateways
      builtinTemplates.value = res.data.builtin_templates
      fieldLabels.value = res.data.field_labels
      sceneLabels.value = res.data.scene_labels
    } else {
      showToast(res.message || '加载支付网关失败', 'error')
    }
  } catch {
    showToast('支付网关加载失败，请检查网络', 'error')
  } finally {
    loading.value = false
  }
}

async function saveMockSetting() {
  try {
    const res = await paymentGatewayApi.update({ mock_enabled: mockEnabled.value })
    if (res.code === 0) {
      showToast(mockEnabled.value ? '模拟支付已开启' : '模拟支付已关闭', 'success')
      return
    }
    mockEnabled.value = !mockEnabled.value
    showToast(res.message || '保存失败', 'error')
  } catch {
    mockEnabled.value = !mockEnabled.value
    showToast('保存失败，请重试', 'error')
  }
}

async function saveGateway() {
  const extra = extraJson.value.trim()
  let extraPayload: Record<string, unknown> = {}
  if (extra) {
    try {
      extraPayload = JSON.parse(extra) as Record<string, unknown>
    } catch {
      showToast('extra JSON 格式不正确', 'warning')
      return
    }
  }

  const payload: Record<string, unknown> = {
    name: form.name,
    label: form.label,
    provider_type: form.provider_type,
    enabled: form.enabled,
    sandbox: form.sandbox,
    priority: form.priority,
    description: form.description,
    scenes: form.scenes,
    gateway_url: form.gateway_url,
    checkout_url: form.checkout_url,
    notify_url: form.notify_url,
    notify_secret: form.notify_secret,
    return_url: form.return_url,
    app_id: form.app_id,
    merchant_id: form.merchant_id,
    merchant_name: form.merchant_name,
    merchant_cert_serial_no: form.merchant_cert_serial_no,
    sign_type: form.sign_type,
    charset: form.charset,
    extra: extraPayload,
  }

  if (form.provider_type === 'wechat') {
    Object.assign(payload, {
      api_v3_key: form.api_v3_key,
      merchant_private_key: form.merchant_private_key,
      merchant_certificate: form.merchant_certificate,
      platform_certificate: form.platform_certificate,
      platform_public_key: form.platform_public_key,
    })
  } else if (form.provider_type === 'alipay') {
    Object.assign(payload, {
      app_private_key: form.app_private_key,
      alipay_public_key: form.alipay_public_key,
    })
  }

  saving.value = true
  try {
    const res = await paymentGatewayApi.saveProvider(payload)
    if (res.code === 0) {
      closeModal()
      await loadSettings()
      showToast('支付网关已保存', 'success')
    } else {
      showToast(extractApiError(res, '保存失败，请检查填写内容'), 'error')
    }
  } catch {
    showToast('保存失败，请检查网络后重试', 'error')
  } finally {
    saving.value = false
  }
}

async function removeGateway(gateway: PaymentGatewayItem) {
  if (!await confirmDialog(`确认删除支付网关「${gateway.label}」？`, { type: 'danger', title: '删除支付网关' })) return
  try {
    const res = await paymentGatewayApi.deleteProvider(gateway.name)
    if (res.code === 0) {
      await loadSettings()
      showToast('支付网关已删除', 'success')
    } else {
      showToast(res.message || '删除失败', 'error')
    }
  } catch {
    showToast('删除失败，请检查网络后重试', 'error')
  }
}

onMounted(loadSettings)
</script>

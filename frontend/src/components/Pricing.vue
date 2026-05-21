<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { Check, X, Crown, Loader2 } from 'lucide-vue-next'
import { createCheckoutSession } from '../api/billing'

const props = defineProps<{
  isLoggedIn: boolean
  isVip?: boolean
  vipUntil?: number | null
}>()

const vipExpiryText = computed(() => {
  const t = props.vipUntil
  if (!props.isVip || t == null) return ''
  return new Date(t * 1000).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

const emit = defineEmits<{
  openAuth: []
}>()

const plans = [
  {
    name: '免费版',
    price: '¥0',
    period: '永久免费',
    desc: '下载不限；AI 总结有每日次数',
    features: [
      { text: '视频解析与下载（不限）', included: true },
      { text: '1700+ 平台支持', included: true },
      { text: '登录后每日 1 次 AI 总结', included: true },
      { text: 'AI 问答（计入总结次数）', included: true },
      { text: '¥9.9 VIP（30 天不限 AI）', included: false },
      { text: 'Stripe 安全支付', included: false },
      { text: '批量下载（规划中）', included: false },
      { text: '字幕翻译（规划中）', included: false },
    ],
    cta: '免费使用',
    highlighted: false,
  },
  {
    name: 'VIP 会员',
    price: '¥9.9',
    period: '/30 天',
    desc: '单次购买 30 天权益，到期手动续费',
    features: [
      { text: 'AI 视频总结不限次数', included: true },
      { text: 'AI 问答不限次数', included: true },
      { text: '下载与解析保持不限', included: true },
      { text: 'Stripe Checkout 安全收款', included: true },
      { text: '邮箱登录后即可开通', included: true },
      { text: '到期前不会自动扣款', included: true },
      { text: '同一时段防止重复下单（幂等）', included: true },
      { text: '专属客服（规划中）', included: false },
    ],
    cta: '立即开通',
    highlighted: true,
  },
]

const checkoutLoading = ref(false)
const checkoutError = ref('')

async function onVipCheckout() {
  checkoutError.value = ''
  if (!props.isLoggedIn) {
    emit('openAuth')
    return
  }
  if (props.isVip) {
    return
  }
  checkoutLoading.value = true
  try {
    const url = await createCheckoutSession()
    window.location.href = url
  } catch (e) {
    if (axios.isAxiosError(e)) {
      const d = e.response?.data as { detail?: string | unknown } | undefined
      const detail = d?.detail
      checkoutError.value =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((x: { msg?: string }) => x.msg).filter(Boolean).join('; ')
            : '发起支付失败，请确认后端已配置 Stripe 环境变量'
    } else {
      checkoutError.value = '网络异常，请稍后重试'
    }
  } finally {
    checkoutLoading.value = false
  }
}
</script>

<template>
  <section id="pricing" class="py-20 bg-bg">
    <div class="max-w-5xl mx-auto px-4">
      <div class="text-center mb-14">
        <h2 class="text-3xl sm:text-4xl font-extrabold text-text mb-4">
          选择适合你的 <span class="text-primary">方案</span>
        </h2>
        <p class="text-text-secondary text-lg max-w-xl mx-auto">
          下载不限；AI 总结需登录 — 免费每日 1 次，¥9.9 单次购买 30 天 VIP（Stripe，到期手动续费）
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div
          v-for="plan in plans"
          :key="plan.name"
          :class="[
            'relative p-8 rounded-2xl border-2 transition-all',
            plan.highlighted
              ? 'border-gold bg-white shadow-xl shadow-gold/10 scale-105'
              : 'border-gray-200 bg-white',
          ]"
        >
          <div
            v-if="plan.highlighted"
            class="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-gold to-gold-dark text-white text-xs font-bold rounded-full flex items-center gap-1"
          >
            <Crown class="w-3.5 h-3.5" />
            推荐
          </div>

          <h3 class="text-xl font-bold text-text mb-1">{{ plan.name }}</h3>
          <p class="text-text-muted text-sm mb-4">{{ plan.desc }}</p>

          <div class="mb-6">
            <span class="text-4xl font-black" :class="plan.highlighted ? 'text-gold' : 'text-text'">
              {{ plan.price }}
            </span>
            <span class="text-text-secondary text-sm">{{ plan.period }}</span>
          </div>

          <ul class="space-y-3 mb-8">
            <li
              v-for="feature in plan.features"
              :key="feature.text"
              class="flex items-center gap-2.5 text-sm"
            >
              <Check
                v-if="feature.included"
                class="w-4 h-4 flex-shrink-0"
                :class="plan.highlighted ? 'text-gold' : 'text-primary'"
              />
              <X v-else class="w-4 h-4 text-gray-300 flex-shrink-0" />
              <span :class="feature.included ? 'text-text' : 'text-gray-400'">
                {{ feature.text }}
              </span>
            </li>
          </ul>

          <p v-if="checkoutError && plan.highlighted" class="text-red-600 text-sm mb-3 text-center">
            {{ checkoutError }}
          </p>

          <button
            type="button"
            :disabled="plan.highlighted ? checkoutLoading || isVip : false"
            @click="plan.highlighted ? onVipCheckout() : undefined"
            :class="[
              'w-full py-3 font-semibold rounded-xl transition-all text-sm cursor-pointer active:scale-[0.99]',
              plan.highlighted
                ? isVip
                  ? 'bg-gray-100 text-text-secondary cursor-default border border-gray-200'
                  : 'bg-gradient-to-r from-gold to-gold-dark text-white hover:shadow-lg hover:shadow-gold/30 disabled:opacity-60 disabled:cursor-not-allowed'
                : 'bg-gray-100 text-text-secondary hover:bg-gray-200 hover:shadow-sm cursor-default',
            ]"
          >
            <span v-if="plan.highlighted && isVip" class="block text-center leading-snug">
              <span class="text-gold-dark font-bold">当前已是 VIP</span>
              <span v-if="vipExpiryText" class="block text-xs font-normal text-text-muted mt-1">
                有效期至 {{ vipExpiryText }} · 到期后再来此续费
              </span>
            </span>
            <span v-else-if="plan.highlighted && checkoutLoading" class="inline-flex items-center justify-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" />
              跳转 Stripe 中...
            </span>
            <span v-else>{{ plan.cta }}</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

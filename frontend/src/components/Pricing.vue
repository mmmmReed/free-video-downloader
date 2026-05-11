<script setup lang="ts">
import { Check, X, Crown } from 'lucide-vue-next'

const plans = [
  {
    name: '免费版',
    price: '¥0',
    period: '永久免费',
    desc: '满足基本下载需求',
    features: [
      { text: '每日 5 次下载', included: true },
      { text: '最高 720P 画质', included: true },
      { text: '标准下载速度', included: true },
      { text: '1700+ 平台支持', included: true },
      { text: '4K / 1080P 画质', included: false },
      { text: '无限次下载', included: false },
      { text: '批量下载', included: false },
      { text: '视频总结 / 字幕翻译', included: false },
    ],
    cta: '免费使用',
    highlighted: false,
  },
  {
    name: 'VIP 会员',
    price: '¥29',
    period: '/月',
    desc: '无限制，极速体验',
    features: [
      { text: '无限次下载', included: true },
      { text: '4K / 1080P 高清', included: true },
      { text: '极速下载通道', included: true },
      { text: '1700+ 平台支持', included: true },
      { text: '批量下载', included: true },
      { text: 'AI 视频总结', included: true },
      { text: '字幕提取 + 翻译', included: true },
      { text: '专属客服支持', included: true },
    ],
    cta: '立即开通',
    highlighted: true,
  },
]
</script>

<template>
  <section id="pricing" class="py-20 bg-bg">
    <div class="max-w-5xl mx-auto px-4">
      <div class="text-center mb-14">
        <h2 class="text-3xl sm:text-4xl font-extrabold text-text mb-4">
          选择适合你的 <span class="text-primary">方案</span>
        </h2>
        <p class="text-text-secondary text-lg max-w-xl mx-auto">
          免费版满足日常需求，VIP 解锁全部高级功能
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

          <button
            :class="[
              'w-full py-3 font-semibold rounded-xl transition-all text-sm',
              plan.highlighted
                ? 'bg-gradient-to-r from-gold to-gold-dark text-white hover:shadow-lg hover:shadow-gold/30'
                : 'bg-gray-100 text-text-secondary hover:bg-gray-200',
            ]"
          >
            {{ plan.cta }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Globe, Zap, MonitorSmartphone, ShieldCheck } from 'lucide-vue-next'

const features = [
  {
    icon: Globe,
    title: '1700+ 平台支持',
    desc: '覆盖 YouTube、B站、TikTok、Instagram、Twitter 等主流平台，一站式解决所有下载需求',
  },
  {
    icon: Zap,
    title: '极速解析下载',
    desc: '高性能后端引擎，秒级解析视频信息，多线程下载，速度拉满',
  },
  {
    icon: MonitorSmartphone,
    title: '全设备通用',
    desc: '响应式设计完美适配手机、平板、电脑，随时随地在线下载',
  },
  {
    icon: ShieldCheck,
    title: '高清无水印',
    desc: '支持 4K/1080P 高清画质，保留原始质量，无额外水印',
  },
]
</script>

<template>
  <section id="features" class="py-20 bg-white">
    <div class="max-w-7xl mx-auto px-4">
      <div class="text-center mb-14">
        <h2 class="text-3xl sm:text-4xl font-extrabold text-text mb-4">
          为什么选择 <span class="text-primary">FreeVideo</span>
        </h2>
        <p class="text-text-secondary text-lg max-w-xl mx-auto">
          简单、快速、强大，让视频下载变得前所未有的简单
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          v-for="(feature, idx) in features"
          :key="idx"
          class="group p-6 bg-bg rounded-2xl border border-gray-100 hover:shadow-lg hover:shadow-blue-50 hover:-translate-y-1 transition-all duration-300"
        >
          <div class="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-colors">
            <component :is="feature.icon" class="w-6 h-6 text-primary group-hover:text-white transition-colors" />
          </div>
          <h3 class="text-lg font-bold text-text mb-2">{{ feature.title }}</h3>
          <p class="text-sm text-text-secondary leading-relaxed">{{ feature.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

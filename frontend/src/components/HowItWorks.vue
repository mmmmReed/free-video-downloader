<script setup lang="ts">
import {
  ClipboardPaste,
  ListChecks,
  Download,
  Sparkles,
  Network,
} from 'lucide-vue-next'

const steps = [
  {
    icon: ClipboardPaste,
    step: '01',
    title: '粘贴链接',
    desc: '复制视频页面的 URL 链接，粘贴到上方输入框中',
  },
  {
    icon: ListChecks,
    step: '02',
    title: '选择格式',
    desc: '系统自动解析视频信息，选择你需要的清晰度和格式',
  },
  {
    icon: Download,
    step: '03',
    title: '一键下载',
    desc: '点击下载按钮，等待下载完成后保存到本地',
  },
  {
    icon: Sparkles,
    step: '04',
    title: 'AI 总结分析',
    desc: '可勾选「解析后自动总结」，一键生成总结摘要；支持查看字幕文本、与 AI 问答',
  },
  {
    icon: Network,
    step: '05',
    title: '思维导图与导出',
    desc: '根据总结生成思维导图，在导图页可导出 SVG 或高清 PNG，保存到本地随时查看',
  },
]
</script>

<template>
  <section id="how-it-works" class="py-20 bg-white">
    <div class="max-w-7xl mx-auto px-4">
      <div class="text-center mb-14">
        <h2 class="text-3xl sm:text-4xl font-extrabold text-text mb-4">
          只需 <span class="text-primary">五步</span>，下载与 AI 分析一次完成
        </h2>
        <p class="text-text-secondary text-lg max-w-2xl mx-auto leading-relaxed">
          无需安装任何软件，打开浏览器即可完成高清下载、智能总结、思维导图导出
        </p>
      </div>

      <div
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 lg:gap-5"
      >
        <div
          v-for="(item, idx) in steps"
          :key="idx"
          class="relative text-center p-7 sm:p-8 bg-bg rounded-2xl border border-gray-100 min-h-0"
        >
          <div class="text-5xl font-black text-primary/10 absolute top-4 right-5 sm:right-6">
            {{ item.step }}
          </div>
          <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <component
              :is="item.icon"
              class="w-8 h-8"
              :class="item.step === '05' ? 'text-pink-500' : 'text-primary'"
            />
          </div>
          <h3 class="text-lg sm:text-xl font-bold text-text mb-2">{{ item.title }}</h3>
          <p class="text-sm text-text-secondary leading-relaxed">{{ item.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

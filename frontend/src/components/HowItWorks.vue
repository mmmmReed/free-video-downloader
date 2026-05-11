<script setup lang="ts">
import { ClipboardPaste, ListChecks, Download } from 'lucide-vue-next'

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
]
</script>

<template>
  <section id="how-it-works" class="py-20 bg-white">
    <div class="max-w-5xl mx-auto px-4">
      <div class="text-center mb-14">
        <h2 class="text-3xl sm:text-4xl font-extrabold text-text mb-4">
          只需 <span class="text-primary">三步</span>，轻松下载
        </h2>
        <p class="text-text-secondary text-lg max-w-xl mx-auto">
          无需安装任何软件，打开浏览器即可使用
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div
          v-for="(item, idx) in steps"
          :key="idx"
          class="relative text-center p-8 bg-bg rounded-2xl border border-gray-100"
        >
          <div class="text-5xl font-black text-primary/10 absolute top-4 right-6">{{ item.step }}</div>
          <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <component :is="item.icon" class="w-8 h-8 text-primary" />
          </div>
          <h3 class="text-xl font-bold text-text mb-2">{{ item.title }}</h3>
          <p class="text-sm text-text-secondary leading-relaxed">{{ item.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

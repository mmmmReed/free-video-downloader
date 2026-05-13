<script setup lang="ts">
import { Download } from 'lucide-vue-next'
</script>

<template>
  <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center">
            <Download class="w-5 h-5 text-white" />
          </div>
          <span class="text-xl font-bold text-text">
            <span class="text-primary">Free</span>Video
          </span>
        </div>

        <nav class="hidden md:flex items-center gap-8">
          <a href="#features" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">功能</a>
          <a href="#platforms" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">支持平台</a>
          <a href="#how-it-works" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">使用方法</a>
          <a href="#pricing" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">定价</a>
        </nav>

        <button class="px-5 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-dark hover:shadow-md active:scale-[0.98] transition-all shadow-sm cursor-pointer">
          登录 / 注册
        </button>
      </div>
    </div>
  </header>
</template>

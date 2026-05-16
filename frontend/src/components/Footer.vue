<script setup lang="ts">
import { Download } from 'lucide-vue-next'
</script>

<template>
  <footer class="bg-white border-t border-gray-100 py-10">
    <div class="max-w-7xl mx-auto px-4">
      <div class="flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-gradient-to-br from-primary to-primary-dark rounded-lg flex items-center justify-center">
            <Download class="w-4 h-4 text-white" />
          </div>
          <span class="text-lg font-bold text-text">
            <span class="text-primary">free</span>Video
          </span>
        </div>

        <div class="text-center text-sm text-text-muted space-y-1">
          <p>本工具仅供学习研究使用，请尊重内容创作者版权</p>
          <p>用户需自行遵守相关平台服务条款，与本站无关</p>
        </div>

        <div class="text-sm text-text-muted">
          &copy; {{ new Date().getFullYear() }} freeVideo
        </div>
      </div>
    </div>
  </footer>
</template>

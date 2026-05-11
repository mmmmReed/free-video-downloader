<script setup lang="ts">
const platforms = [
  { name: 'YouTube', color: '#FF0000' },
  { name: 'Bilibili', color: '#00A1D6' },
  { name: 'TikTok', color: '#000000' },
  { name: 'Instagram', color: '#E4405F' },
  { name: 'Twitter / X', color: '#1DA1F2' },
  { name: 'Facebook', color: '#1877F2' },
  { name: 'Vimeo', color: '#1AB7EA' },
  { name: 'Dailymotion', color: '#0066DC' },
  { name: 'Reddit', color: '#FF4500' },
  { name: 'Twitch', color: '#9146FF' },
]
</script>

<template>
  <section id="platforms" class="py-20 bg-bg">
    <div class="max-w-7xl mx-auto px-4">
      <div class="text-center mb-14">
        <h2 class="text-3xl sm:text-4xl font-extrabold text-text mb-4">
          支持 <span class="text-primary">1700+</span> 平台
        </h2>
        <p class="text-text-secondary text-lg max-w-xl mx-auto">
          几乎覆盖所有主流视频平台，更多平台持续更新中
        </p>
      </div>

      <div class="flex flex-wrap justify-center gap-4 max-w-3xl mx-auto">
        <div
          v-for="platform in platforms"
          :key="platform.name"
          class="flex items-center gap-2.5 px-5 py-3 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
        >
          <div
            class="w-3 h-3 rounded-full flex-shrink-0"
            :style="{ backgroundColor: platform.color }"
          />
          <span class="text-sm font-medium text-text">{{ platform.name }}</span>
        </div>
      </div>

      <p class="text-center mt-8 text-sm text-text-muted">
        以及 Soundcloud、Pornhub、Niconico、Weibo 等 1700+ 平台...
      </p>
    </div>
  </section>
</template>

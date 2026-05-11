<script setup lang="ts">
import { ref } from 'vue'
import { useVideoDownload } from '../composables/useVideoDownload'
import Header from '../components/Header.vue'
import HeroSection from '../components/HeroSection.vue'
import VideoResult from '../components/VideoResult.vue'
import Features from '../components/Features.vue'
import Platforms from '../components/Platforms.vue'
import HowItWorks from '../components/HowItWorks.vue'
import Pricing from '../components/Pricing.vue'
import Footer from '../components/Footer.vue'

const {
  videoInfo,
  loading,
  error,
  progress,
  selectedFormat,
  isDownloading,
  isFinished,
  parse,
  download,
  downloadFile,
  reset,
} = useVideoDownload()

const currentUrl = ref('')

function handleParse(url: string) {
  currentUrl.value = url
  parse(url)
}

function handleDownload() {
  download(currentUrl.value)
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <Header />
    <main>
      <HeroSection :loading="loading" @parse="handleParse" />

      <!-- Parse error shown when videoInfo is not yet available -->
      <div v-if="error && !videoInfo" class="max-w-2xl mx-auto px-4 -mt-4 mb-8 relative z-10">
        <div class="flex items-center gap-3 text-red-600 bg-red-50 border border-red-100 px-5 py-4 rounded-2xl text-sm shadow-sm">
          <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{{ error }}</span>
        </div>
      </div>

      <VideoResult
        v-if="videoInfo"
        :video-info="videoInfo"
        :selected-format="selectedFormat"
        :progress="progress"
        :is-downloading="isDownloading"
        :is-finished="isFinished"
        :error="error"
        @update:selected-format="(f) => (selectedFormat = f)"
        @download="handleDownload"
        @download-file="downloadFile"
        @reset="reset"
      />

      <Features />
      <Platforms />
      <HowItWorks />
      <Pricing />
    </main>
    <Footer />
  </div>
</template>

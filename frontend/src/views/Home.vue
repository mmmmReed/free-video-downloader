<script setup lang="ts">
import { ref, watch } from 'vue'
import { useVideoDownload } from '../composables/useVideoDownload'
import { useVideoSummary } from '../composables/useVideoSummary'
import Header from '../components/Header.vue'
import HeroSection from '../components/HeroSection.vue'
import VideoResult from '../components/VideoResult.vue'
import SummaryPanel from '../components/SummaryPanel.vue'
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

const {
  subtitleData,
  subtitleLoading,
  subtitleError,
  summaryContent,
  summaryLoading,
  summaryError,
  summaryDone,
  chatMessages,
  chatLoading,
  chatError,
  activeTab,
  hasSubtitle,
  loadSubtitle,
  startSummarize,
  sendChatMessage,
  resetSummary,
} = useVideoSummary()

const currentUrl = ref('')
/** 解析成功后是否自动拉字幕并总结（默认勾选，可取消本次） */
const autoSummarizeAfterParse = ref(true)
/** 无有效字幕时提示总结质量可能下降 */
const subtitleQualityHint = ref(false)

function handleParse(url: string) {
  currentUrl.value = url
  subtitleQualityHint.value = false
  resetSummary()
  parse(url)
}

async function runSummarizePipeline() {
  const url = currentUrl.value
  if (!url || !videoInfo.value) return

  await loadSubtitle(url)
  if (currentUrl.value !== url || !videoInfo.value) return

  const text = subtitleData.value?.full_text?.trim() ?? ''
  subtitleQualityHint.value =
    !!subtitleError.value || !hasSubtitle.value || !text

  startSummarize(url, videoInfo.value.title || '')
}

watch(
  videoInfo,
  async (vi) => {
    if (!vi) return
    if (!autoSummarizeAfterParse.value) return
    await runSummarizePipeline()
  },
  { flush: 'post' }
)

function handleDownload() {
  download(currentUrl.value)
}

async function handleSummarize() {
  await runSummarizePipeline()
}

function handleChatSend(question: string) {
  sendChatMessage(
    subtitleData.value?.full_text || '',
    videoInfo.value?.title || '',
    question
  )
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <Header />
    <main>
      <HeroSection
        v-model:auto-summarize-after-parse="autoSummarizeAfterParse"
        :loading="loading"
        @parse="handleParse"
      />

      <!-- Parse error shown when videoInfo is not yet available -->
      <div v-if="error && !videoInfo" class="max-w-2xl mx-auto px-4 -mt-4 mb-8 relative z-10">
        <div class="flex items-center gap-3 text-red-600 bg-red-50 border border-red-100 px-5 py-4 rounded-2xl text-sm shadow-sm">
          <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{{ error }}</span>
        </div>
      </div>

      <section
        v-if="videoInfo"
        class="max-w-7xl mx-auto px-4 mt-0 sm:mt-0.5 mb-14 relative z-10"
      >
        <div
          class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.08fr)] gap-5 lg:gap-6 items-stretch lg:min-h-[min(480px,72vh)]"
        >
          <VideoResult
            split
            :video-info="videoInfo"
            :selected-format="selectedFormat"
            :progress="progress"
            :is-downloading="isDownloading"
            :is-finished="isFinished"
            :error="error"
            :summary-loading="subtitleLoading || summaryLoading"
            @update:selected-format="(f) => (selectedFormat = f)"
            @download="handleDownload"
            @download-file="downloadFile"
            @reset="reset"
            @summarize="handleSummarize"
          />
          <SummaryPanel
            split
            :active-tab="activeTab"
            :video-title="videoInfo?.title ?? ''"
            :subtitle-data="subtitleData"
            :subtitle-loading="subtitleLoading"
            :subtitle-error="subtitleError"
            :summary-content="summaryContent"
            :summary-loading="summaryLoading"
            :summary-error="summaryError"
            :summary-done="summaryDone"
            :chat-messages="chatMessages"
            :chat-loading="chatLoading"
            :chat-error="chatError"
            :has-subtitle="hasSubtitle"
            :subtitle-quality-hint="subtitleQualityHint"
            @update:active-tab="(t) => (activeTab = t)"
            @chat:send="handleChatSend"
          />
        </div>
      </section>

      <Features />
      <Platforms />
      <HowItWorks />
      <Pricing />
    </main>
    <Footer />
  </div>
</template>

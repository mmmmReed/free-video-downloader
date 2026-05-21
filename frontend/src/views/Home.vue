<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useVideoDownload } from '../composables/useVideoDownload'
import { useVideoSummary } from '../composables/useVideoSummary'
import { verifyCheckoutSession } from '../api/billing'
import { fetchMe } from '../api/auth'
import type { AuthMe } from '../api/auth'
import Header from '../components/Header.vue'
import AuthModal from '../components/AuthModal.vue'
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

const billingNotice = ref<{ kind: 'success' | 'error'; message: string } | null>(null)
const authNotice = ref<string | null>(null)
let authNoticeTimer: ReturnType<typeof setTimeout> | null = null
const userMe = ref<AuthMe | null>(null)
const showAuth = ref(false)

async function loadMe() {
  const t = localStorage.getItem('auth_token')
  if (!t) {
    userMe.value = null
    return
  }
  try {
    userMe.value = await fetchMe()
  } catch {
    userMe.value = null
    localStorage.removeItem('auth_token')
  }
}

function onLoggedIn(payload: { token: string; mode: 'login' | 'register' }) {
  localStorage.setItem('auth_token', payload.token)
  if (authNoticeTimer) {
    clearTimeout(authNoticeTimer)
    authNoticeTimer = null
  }
  authNotice.value =
    payload.mode === 'register'
      ? '注册成功，已自动登录。可使用下载与 AI 总结（免费每日有限次，开通 VIP 不限）。'
      : '登录成功，欢迎回来。'
  authNoticeTimer = setTimeout(() => {
    authNotice.value = null
    authNoticeTimer = null
  }, 6000)
  loadMe()
}

function logout() {
  localStorage.removeItem('auth_token')
  userMe.value = null
}

onMounted(async () => {
  await loadMe()
  const sp = new URLSearchParams(window.location.search)
  const sid = sp.get('stripe_session_id')
  if (!sid) return

  if (!localStorage.getItem('auth_token')) {
    billingNotice.value = {
      kind: 'error',
      message: '请先登录账号后再校验支付结果（需与付款时使用同一账号）。',
    }
    window.history.replaceState({}, '', window.location.pathname + window.location.hash)
    return
  }

  try {
    const r = await verifyCheckoutSession(sid)
    billingNotice.value = {
      kind: 'success',
      message: r.is_vip
        ? 'VIP 已生效：AI 总结在会员有效期内不限次数。到期后请再次购买续费。'
        : '支付结果已确认，若页面未显示 VIP 请刷新或稍后查看个人状态。',
    }
    await loadMe()
  } catch {
    billingNotice.value = {
      kind: 'error',
      message:
        '支付校验失败。若已完成付款请勿重复支付，请稍后重试或查看 Stripe 收据邮件。',
    }
  }
  window.history.replaceState({}, '', window.location.pathname + window.location.hash)
})

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
  const notice = subtitleData.value?.quality_notice
  subtitleQualityHint.value =
    !!subtitleError.value ||
    !hasSubtitle.value ||
    !text ||
    (subtitleData.value?.source === 'fallback_meta' && !notice)

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
    <Header
      :user-email="userMe?.email ?? null"
      :is-vip="userMe?.is_vip ?? false"
      :vip-until="userMe?.vip_until ?? null"
      @open-auth="showAuth = true"
      @logout="logout"
    />
    <div
      v-if="authNotice"
      class="max-w-4xl mx-auto px-4 pt-4 relative z-20"
      role="status"
    >
      <div class="rounded-2xl px-4 py-3 text-sm border shadow-sm bg-blue-50 border-blue-100 text-blue-900">
        {{ authNotice }}
      </div>
    </div>
    <div
      v-if="billingNotice"
      class="max-w-4xl mx-auto px-4 pt-4 relative z-20"
      role="status"
    >
      <div
        :class="[
          'rounded-2xl px-4 py-3 text-sm border shadow-sm',
          billingNotice.kind === 'success'
            ? 'bg-green-50 border-green-100 text-green-800'
            : 'bg-red-50 border-red-100 text-red-800',
        ]"
      >
        {{ billingNotice.message }}
      </div>
    </div>
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
            :subtitle-quality-hint="!!userMe && subtitleQualityHint"
            :subtitle-quality-notice="userMe ? subtitleData?.quality_notice : undefined"
            @update:active-tab="(t) => (activeTab = t)"
            @chat:send="handleChatSend"
          />
        </div>
      </section>

      <Features />
      <Platforms />
      <HowItWorks />
      <Pricing
        :is-logged-in="!!userMe"
        :is-vip="userMe?.is_vip ?? false"
        :vip-until="userMe?.vip_until ?? null"
        @open-auth="showAuth = true"
      />
    </main>
    <Footer />
    <AuthModal v-model:open="showAuth" @logged-in="onLoggedIn" />
  </div>
</template>

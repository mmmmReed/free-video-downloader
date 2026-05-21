<script setup lang="ts">
import { ref } from 'vue'
import { Search, Loader2 } from 'lucide-vue-next'

const autoSummarizeAfterParse = defineModel<boolean>('autoSummarizeAfterParse', {
  default: true,
})

const props = defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  parse: [url: string]
}>()

const url = ref('')

function extractUrl(text: string): string {
  const match = text.match(/https?:\/\/[^\s<>"{}|\\^`\[\]]+/i)
  return match ? match[0] : text.trim()
}

function handleSubmit() {
  const extracted = extractUrl(url.value)
  if (extracted) {
    emit('parse', extracted)
  }
}
</script>

<template>
  <section class="relative overflow-hidden bg-gradient-to-b from-blue-50 via-white to-bg pt-10 pb-6 sm:pt-11 sm:pb-7">
    <!-- Decorative blobs -->
    <div class="absolute top-0 left-1/4 w-96 h-96 bg-blue-100 rounded-full blur-3xl opacity-40 -translate-y-1/2" />
    <div class="absolute top-20 right-1/4 w-72 h-72 bg-indigo-100 rounded-full blur-3xl opacity-30" />

    <div class="relative max-w-4xl mx-auto px-4 text-center">
      <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-text leading-tight mb-2.5 sm:mb-3">
        万能视频下载总结器，<span class="text-primary">一键搞定</span>
      </h1>
      <p class="text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto mb-4 sm:mb-5 leading-relaxed">
        支持 YouTube、B站、TikTok、Instagram 等 <strong class="text-primary">1700+</strong> 平台，粘贴链接即可高清下载与 AI 总结，手机也能用
      </p>

      <form
        @submit.prevent="handleSubmit"
        class="max-w-2xl mx-auto flex items-center gap-3 bg-white rounded-2xl shadow-lg shadow-blue-100/50 p-2 border border-gray-100"
      >
        <div class="flex-1 flex items-center gap-3 px-4">
          <Search class="w-5 h-5 text-text-muted flex-shrink-0" />
          <input
            v-model="url"
            type="text"
            placeholder="粘贴视频链接，例如 https://www.youtube.com/watch?v=..."
            class="w-full py-3 text-base outline-none bg-transparent placeholder:text-gray-400"
            :disabled="loading"
          />
        </div>
        <button
          type="submit"
          :disabled="loading || !url.trim()"
          class="px-8 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/30 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md flex items-center gap-2 shadow-md shadow-primary/20 cursor-pointer"
        >
          <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
          <span>{{ loading ? '解析中...' : '解析视频' }}</span>
        </button>
      </form>

      <label
        class="flex items-start justify-center gap-3 mt-3 text-left text-sm text-text-secondary cursor-pointer select-none max-w-2xl mx-auto px-1"
      >
        <input
          v-model="autoSummarizeAfterParse"
          type="checkbox"
          class="mt-0.5 size-4 shrink-0 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
        />
        <span class="leading-relaxed">
          解析后自动进行 AI 总结（取消勾选则仅解析，本次不会自动总结）
        </span>
      </label>

      <p class="mt-2.5 text-sm text-text-muted mb-2.5 sm:mb-3">
          下载解析免费 · AI 总结需登录（免费每日 1 次 / VIP ¥9.9·30 天）· 支持手机
      </p>
    </div>
  </section>
</template>

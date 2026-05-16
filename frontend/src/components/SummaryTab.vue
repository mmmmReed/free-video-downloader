<script setup lang="ts">
import { computed, watch, ref, nextTick } from 'vue'
import { marked } from 'marked'
import { Loader2, Copy, Check } from 'lucide-vue-next'

marked.setOptions({
  gfm: true,
  breaks: true,
})

const props = defineProps<{
  content: string
  loading: boolean
  error: string
  done: boolean
}>()

const copied = ref(false)
const contentRef = ref<HTMLElement | null>(null)

const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked.parse(props.content, { async: false }) as string
})

watch(() => props.content, async () => {
  await nextTick()
  if (contentRef.value) {
    contentRef.value.scrollTop = contentRef.value.scrollHeight
  }
})

async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
  }
}
</script>

<template>
  <div class="flex flex-col flex-1 min-h-0">
    <!-- Loading State -->
    <div v-if="loading && !content" class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <Loader2 class="w-8 h-8 animate-spin mb-3 text-primary" />
      <p class="text-sm">AI 正在分析视频内容...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center gap-2 text-red-500 bg-red-50 px-4 py-3 rounded-xl text-sm">
      {{ error }}
    </div>

    <!-- Content -->
    <div v-else-if="content" class="flex flex-col flex-1 min-h-0">
      <!-- Toolbar -->
      <div v-if="done" class="flex justify-end mb-3">
        <button
          type="button"
          @click="copyContent"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
        >
          <Check v-if="copied" class="w-3.5 h-3.5 text-green-500" />
          <Copy v-else class="w-3.5 h-3.5" />
          {{ copied ? '已复制' : '复制' }}
        </button>
      </div>

      <article
        ref="contentRef"
        class="summary-markdown prose prose-slate prose-sm sm:prose-base max-w-none overflow-y-auto flex-1 min-h-0 rounded-xl border border-gray-100 bg-gray-50/60 px-4 py-4 sm:px-6 sm:py-5
          prose-headings:scroll-mt-4 prose-headings:font-semibold prose-headings:text-text prose-headings:tracking-tight
          prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
          prose-p:text-text-secondary prose-p:leading-relaxed
          prose-li:text-text-secondary prose-li:marker:text-primary
          prose-strong:text-text prose-strong:font-semibold
          prose-a:text-primary prose-a:font-medium prose-a:no-underline hover:prose-a:underline
          prose-code:text-[0.9em] prose-code:font-mono prose-code:text-primary-dark prose-code:bg-blue-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none
          prose-pre:rounded-xl prose-pre:border prose-pre:border-gray-200 prose-pre:shadow-sm
          prose-blockquote:border-l-primary prose-blockquote:text-text-secondary prose-blockquote:not-italic
          prose-hr:border-border
          prose-img:rounded-lg prose-img:border prose-img:border-gray-100 prose-img:shadow-sm"
        v-html="renderedHtml"
      />

      <!-- Streaming indicator -->
      <div v-if="loading" class="flex items-center gap-2 mt-3 text-xs text-text-secondary">
        <Loader2 class="w-3.5 h-3.5 animate-spin" />
        <span>正在生成中...</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-16 text-text-secondary px-4 text-center">
      <p class="text-sm leading-relaxed">
        点击左侧「AI 总结」开始分析；若已勾选「解析后自动总结」，解析成功后会自动在「总结摘要」中开始。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, nextTick } from 'vue'
import { marked } from 'marked'
import { Loader2, Copy, Check } from 'lucide-vue-next'

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
  <div class="flex flex-col h-full">
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
    <div v-else-if="content" class="flex flex-col h-full">
      <!-- Toolbar -->
      <div v-if="done" class="flex justify-end mb-3">
        <button
          @click="copyContent"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <Check v-if="copied" class="w-3.5 h-3.5 text-green-500" />
          <Copy v-else class="w-3.5 h-3.5" />
          {{ copied ? '已复制' : '复制' }}
        </button>
      </div>

      <!-- Markdown Content -->
      <div
        ref="contentRef"
        class="prose prose-sm max-w-none overflow-y-auto flex-1 prose-headings:text-text prose-p:text-text-secondary prose-li:text-text-secondary prose-strong:text-text"
        v-html="renderedHtml"
      />

      <!-- Streaming indicator -->
      <div v-if="loading" class="flex items-center gap-2 mt-3 text-xs text-text-secondary">
        <Loader2 class="w-3.5 h-3.5 animate-spin" />
        <span>正在生成中...</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <p class="text-sm">点击上方"AI 总结"按钮开始分析视频</p>
    </div>
  </div>
</template>

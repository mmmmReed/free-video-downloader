<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import { Send, Loader2, MessageCircle } from 'lucide-vue-next'
import type { ChatMessage } from '../types/summary'

const props = defineProps<{
  messages: ChatMessage[]
  loading: boolean
  error: string
  hasSubtitle: boolean
}>()

const emit = defineEmits<{
  send: [question: string]
}>()

const inputText = ref('')
const messagesRef = ref<HTMLElement | null>(null)

const quickQuestions = [
  '这个视频的主要内容是什么？',
  '视频中有哪些关键结论？',
  '帮我列出视频的重点知识',
]

function handleSend() {
  const question = inputText.value.trim()
  if (!question || props.loading) return
  emit('send', question)
  inputText.value = ''
}

function handleQuickQuestion(q: string) {
  if (props.loading) return
  emit('send', q)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  return marked.parse(text, { async: false }) as string
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  }
)

watch(
  () => props.messages[props.messages.length - 1]?.content,
  async () => {
    await nextTick()
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  }
)
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Not ready -->
    <div v-if="!hasSubtitle" class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <MessageCircle class="w-8 h-8 mb-3 opacity-50" />
      <p class="text-sm">需要先提取字幕才能开始对话</p>
    </div>

    <template v-else>
      <!-- Messages Area -->
      <div ref="messagesRef" class="flex-1 overflow-y-auto space-y-4 mb-4">
        <!-- Empty state -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center py-8">
          <MessageCircle class="w-10 h-10 text-primary/30 mb-4" />
          <p class="text-sm text-text-secondary mb-4">基于视频内容提问，AI 会帮你解答</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button
              v-for="q in quickQuestions"
              :key="q"
              @click="handleQuickQuestion(q)"
            class="px-3 py-1.5 text-xs bg-blue-50 text-primary rounded-full border border-transparent hover:bg-blue-100 hover:border-primary/20 hover:shadow-sm active:scale-[0.98] transition-all cursor-pointer"
            >
              {{ q }}
            </button>
          </div>
        </div>

        <!-- Chat messages -->
        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <div
            :class="[
              'max-w-[80%] px-4 py-3 rounded-2xl text-sm',
              msg.role === 'user'
                ? 'bg-primary text-white rounded-br-md'
                : 'bg-gray-100 text-text-secondary rounded-bl-md',
            ]"
          >
            <div
              v-if="msg.role === 'assistant'"
              class="prose prose-sm max-w-none prose-p:my-1 prose-li:my-0"
              v-html="renderMarkdown(msg.content) || '<span class=\'opacity-50\'>思考中...</span>'"
            />
            <span v-else>{{ msg.content }}</span>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="loading && messages.length > 0" class="flex items-center gap-2 text-xs text-text-secondary pl-2">
          <Loader2 class="w-3.5 h-3.5 animate-spin" />
          <span>AI 正在回复...</span>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="text-red-500 text-xs bg-red-50 px-3 py-2 rounded-lg mb-2">
        {{ error }}
      </div>

      <!-- Input Area -->
      <div class="flex gap-2 items-end">
        <textarea
          v-model="inputText"
          @keydown="handleKeydown"
          :disabled="loading"
          placeholder="输入你的问题..."
          rows="1"
          class="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
        />
        <button
          @click="handleSend"
          :disabled="!inputText.trim() || loading"
          class="p-2.5 bg-primary text-white rounded-xl hover:bg-primary-dark hover:shadow-md active:scale-[0.95] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none cursor-pointer"
        >
          <Send class="w-4 h-4" />
        </button>
      </div>
    </template>
  </div>
</template>

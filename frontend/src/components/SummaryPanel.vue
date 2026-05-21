<script setup lang="ts">
import {
  FileText,
  Sparkles,
  Subtitles,
  Network,
  MessageCircle,
  AlertTriangle,
} from 'lucide-vue-next'
import SummaryTab from './SummaryTab.vue'
import SubtitleTab from './SubtitleTab.vue'
import MindMapTab from './MindMapTab.vue'
import ChatTab from './ChatTab.vue'
import type { SubtitleData, ChatMessage } from '../types/summary'

const props = defineProps<{
  activeTab: 'summary' | 'subtitle' | 'mindmap' | 'chat'
  videoTitle?: string
  subtitleData: SubtitleData | null
  subtitleLoading: boolean
  subtitleError: string
  summaryContent: string
  summaryLoading: boolean
  summaryError: string
  summaryDone: boolean
  chatMessages: ChatMessage[]
  chatLoading: boolean
  chatError: string
  hasSubtitle: boolean
  /** 与 VideoResult 并排：独立圆角卡片 */
  split?: boolean
  /** 无有效字幕时提示总结质量可能下降 */
  subtitleQualityHint?: boolean
  /** 后端返回的详细说明（如抖音仅文案兜底） */
  subtitleQualityNotice?: string
}>()

const emit = defineEmits<{
  'update:activeTab': [tab: 'summary' | 'subtitle' | 'mindmap' | 'chat']
  'chat:send': [question: string]
}>()

function tabBtnClass(id: 'summary' | 'subtitle' | 'mindmap' | 'chat') {
  const active = props.activeTab === id
  if (active && id === 'mindmap') {
    return [
      'flex items-center gap-2 px-4 sm:px-5 py-3.5 text-sm font-medium cursor-pointer transition-all border-b-2 -mb-px rounded-t-lg shrink-0',
      'border-pink-500 text-pink-600 bg-white',
    ]
  }
  if (active) {
    return [
      'flex items-center gap-2 px-4 sm:px-5 py-3.5 text-sm font-medium cursor-pointer transition-all border-b-2 -mb-px rounded-t-lg shrink-0',
      'border-primary text-primary bg-white',
    ]
  }
  return [
    'flex items-center gap-2 px-4 sm:px-5 py-3.5 text-sm font-medium cursor-pointer transition-all border-b-2 -mb-px rounded-t-lg shrink-0',
    'border-transparent text-text-secondary hover:text-text hover:border-gray-200 hover:bg-gray-50/80',
  ]
}
</script>

<template>
  <section
    :class="
      props.split
        ? 'min-w-0 flex flex-col flex-1 min-h-0 h-full relative z-10'
        : 'max-w-4xl mx-auto px-4 mb-16 relative z-10'
    "
  >
    <div
      :class="
        props.split
          ? 'flex flex-col flex-1 min-h-0 overflow-hidden bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100'
          : 'bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100 overflow-hidden'
      "
    >
      <div
        v-if="props.subtitleQualityHint || props.subtitleQualityNotice"
        class="flex gap-2.5 mx-4 mt-4 mb-1 px-3.5 py-3 rounded-xl text-sm text-amber-900 bg-amber-50 border border-amber-100/90"
        role="status"
      >
        <AlertTriangle class="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
        <div class="leading-relaxed space-y-2">
          <p v-if="props.subtitleQualityNotice">{{ props.subtitleQualityNotice }}</p>
          <p v-if="props.subtitleQualityHint">
            当前未能获取到足够完整的字幕时，总结可能偏泛、不够贴合视频细节。若平台支持字幕，请在「字幕文本」页核对实际内容。
          </p>
        </div>
      </div>

      <!-- Tab Bar：横向不足时可滑动；禁止纵向滚动条 -->
      <div
        class="flex flex-nowrap items-center border-b border-gray-100 flex-shrink-0 overflow-x-auto overflow-y-hidden"
      >
        <button type="button" :class="tabBtnClass('summary')" @click="emit('update:activeTab', 'summary')">
          <span class="relative inline-flex h-5 w-5 shrink-0 items-center justify-center" aria-hidden="true">
            <FileText
              class="h-4 w-4"
              :class="activeTab === 'summary' ? 'text-primary' : 'text-text-secondary'"
              stroke-width="2"
            />
            <Sparkles
              class="absolute -right-1 -top-0.5 h-2.5 w-2.5 text-amber-500"
              stroke-width="2.5"
              aria-hidden="true"
            />
          </span>
          总结摘要
        </button>
        <button type="button" :class="tabBtnClass('subtitle')" @click="emit('update:activeTab', 'subtitle')">
          <Subtitles
            class="h-4 w-4 shrink-0"
            :class="activeTab === 'subtitle' ? 'text-primary' : 'text-text-secondary'"
            stroke-width="2"
          />
          字幕文本
        </button>
        <button type="button" :class="tabBtnClass('mindmap')" @click="emit('update:activeTab', 'mindmap')">
          <Network
            class="h-4 w-4 shrink-0"
            :class="activeTab === 'mindmap' ? 'text-pink-500' : 'text-text-secondary'"
            stroke-width="2"
          />
          思维导图
        </button>
        <button type="button" :class="tabBtnClass('chat')" @click="emit('update:activeTab', 'chat')">
          <MessageCircle
            class="h-4 w-4 shrink-0"
            :class="activeTab === 'chat' ? 'text-primary' : 'text-text-secondary'"
            stroke-width="2"
          />
          AI 问答
        </button>
      </div>

      <!-- Tab Content：思维导图需要更高可视区域 -->
      <div
        :class="[
          'p-6 min-h-[300px] flex flex-col overflow-hidden flex-1 min-h-0',
          activeTab === 'mindmap'
            ? props.split
              ? 'max-h-[min(85vh,880px)]'
              : 'max-h-[min(92vh,960px)]'
            : props.split
              ? 'max-h-[min(70vh,560px)]'
              : 'max-h-[600px]',
        ]"
      >
        <SummaryTab
          v-if="activeTab === 'summary'"
          class="flex-1 min-h-0"
          :content="summaryContent"
          :loading="summaryLoading"
          :error="summaryError"
          :done="summaryDone"
        />
        <SubtitleTab
          v-else-if="activeTab === 'subtitle'"
          class="flex-1 min-h-0"
          :video-title="videoTitle"
          :data="subtitleData"
          :loading="subtitleLoading"
          :error="subtitleError"
        />
        <MindMapTab
          v-else-if="activeTab === 'mindmap'"
          class="flex-1 min-h-0"
          :content="summaryContent"
          :loading="summaryLoading"
        />
        <ChatTab
          v-else-if="activeTab === 'chat'"
          class="flex-1 min-h-0"
          :messages="chatMessages"
          :loading="chatLoading"
          :error="chatError"
          :has-subtitle="hasSubtitle"
          @send="(q) => emit('chat:send', q)"
        />
      </div>
    </div>
  </section>
</template>

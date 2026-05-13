<script setup lang="ts">
import { FileText, Subtitles, Brain, MessageCircle } from 'lucide-vue-next'
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
}>()

const emit = defineEmits<{
  'update:activeTab': [tab: 'summary' | 'subtitle' | 'mindmap' | 'chat']
  'chat:send': [question: string]
}>()

const tabs = [
  { id: 'summary' as const, label: '总结', icon: FileText },
  { id: 'subtitle' as const, label: '字幕', icon: Subtitles },
  { id: 'mindmap' as const, label: '思维导图', icon: Brain },
  { id: 'chat' as const, label: 'AI 问答', icon: MessageCircle },
]
</script>

<template>
  <section class="max-w-4xl mx-auto px-4 mb-16 relative z-10">
    <div class="bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100 overflow-hidden">
      <!-- Tab Bar -->
      <div class="flex border-b border-gray-100">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="emit('update:activeTab', tab.id)"
          :class="[
            'flex items-center gap-2 px-5 py-3.5 text-sm font-medium cursor-pointer transition-all border-b-2 -mb-px rounded-t-lg',
            activeTab === tab.id
              ? 'border-primary text-primary bg-white'
              : 'border-transparent text-text-secondary hover:text-text hover:border-gray-200 hover:bg-gray-50/80',
          ]"
        >
          <component :is="tab.icon" class="w-4 h-4" />
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content：思维导图需要更高可视区域 -->
      <div
        :class="[
          'p-6 min-h-[300px] flex flex-col overflow-hidden',
          activeTab === 'mindmap' ? 'max-h-[min(92vh,960px)]' : 'max-h-[600px]',
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

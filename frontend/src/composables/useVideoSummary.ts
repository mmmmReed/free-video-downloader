import { ref, computed } from 'vue'
import type { SubtitleData, ChatMessage } from '../types/summary'
import { fetchSubtitle, subscribeSummarize, subscribeChat } from '../api/summary'

export function useVideoSummary() {
  const subtitleData = ref<SubtitleData | null>(null)
  const subtitleLoading = ref(false)
  const subtitleError = ref('')

  const summaryContent = ref('')
  const summaryLoading = ref(false)
  const summaryError = ref('')
  const summaryDone = ref(false)

  const chatMessages = ref<ChatMessage[]>([])
  const chatLoading = ref(false)
  const chatError = ref('')

  const activeTab = ref<'summary' | 'subtitle' | 'mindmap' | 'chat'>('summary')

  let cancelSummarize: (() => void) | null = null
  let cancelChat: (() => void) | null = null

  const hasSubtitle = computed(() =>
    !!subtitleData.value && subtitleData.value.segments.length > 0
  )

  async function loadSubtitle(url: string) {
    subtitleLoading.value = true
    subtitleError.value = ''
    subtitleData.value = null

    try {
      const res = await fetchSubtitle(url)
      if (res.success) {
        subtitleData.value = res.data
      } else {
        subtitleError.value = res.error || res.data?.error || '字幕提取失败'
        subtitleData.value = res.data
      }
    } catch (e: any) {
      subtitleError.value = e.response?.data?.detail || e.message || '字幕提取失败'
    } finally {
      subtitleLoading.value = false
    }
  }

  function startSummarize(url: string, videoTitle: string) {
    cancelSummarize?.()
    summaryContent.value = ''
    summaryLoading.value = true
    summaryError.value = ''
    summaryDone.value = false

    const subtitleText = subtitleData.value?.full_text || ''

    cancelSummarize = subscribeSummarize(
      url,
      subtitleText,
      videoTitle,
      (chunk) => {
        if (chunk.done) {
          summaryLoading.value = false
          summaryDone.value = true
        } else {
          summaryContent.value += chunk.content
        }
      },
      (error) => {
        summaryError.value = error
        summaryLoading.value = false
      }
    )
  }

  function sendChatMessage(
    subtitleText: string,
    videoTitle: string,
    question: string
  ) {
    cancelChat?.()
    chatLoading.value = true
    chatError.value = ''

    chatMessages.value.push({ role: 'user', content: question })
    chatMessages.value.push({ role: 'assistant', content: '' })

    const assistantIndex = chatMessages.value.length - 1
    const historyForApi = chatMessages.value
      .slice(0, -2)
      .map((m) => ({ role: m.role, content: m.content }))

    cancelChat = subscribeChat(
      subtitleText,
      videoTitle,
      historyForApi,
      question,
      (chunk) => {
        if (chunk.done) {
          chatLoading.value = false
        } else {
          chatMessages.value[assistantIndex] = {
            role: 'assistant',
            content: chatMessages.value[assistantIndex].content + chunk.content,
          }
        }
      },
      (error) => {
        chatError.value = error
        chatLoading.value = false
      }
    )
  }

  function resetSummary() {
    cancelSummarize?.()
    cancelChat?.()
    subtitleData.value = null
    subtitleLoading.value = false
    subtitleError.value = ''
    summaryContent.value = ''
    summaryLoading.value = false
    summaryError.value = ''
    summaryDone.value = false
    chatMessages.value = []
    chatLoading.value = false
    chatError.value = ''
    activeTab.value = 'summary'
  }

  return {
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
  }
}

export interface SubtitleSegment {
  start: number
  end: number
  text: string
}

export interface SubtitleData {
  segments: SubtitleSegment[]
  full_text: string
  language: string
  source: 'manual' | 'auto' | 'fallback_meta' | ''
  /** 后端提示：如抖音仅拿到简介文案时的说明 */
  quality_notice?: string
  error?: string
}

export interface SubtitleResponse {
  success: boolean
  data: SubtitleData
  error?: string
}

export interface SummarizeStreamChunk {
  content: string
  done: boolean
}

export interface ChatStreamChunk {
  content: string
  done: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface SubtitleSegment {
  start: number
  end: number
  text: string
}

export interface SubtitleData {
  segments: SubtitleSegment[]
  full_text: string
  language: string
  source: 'manual' | 'auto' | ''
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

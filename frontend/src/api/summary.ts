import axios from 'axios'
import type { SubtitleResponse, SummarizeStreamChunk, ChatStreamChunk, ChatMessage } from '../types/summary'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function fetchSubtitle(url: string): Promise<SubtitleResponse> {
  const { data } = await api.post<SubtitleResponse>('/subtitle', { url })
  return data
}

export function subscribeSummarize(
  url: string,
  subtitleText: string,
  videoTitle: string,
  onChunk: (chunk: SummarizeStreamChunk) => void,
  onError: (error: string) => void
): () => void {
  const controller = new AbortController()

  fetch('/api/summarize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      subtitle_text: subtitleText,
      video_title: videoTitle,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errBody = await response.json().catch(() => null)
        onError(errBody?.detail || `请求失败 (${response.status})`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        onError('无法读取响应流')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.slice(5).trim()
            if (jsonStr === '[DONE]') continue
            try {
              const chunk: SummarizeStreamChunk = JSON.parse(jsonStr)
              onChunk(chunk)
            } catch {
              // skip malformed chunks
            }
          } else if (trimmed.startsWith('event:') && trimmed.includes('error')) {
            // next data line will contain error info
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message || '总结请求失败')
      }
    })

  return () => controller.abort()
}

export function subscribeChat(
  subtitleText: string,
  videoTitle: string,
  history: ChatMessage[],
  question: string,
  onChunk: (chunk: ChatStreamChunk) => void,
  onError: (error: string) => void
): () => void {
  const controller = new AbortController()

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      subtitle_text: subtitleText,
      video_title: videoTitle,
      history,
      question,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errBody = await response.json().catch(() => null)
        onError(errBody?.detail || `请求失败 (${response.status})`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        onError('无法读取响应流')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.slice(5).trim()
            if (jsonStr === '[DONE]') continue
            try {
              const chunk: ChatStreamChunk = JSON.parse(jsonStr)
              onChunk(chunk)
            } catch {
              // skip malformed chunks
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message || '对话请求失败')
      }
    })

  return () => controller.abort()
}

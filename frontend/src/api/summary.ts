import { getApiBase } from './base'
import { http } from './http'
import type { SubtitleResponse, SummarizeStreamChunk, ChatStreamChunk, ChatMessage } from '../types/summary'

export async function fetchSubtitle(url: string): Promise<SubtitleResponse> {
  const { data } = await http.post<SubtitleResponse>('/subtitle', { url })
  return data
}

function summarizeAuthHeaders(): Record<string, string> {
  const t = localStorage.getItem('auth_token')
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

export function subscribeSummarize(
  url: string,
  subtitleText: string,
  videoTitle: string,
  onChunk: (chunk: SummarizeStreamChunk) => void,
  onError: (error: string) => void
): () => void {
  const controller = new AbortController()

  fetch(`${getApiBase()}/summarize`, {
    method: 'POST',
    headers: summarizeAuthHeaders(),
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
        const d = errBody?.detail
        const msg =
          typeof d === 'string'
            ? d
            : Array.isArray(d)
              ? d.map((x: { msg?: string }) => x.msg).filter(Boolean).join('; ')
              : `请求失败 (${response.status})`
        onError(msg)
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

  fetch(`${getApiBase()}/chat`, {
    method: 'POST',
    headers: summarizeAuthHeaders(),
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
        const d = errBody?.detail
        const msg =
          typeof d === 'string'
            ? d
            : Array.isArray(d)
              ? d.map((x: { msg?: string }) => x.msg).filter(Boolean).join('; ')
              : `请求失败 (${response.status})`
        onError(msg)
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

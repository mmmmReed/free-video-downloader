import { getApiBase } from './base'
import { http } from './http'
import type { ParseResponse, DownloadResponse, ProgressData } from '../types/video'

export async function parseVideo(url: string): Promise<ParseResponse> {
  const { data } = await http.post<ParseResponse>('/parse', { url })
  return data
}

export async function startDownload(url: string, formatId: string): Promise<DownloadResponse> {
  const { data } = await http.post<DownloadResponse>('/download', {
    url,
    format_id: formatId,
  })
  return data
}

export function subscribeProgress(
  taskId: string,
  onProgress: (data: ProgressData) => void,
  onError: (error: string) => void
): () => void {
  const eventSource = new EventSource(`${getApiBase()}/progress/${taskId}`)


  eventSource.onmessage = (event) => {
    try {
      const data: ProgressData = JSON.parse(event.data)
      onProgress(data)
      if (data.status === 'finished' || data.status === 'error') {
        eventSource.close()
      }
    } catch {
      onError('Failed to parse progress data')
      eventSource.close()
    }
  }

  eventSource.onerror = () => {
    onError('Connection lost')
    eventSource.close()
  }

  return () => eventSource.close()
}

export function getFileUrl(taskId: string): string {
  return `${getApiBase()}/file/${taskId}`
}

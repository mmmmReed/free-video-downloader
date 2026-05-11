import { ref, computed } from 'vue'
import type { VideoInfo, VideoFormat, ProgressData } from '../types/video'
import { parseVideo, startDownload, subscribeProgress, getFileUrl } from '../api/video'

export function useVideoDownload() {
  const videoInfo = ref<VideoInfo | null>(null)
  const loading = ref(false)
  const error = ref('')
  const progress = ref<ProgressData | null>(null)
  const selectedFormat = ref<VideoFormat | null>(null)
  const currentTaskId = ref('')

  let unsubscribe: (() => void) | null = null

  const isDownloading = computed(() =>
    progress.value?.status === 'downloading' || progress.value?.status === 'merging'
  )

  const isFinished = computed(() => progress.value?.status === 'finished')

  async function parse(url: string) {
    loading.value = true
    error.value = ''
    videoInfo.value = null
    progress.value = null
    selectedFormat.value = null
    currentTaskId.value = ''

    try {
      const res = await parseVideo(url)
      if (res.success) {
        videoInfo.value = res.data
        if (res.data.formats.length > 0) {
          selectedFormat.value = res.data.formats[0]
        }
      }
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '解析失败，请检查链接是否正确'
    } finally {
      loading.value = false
    }
  }

  async function download(url: string) {
    if (!selectedFormat.value) return

    error.value = ''
    progress.value = { status: 'pending', percentage: 0, speed: '', eta: 0, filename: '', error: '' }

    try {
      const res = await startDownload(url, selectedFormat.value.format_id)
      if (res.success) {
        currentTaskId.value = res.task_id
        unsubscribe = subscribeProgress(
          res.task_id,
          (data) => {
            progress.value = data
          },
          (errMsg) => {
            error.value = errMsg
          }
        )
      }
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '下载启动失败'
      progress.value = null
    }
  }

  function downloadFile() {
    if (currentTaskId.value) {
      const link = document.createElement('a')
      link.href = getFileUrl(currentTaskId.value)
      link.download = ''
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  function reset() {
    unsubscribe?.()
    videoInfo.value = null
    loading.value = false
    error.value = ''
    progress.value = null
    selectedFormat.value = null
    currentTaskId.value = ''
  }

  return {
    videoInfo,
    loading,
    error,
    progress,
    selectedFormat,
    isDownloading,
    isFinished,
    parse,
    download,
    downloadFile,
    reset,
  }
}

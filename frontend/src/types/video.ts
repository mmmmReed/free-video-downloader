export interface VideoFormat {
  format_id: string
  ext: string
  quality: string
  resolution: string
  filesize: number | null
  label: string
}

export interface VideoInfo {
  title: string
  thumbnail: string
  duration: number
  uploader: string
  webpage_url: string
  formats: VideoFormat[]
}

export interface ParseResponse {
  success: boolean
  data: VideoInfo
}

export interface DownloadResponse {
  success: boolean
  task_id: string
}

export interface ProgressData {
  status: 'pending' | 'downloading' | 'merging' | 'finished' | 'error'
  percentage: number
  speed: string
  eta: number
  filename: string
  error: string
}

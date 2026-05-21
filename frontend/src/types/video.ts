export interface VideoFormat {
  format_id: string
  ext: string
  quality: string
  resolution: string
  filesize: number | null
  /** 抖音：由码率估算的大小时为 true，HEAD/Range 探测到的一般为 false */
  filesize_approx?: boolean
  label: string
}

export interface VideoInfo {
  title: string
  thumbnail: string
  duration: number
  uploader: string
  webpage_url: string
  formats: VideoFormat[]
  view_count?: number | null
  /** 抖音点赞数；播放量接口常缺失时为兜底展示 */
  like_count?: number | null
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

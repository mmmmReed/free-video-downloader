<script setup lang="ts">
import { computed } from 'vue'
import {
  Clock,
  User,
  Download,
  Check,
  Loader2,
  AlertCircle,
  Sparkles,
  SlidersHorizontal,
  FileVideo,
} from 'lucide-vue-next'
import type { VideoInfo, VideoFormat, ProgressData } from '../types/video'

const props = defineProps<{
  videoInfo: VideoInfo
  selectedFormat: VideoFormat | null
  progress: ProgressData | null
  isDownloading: boolean
  isFinished: boolean
  error: string
  summaryLoading?: boolean
  /** 与总结面板并排时：独立圆角卡片、列表式选格式 */
  split?: boolean
}>()

const emit = defineEmits<{
  'update:selectedFormat': [format: VideoFormat]
  download: []
  downloadFile: []
  reset: []
  summarize: []
}>()

function formatDuration(seconds: number): string {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatSize(bytes: number | null): string {
  if (!bytes) return '未知大小'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

const progressPercent = computed(() => props.progress?.percentage ?? 0)
</script>

<template>
  <section
    :class="
      props.split
        ? 'min-w-0 h-full flex flex-col relative z-10'
        : 'max-w-4xl mx-auto px-4 -mt-6 mb-16 relative z-10'
    "
  >
    <div
      :class="
        props.split
          ? 'flex flex-col flex-1 min-h-0 overflow-hidden bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100'
          : 'bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100 overflow-hidden'
      "
    >
      <!-- Video Info Header -->
      <div class="flex flex-col sm:flex-row gap-6 p-6">
        <div class="flex-shrink-0">
          <img
            :src="videoInfo.thumbnail"
            :alt="videoInfo.title"
            referrerpolicy="no-referrer"
            class="w-full sm:w-64 h-36 object-cover rounded-xl bg-gray-100"
          />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-lg font-bold text-text line-clamp-2 mb-3">{{ videoInfo.title }}</h3>
          <div class="flex flex-wrap items-center gap-4 text-sm text-text-secondary">
            <span class="flex items-center gap-1.5">
              <User class="w-4 h-4" />
              {{ videoInfo.uploader || '未知' }}
            </span>
            <span class="flex items-center gap-1.5">
              <Clock class="w-4 h-4" />
              {{ formatDuration(videoInfo.duration) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Format Selection -->
      <div class="px-6 pb-4">
        <div class="flex items-center gap-2 mb-3">
          <SlidersHorizontal class="w-5 h-5 text-primary shrink-0" aria-hidden="true" />
          <h4 class="text-sm font-semibold text-text">选择清晰度和格式</h4>
        </div>
        <div class="flex flex-col gap-2">
          <button
            v-for="fmt in videoInfo.formats"
            :key="fmt.format_id"
            type="button"
            @click="emit('update:selectedFormat', fmt)"
            :class="[
              'flex w-full items-start gap-3 rounded-xl border-2 px-4 py-3 text-left transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white',
              selectedFormat?.format_id === fmt.format_id
                ? 'border-primary bg-blue-50/90 shadow-sm'
                : 'border-gray-100 bg-white hover:border-primary/40 hover:bg-blue-50/30',
            ]"
            :disabled="isDownloading"
          >
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-primary"
              aria-hidden="true"
            >
              <FileVideo class="w-5 h-5" />
            </span>
            <span class="min-w-0 flex-1 pt-0.5">
              <span
                class="block text-sm font-medium leading-snug"
                :class="selectedFormat?.format_id === fmt.format_id ? 'text-primary' : 'text-text'"
              >{{ fmt.label }}</span>
              <span class="mt-0.5 block text-xs text-text-secondary">{{ formatSize(fmt.filesize) }}</span>
            </span>
          </button>
        </div>
      </div>

      <!-- Progress Bar -->
      <div v-if="progress" class="px-6 pb-4">
        <div class="bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-300"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
        <div class="flex justify-between mt-2 text-xs text-text-secondary">
          <span>
            <template v-if="progress.status === 'downloading'">
              下载中 {{ progressPercent }}% · {{ progress.speed }} · 剩余 {{ progress.eta }}s
            </template>
            <template v-else-if="progress.status === 'merging'">
              正在合并音视频...
            </template>
            <template v-else-if="progress.status === 'finished'">
              下载完成！
            </template>
            <template v-else-if="progress.status === 'error'">
              下载失败
            </template>
            <template v-else>
              准备中...
            </template>
          </span>
          <span>{{ progressPercent }}%</span>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="px-6 pb-4">
        <div class="flex items-center gap-2 text-red-500 bg-red-50 px-4 py-3 rounded-xl text-sm">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          {{ error }}
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="px-6 pb-6 flex gap-3">
        <template v-if="isFinished">
          <button
            @click="emit('downloadFile')"
            class="flex-1 py-3 bg-green-500 text-white font-semibold rounded-xl hover:bg-green-600 hover:shadow-md active:scale-[0.99] transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            <Check class="w-5 h-5" />
            保存到本地
          </button>
          <button
            @click="emit('summarize')"
            :disabled="summaryLoading"
            class="px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white font-medium rounded-xl hover:from-violet-600 hover:to-purple-600 hover:shadow-lg hover:shadow-purple-200/40 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md flex items-center gap-2 shadow-md shadow-purple-200/50 cursor-pointer"
          >
            <Loader2 v-if="summaryLoading" class="w-4 h-4 animate-spin" />
            <Sparkles v-else class="w-4 h-4" />
            AI 总结
          </button>
          <button
            @click="emit('reset')"
            class="px-6 py-3 bg-gray-100 text-text-secondary font-medium rounded-xl hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] transition-all cursor-pointer"
          >
            重新下载
          </button>
        </template>
        <template v-else>
          <button
            @click="emit('download')"
            :disabled="isDownloading || !selectedFormat"
            class="flex-1 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/25 active:scale-[0.99] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md flex items-center justify-center gap-2 shadow-md shadow-primary/20 cursor-pointer"
          >
            <Loader2 v-if="isDownloading" class="w-5 h-5 animate-spin" />
            <Download v-else class="w-5 h-5" />
            {{ isDownloading ? '下载中...' : '开始下载' }}
          </button>
          <button
            @click="emit('summarize')"
            :disabled="summaryLoading"
            class="px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white font-medium rounded-xl hover:from-violet-600 hover:to-purple-600 hover:shadow-lg hover:shadow-purple-200/40 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md flex items-center gap-2 shadow-md shadow-purple-200/50 cursor-pointer"
          >
            <Loader2 v-if="summaryLoading" class="w-4 h-4 animate-spin" />
            <Sparkles v-else class="w-4 h-4" />
            AI 总结
          </button>
        </template>
      </div>
    </div>
  </section>
</template>

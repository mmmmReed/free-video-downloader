<script setup lang="ts">
import { ref, computed } from 'vue'
import { Copy, Check, Loader2, Download } from 'lucide-vue-next'
import type { SubtitleData, SubtitleSegment } from '../types/summary'

const props = defineProps<{
  data: SubtitleData | null
  loading: boolean
  error: string
  videoTitle?: string
}>()

const copied = ref(false)

function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const sourceLabel = computed(() => {
  if (!props.data) return ''
  if (props.data.source === 'manual') return '人工字幕'
  if (props.data.source === 'auto') return '自动生成'
  return ''
})

function safeBaseName(raw: string): string {
  const base = raw.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_').replace(/\s+/g, ' ').trim().slice(0, 80)
  return base || 'subtitle'
}

const downloadBase = computed(() => {
  const lang = props.data?.language ? `_${props.data.language}` : ''
  return `${safeBaseName(props.videoTitle || '')}${lang}`
})

function formatSrtTime(seconds: number): string {
  const totalMs = Math.max(0, Math.round(Number(seconds) * 1000))
  const ms = totalMs % 1000
  let t = Math.floor(totalMs / 1000)
  const s = t % 60
  t = Math.floor(t / 60)
  const m = t % 60
  const h = Math.floor(t / 60)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

function formatVttTime(seconds: number): string {
  const totalMs = Math.max(0, Math.round(Number(seconds) * 1000))
  const ms = totalMs % 1000
  let t = Math.floor(totalMs / 1000)
  const s = t % 60
  t = Math.floor(t / 60)
  const m = t % 60
  const h = Math.floor(t / 60)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(3, '0')}`
}

function buildSrt(segments: SubtitleSegment[]): string {
  return segments
    .map((seg, i) => {
      const text = seg.text.trim()
      return `${i + 1}\n${formatSrtTime(seg.start)} --> ${formatSrtTime(seg.end)}\n${text}`
    })
    .join('\n\n')
}

function buildVtt(segments: SubtitleSegment[]): string {
  const body = segments
    .map((seg) => `${formatVttTime(seg.start)} --> ${formatVttTime(seg.end)}\n${seg.text.trim()}`)
    .join('\n\n')
  return `WEBVTT\n\n${body}\n`
}

function downloadTextFile(text: string, filename: string, mime: string) {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function downloadSrt() {
  if (!props.data?.segments.length) return
  downloadTextFile(buildSrt(props.data.segments), `${downloadBase.value}.srt`, 'text/plain;charset=utf-8')
}

function downloadVtt() {
  if (!props.data?.segments.length) return
  downloadTextFile(buildVtt(props.data.segments), `${downloadBase.value}.vtt`, 'text/plain;charset=utf-8')
}

function downloadTxt() {
  if (!props.data?.full_text) return
  const text = `\uFEFF${props.data.full_text}`
  downloadTextFile(text, `${downloadBase.value}.txt`, 'text/plain;charset=utf-8')
}

async function copyAll() {
  if (!props.data?.full_text) return
  try {
    await navigator.clipboard.writeText(props.data.full_text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <Loader2 class="w-8 h-8 animate-spin mb-3 text-primary" />
      <p class="text-sm">正在提取字幕...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center gap-2 text-red-500 bg-red-50 px-4 py-3 rounded-xl text-sm">
      {{ error }}
    </div>

    <!-- No subtitle -->
    <div v-else-if="data && data.segments.length === 0" class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <p class="text-sm">该视频没有可用的字幕</p>
    </div>

    <!-- Subtitle List -->
    <div v-else-if="data" class="flex flex-col h-full">
      <!-- Header -->
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-3">
        <div class="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
          <span v-if="sourceLabel" class="px-2 py-0.5 bg-blue-50 text-primary rounded-full">{{ sourceLabel }}</span>
          <span v-if="data.language">语言: {{ data.language }}</span>
          <span>共 {{ data.segments.length }} 条</span>
        </div>
        <div class="flex flex-wrap items-center gap-2 justify-end">
          <button
            type="button"
            @click="downloadSrt"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
          >
            <Download class="w-3.5 h-3.5" />
            SRT
          </button>
          <button
            type="button"
            @click="downloadVtt"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
          >
            <Download class="w-3.5 h-3.5" />
            VTT
          </button>
          <button
            type="button"
            @click="downloadTxt"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
          >
            <Download class="w-3.5 h-3.5" />
            纯文本
          </button>
          <button
            type="button"
            @click="copyAll"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
          >
            <Check v-if="copied" class="w-3.5 h-3.5 text-green-500" />
            <Copy v-else class="w-3.5 h-3.5" />
            {{ copied ? '已复制' : '全部复制' }}
          </button>
        </div>
      </div>

      <!-- Segments -->
      <div class="overflow-y-auto flex-1 space-y-1">
        <div
          v-for="(seg, i) in data.segments"
          :key="i"
          class="flex gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors group"
        >
          <span class="text-xs text-primary font-mono whitespace-nowrap pt-0.5 opacity-70 group-hover:opacity-100">
            {{ formatTimestamp(seg.start) }}
          </span>
          <span class="text-sm text-text-secondary leading-relaxed">
            {{ seg.text }}
          </span>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <p class="text-sm">点击"AI 总结"后将自动提取字幕</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Loader2, Maximize2, Minimize2, FileImage, FileCode2 } from 'lucide-vue-next'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'

const props = defineProps<{
  content: string
  loading: boolean
}>()

const svgRef = ref<SVGSVGElement | null>(null)
let markmapInstance: Markmap | null = null
const transformer = new Transformer()

const isFullscreen = ref(false)
const exportBusy = ref(false)
const exportHint = ref('')

let exportHintTimer: ReturnType<typeof setTimeout> | null = null

function showHint(msg: string) {
  exportHint.value = msg
  if (exportHintTimer) clearTimeout(exportHintTimer)
  exportHintTimer = setTimeout(() => {
    exportHint.value = ''
    exportHintTimer = null
  }, 4500)
}

function renderMap() {
  if (!svgRef.value || !props.content) return

  const { root } = transformer.transform(props.content)

  if (markmapInstance) {
    markmapInstance.setData(root)
    markmapInstance.fit()
  } else {
    markmapInstance = Markmap.create(svgRef.value, { autoFit: true }, root)
  }
}

watch(() => props.content, () => {
  if (props.content) {
    nextTick(renderMap)
  }
})

watch(isFullscreen, () => {
  nextTick(() => {
    markmapInstance?.fit()
  })
})

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function exitFullscreen() {
  isFullscreen.value = false
  nextTick(() => {
    markmapInstance?.fit()
  })
}

function resetView() {
  nextTick(() => {
    markmapInstance?.fit()
  })
}

function onGlobalKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isFullscreen.value) {
    exitFullscreen()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeydown)
  if (props.content) {
    nextTick(renderMap)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
  if (exportHintTimer) clearTimeout(exportHintTimer)
  if (markmapInstance) {
    markmapInstance.destroy()
    markmapInstance = null
  }
})

function buildExportSvgString(): string | null {
  const mm = markmapInstance
  const svg = svgRef.value
  if (!mm || !svg) return null

  let bb = svg.getBBox()
  if (!bb.width || !bb.height) {
    const gNode = mm.g?.node?.() as SVGGElement | undefined
    if (gNode) {
      try {
        const gBb = gNode.getBBox()
        if (gBb.width > 0 && gBb.height > 0)
          bb = gBb
      }
      catch { /* ignore */ }
    }
  }
  if (!bb.width || !bb.height) {
    showHint('思维导图尚未布局完成，请稍后再导出')
    return null
  }

  const pad = 56
  const vbW = bb.width + pad * 2
  const vbH = bb.height + pad * 2
  const vx = bb.x - pad
  const vy = bb.y - pad

  const clone = svg.cloneNode(true) as SVGSVGElement
  const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style')
  styleEl.setAttribute('type', 'text/css')
  styleEl.textContent = mm.getStyleContent()
  clone.insertBefore(styleEl, clone.firstChild)

  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
  clone.setAttribute('viewBox', `${vx} ${vy} ${vbW} ${vbH}`)
  const outW = Math.ceil(vbW)
  const outH = Math.ceil(vbH)
  clone.setAttribute('width', String(outW))
  clone.setAttribute('height', String(outH))
  clone.removeAttribute('class')
  clone.removeAttribute('style')

  return new XMLSerializer().serializeToString(clone)
}

function downloadMindmapSvg() {
  const xml = buildExportSvgString()
  if (!xml) return

  const blob = new Blob([xml], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '思维导图.svg'
  a.click()
  URL.revokeObjectURL(url)
  showHint('已下载 SVG（矢量图，可无损放大）')
}

function drawSvgToPngBlob(xml: string, scale: number): Promise<Blob> {
  const parseExportSize = (): { w: number, h: number } | null => {
    const wm = xml.match(/width="(\d+)"/)
    const hm = xml.match(/height="(\d+)"/)
    if (wm && hm)
      return { w: Number(wm[1]), h: Number(hm[1]) }
    return null
  }

  const rasterize = (src: string, revoke?: string) =>
    new Promise<Blob>((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        if (revoke)
          URL.revokeObjectURL(revoke)
        try {
          let w = img.naturalWidth || img.width
          let h = img.naturalHeight || img.height
          if (!w || !h) {
            const parsed = parseExportSize()
            if (parsed) {
              w = parsed.w
              h = parsed.h
            }
          }
          if (!w || !h) {
            reject(new Error('size'))
            return
          }
          const canvas = document.createElement('canvas')
          canvas.width = Math.max(1, Math.ceil(w * scale))
          canvas.height = Math.max(1, Math.ceil(h * scale))
          const ctx = canvas.getContext('2d')
          if (!ctx) {
            reject(new Error('canvas'))
            return
          }
          ctx.fillStyle = '#ffffff'
          ctx.fillRect(0, 0, canvas.width, canvas.height)
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
          canvas.toBlob(
            (blob) => {
              if (!blob) {
                reject(new Error('toBlob'))
                return
              }
              resolve(blob)
            },
            'image/png',
            1,
          )
        }
        catch (e) {
          reject(e)
        }
      }
      img.onerror = () => {
        if (revoke)
          URL.revokeObjectURL(revoke)
        reject(new Error('img-load'))
      }
      img.src = src
    })

  return (async () => {
    const svgBlob = new Blob([xml], { type: 'image/svg+xml;charset=utf-8' })
    if (typeof createImageBitmap === 'function') {
      try {
        const bmp = await createImageBitmap(svgBlob)
        try {
          const canvas = document.createElement('canvas')
          canvas.width = Math.max(1, Math.ceil(bmp.width * scale))
          canvas.height = Math.max(1, Math.ceil(bmp.height * scale))
          const ctx = canvas.getContext('2d')
          if (!ctx)
            throw new Error('canvas')
          ctx.fillStyle = '#ffffff'
          ctx.fillRect(0, 0, canvas.width, canvas.height)
          ctx.drawImage(bmp, 0, 0, canvas.width, canvas.height)
          const blob = await new Promise<Blob>((res, rej) => {
            canvas.toBlob((b) => (b ? res(b) : rej(new Error('toBlob'))), 'image/png', 1)
          })
          return blob
        }
        finally {
          bmp.close()
        }
      }
      catch {
        /* fall through */
      }
    }
    const objUrl = URL.createObjectURL(svgBlob)
    try {
      return await rasterize(objUrl, objUrl)
    }
    catch {
      const dataUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(xml)}`
      return await rasterize(dataUrl)
    }
  })()
}

async function downloadMindmapPng() {
  const xml = buildExportSvgString()
  if (!xml) return

  exportBusy.value = true
  const scale = 3

  try {
    const pngBlob = await drawSvgToPngBlob(xml, scale)
    const pngUrl = URL.createObjectURL(pngBlob)
    const a = document.createElement('a')
    a.href = pngUrl
    a.download = '思维导图.png'
    a.click()
    URL.revokeObjectURL(pngUrl)
    showHint('已下载 PNG（3× 分辨率，白底）')
  } catch {
    showHint('导出 PNG 失败，请改用 SVG 导出')
  } finally {
    exportBusy.value = false
  }
}
</script>

<template>
  <!-- Teleport：父级 SummaryPanel 有 overflow:hidden，会裁掉 fixed 子节点；展开时挂到 body 才能保证「收起」按钮可见 -->
  <Teleport :disabled="!isFullscreen" to="body">
    <div
      :class="[
        'flex flex-col min-h-0',
        isFullscreen
          ? 'fixed inset-0 z-[300] h-[100dvh] bg-white pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1rem,env(safe-area-inset-bottom))] px-4 sm:px-6 sm:pt-6 sm:pb-6 shadow-2xl'
          : 'h-full flex-1',
      ]"
    >
      <div v-if="loading && !content" class="flex flex-col items-center justify-center py-16 text-text-secondary">
        <Loader2 class="w-8 h-8 animate-spin mb-3 text-primary" />
        <p class="text-sm">等待总结生成后自动渲染思维导图...</p>
      </div>

      <template v-else-if="content">
      <div
        :class="[
          'flex flex-wrap items-center gap-2 mb-3',
          isFullscreen
            ? 'sticky top-0 z-[310] shrink-0 -mx-2 px-2 py-2.5 bg-white/95 backdrop-blur-sm border border-gray-100 rounded-xl mb-4'
            : '',
        ]"
      >
        <button
          v-if="isFullscreen"
          type="button"
          @click="exitFullscreen"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-text hover:bg-text/95 shadow-md active:scale-[0.98] rounded-lg transition-all cursor-pointer"
          aria-label="收起思维导图"
        >
          <Minimize2 class="w-3.5 h-3.5" />
          收起
        </button>
        <button
          v-if="!isFullscreen"
          type="button"
          @click="toggleFullscreen"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
        >
          <Maximize2 class="w-3.5 h-3.5" />
          全屏
        </button>
        <button
          v-if="isFullscreen"
          type="button"
          @click="resetView"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
        >
          重置视图
        </button>
        <button
          type="button"
          @click="downloadMindmapSvg"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary bg-gray-100 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98] rounded-lg transition-all cursor-pointer"
        >
          <FileCode2 class="w-3.5 h-3.5" />
          导出 SVG
        </button>
        <button
          type="button"
          :disabled="exportBusy"
          @click="downloadMindmapPng"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-primary hover:bg-primary-dark hover:shadow-md active:scale-[0.98] rounded-lg transition-all disabled:opacity-60 cursor-pointer disabled:cursor-not-allowed"
        >
          <Loader2 v-if="exportBusy" class="w-3.5 h-3.5 animate-spin" />
          <FileImage v-else class="w-3.5 h-3.5" />
          导出高清 PNG
        </button>
        <span v-if="isFullscreen" class="text-[11px] text-text-muted w-full sm:w-auto sm:ml-auto text-center sm:text-right leading-snug">
          按 Esc 或点「收起」退出全屏
        </span>
      </div>

      <div
        :class="[
          'flex-1 bg-gray-50 rounded-xl overflow-hidden relative border border-gray-100 min-h-0',
          isFullscreen ? 'min-h-0' : 'min-h-[400px]',
        ]"
      >
        <svg ref="svgRef" class="w-full h-full touch-none block" :style="isFullscreen ? { minHeight: '0' } : { minHeight: '400px' }" />
      </div>

      <p v-if="exportHint" class="text-xs text-text-secondary mt-2">{{ exportHint }}</p>
    </template>

    <div v-else class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <p class="text-sm">总结完成后将自动生成思维导图</p>
    </div>
    </div>
  </Teleport>
</template>

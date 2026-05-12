<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'

const props = defineProps<{
  content: string
  loading: boolean
}>()

const svgRef = ref<SVGSVGElement | null>(null)
let markmapInstance: Markmap | null = null
const transformer = new Transformer()

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

onMounted(() => {
  if (props.content) {
    nextTick(renderMap)
  }
})

onBeforeUnmount(() => {
  if (markmapInstance) {
    markmapInstance.destroy()
    markmapInstance = null
  }
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Loading -->
    <div v-if="loading && !content" class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <Loader2 class="w-8 h-8 animate-spin mb-3 text-primary" />
      <p class="text-sm">等待总结生成后自动渲染思维导图...</p>
    </div>

    <!-- Map -->
    <div v-else-if="content" class="flex-1 min-h-[400px] bg-gray-50 rounded-xl overflow-hidden relative">
      <svg ref="svgRef" class="w-full h-full" style="min-height: 400px;" />
    </div>

    <!-- Empty -->
    <div v-else class="flex flex-col items-center justify-center py-16 text-text-secondary">
      <p class="text-sm">总结完成后将自动生成思维导图</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Download, LogOut, Crown } from 'lucide-vue-next'

const props = defineProps<{
  /** 已登录时展示邮箱 */
  userEmail: string | null
  /** 会员有效期内为 true */
  isVip?: boolean
  /** Unix 秒，到期时间 */
  vipUntil?: number | null
}>()

const emit = defineEmits<{
  openAuth: []
  logout: []
}>()

const vipHint = computed(() => {
  const t = props.vipUntil
  if (!props.isVip || !t) return ''
  const d = new Date(t * 1000)
  return `VIP 至 ${d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })}`
})
</script>

<template>
  <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 gap-4">
        <div class="flex items-center gap-2 min-w-0">
          <div class="w-9 h-9 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center shrink-0">
            <Download class="w-5 h-5 text-white" />
          </div>
          <span class="text-xl font-bold text-text truncate">
            <span class="text-primary">free</span>Video
          </span>
        </div>

        <nav class="hidden md:flex items-center gap-8 shrink-0">
          <a href="#features" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">功能</a>
          <a href="#platforms" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">支持平台</a>
          <a href="#how-it-works" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">使用方法</a>
          <a href="#pricing" class="text-text-secondary hover:text-primary transition-colors text-sm font-medium">定价</a>
        </nav>

        <div class="flex items-center gap-2 shrink-0">
          <template v-if="userEmail">
            <span
              v-if="isVip"
              class="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r from-gold to-gold-dark text-white shrink-0"
              :title="vipHint || 'VIP 会员'"
            >
              <Crown class="w-3.5 h-3.5" aria-hidden="true" />
              VIP
            </span>
            <span
              class="hidden sm:inline text-xs text-text-secondary max-w-[10rem] truncate"
              :title="vipHint ? `${userEmail} · ${vipHint}` : userEmail"
            >{{ userEmail }}</span>
            <button
              type="button"
              class="inline-flex items-center gap-1 px-3 py-2 text-text-secondary border border-gray-200 text-sm font-medium rounded-lg hover:bg-gray-50 cursor-pointer"
              @click="emit('logout')"
            >
              <LogOut class="w-4 h-4" />
              <span class="hidden sm:inline">退出</span>
            </button>
          </template>
          <button
            v-else
            type="button"
            class="px-5 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-dark hover:shadow-md active:scale-[0.98] transition-all shadow-sm cursor-pointer whitespace-nowrap"
            @click="emit('openAuth')"
          >
            登录 / 注册
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

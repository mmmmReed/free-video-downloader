<script setup lang="ts">
import { ref, watch } from 'vue'
import axios from 'axios'
import { X } from 'lucide-vue-next'
import { login, register } from '../api/auth'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  loggedIn: [payload: { token: string; mode: 'login' | 'register' }]
}>()

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

watch(
  () => props.open,
  (v) => {
    if (v) {
      errorMsg.value = ''
      loading.value = false
    }
  }
)

function close() {
  emit('update:open', false)
}

async function submit() {
  errorMsg.value = ''
  loading.value = true
  try {
    const token =
      mode.value === 'login'
        ? await login(email.value, password.value)
        : await register(email.value, password.value)
    emit('loggedIn', { token, mode: mode.value })
    emit('update:open', false)
    email.value = ''
    password.value = ''
  } catch (e) {
    if (axios.isAxiosError(e)) {
      const status = e.response?.status
      if (status === 404) {
        const reqUrl = `${e.config?.baseURL ?? ''}${e.config?.url ?? ''}`
        errorMsg.value = reqUrl
          ? `接口不存在（404）：${reqUrl}。请确认后端运行在 ${import.meta.env.VITE_API_ORIGIN?.trim() || 'http://127.0.0.1:8001'} 且已加载 /api/auth；手机访问电脑前端时请用局域网 IP 而非写死 127.0.0.1。`
          : '接口不存在（404）。请确认后端已加载 /api/auth 路由。'
      } else {
        const d = e.response?.data as { detail?: string | unknown }
        const detail = d?.detail
        errorMsg.value =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((x: { msg?: string }) => x.msg).filter(Boolean).join('; ')
              : '请求失败'
      }
    } else {
      errorMsg.value = '网络错误'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      @click.self="close"
    >
      <div
        class="relative w-full max-w-md rounded-2xl bg-white shadow-xl border border-gray-100 p-6"
      >
        <button
          type="button"
          class="absolute top-4 right-4 p-1 rounded-lg text-text-muted hover:bg-gray-100 cursor-pointer"
          aria-label="关闭"
          @click="close"
        >
          <X class="w-5 h-5" />
        </button>

        <h2 class="text-xl font-bold text-text mb-1">
          {{ mode === 'login' ? '登录' : '注册' }}
        </h2>
        <p class="text-sm text-text-secondary mb-6">
          AI 视频总结需登录；VIP 为一次性购买时长，到期后请手动续费。
        </p>

        <div class="flex gap-2 mb-4">
          <button
            type="button"
            class="flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors"
            :class="
              mode === 'login'
                ? 'border-primary text-primary bg-blue-50'
                : 'border-gray-200 text-text-secondary'
            "
            @click="mode = 'login'"
          >
            登录
          </button>
          <button
            type="button"
            class="flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors"
            :class="
              mode === 'register'
                ? 'border-primary text-primary bg-blue-50'
                : 'border-gray-200 text-text-secondary'
            "
            @click="mode = 'register'"
          >
            注册
          </button>
        </div>

        <form class="space-y-4" @submit.prevent="submit">
          <div>
            <label class="block text-sm font-medium text-text mb-1">邮箱</label>
            <input
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="you@example.com"
              required
              class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-primary focus:ring-1 focus:ring-primary outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-text mb-1">密码</label>
            <input
              v-model="password"
              type="password"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              placeholder="请输入密码"
              required
              minlength="8"
              class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-primary focus:ring-1 focus:ring-primary outline-none text-sm"
            />
            <p class="text-xs text-text-muted mt-1">至少 8 位字符</p>
          </div>

          <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-dark disabled:opacity-50 cursor-pointer"
          >
            {{ loading ? '请稍候…' : mode === 'login' ? '登录' : '注册并登录' }}
          </button>
        </form>
      </div>
    </div>
  </Teleport>
</template>

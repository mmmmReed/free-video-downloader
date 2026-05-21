/**
 * API 根路径（须含 `/api` 后缀语义：与 axios 里 `/auth/register` 等拼接）。
 *
 * - `VITE_USE_DEV_PROXY=1`：始终相对路径 `/api`，强制走 Vite `server.preview` 代理。
 * - 浏览器地址为 localhost / 127.0.0.1：直连后端（默认 http://127.0.0.1:8001），避免代理未转发导致 404；
 *   `vite preview`、本地打开 dist 等为 **生产构建**（DEV=false）时也适用。
 * - 用手机/局域网 IP 打开前端（如 http://192.168.x.x:3000）：必须用相对 `/api`，由开发机上的 Vite 代转发，
 *   不能写死 127.0.0.1（否则请求会打到手机本机）。
 *
 * 后端端口：`VITE_API_ORIGIN=http://127.0.0.1:端口`
 */

function localBrowserHost(): boolean {
  if (typeof window === 'undefined') return false
  const h = window.location.hostname
  return h === 'localhost' || h === '127.0.0.1' || h === '[::1]'
}

function directApiBase(): string {
  const origin = import.meta.env.VITE_API_ORIGIN?.trim() || 'http://127.0.0.1:8001'
  return `${origin.replace(/\/$/, '')}/api`
}

export function getApiBase(): string {
  if (import.meta.env.VITE_USE_DEV_PROXY === '1') {
    return '/api'
  }

  if (import.meta.env.DEV) {
    if (typeof window !== 'undefined' && !localBrowserHost()) {
      return '/api'
    }
    return directApiBase()
  }

  // 生产构建：仅在本地打开页面时直连后端（preview / 本地静态服务器未配置反代时）
  if (typeof window !== 'undefined' && localBrowserHost()) {
    return directApiBase()
  }

  return '/api'
}

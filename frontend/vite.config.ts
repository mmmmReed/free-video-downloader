import { defineConfig, loadEnv } from 'vite'
import type { Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

/** 构建时写入 canonical、og:url 与 JSON-LD（需配置 VITE_SITE_URL） */
function seoInjectPlugin(siteUrl: string): Plugin {
  const base = siteUrl.replace(/\/$/, '')
  return {
    name: 'seo-inject',
    transformIndexHtml(html) {
      if (!base) return html
      const canonical = `${base}/`
      const structuredData = {
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'WebSite',
            name: '万能视频下载总结器',
            description:
              '在线解析与下载多平台视频，支持高清格式与 AI 视频总结等能力。',
            url: canonical,
            inLanguage: 'zh-CN',
            publisher: {
              '@type': 'Organization',
              name: 'freeVideo',
              url: canonical,
            },
          },
          {
            '@type': 'WebApplication',
            name: '万能视频下载总结器',
            applicationCategory: 'UtilitiesApplication',
            operatingSystem: 'Any',
            browserRequirements: 'Requires JavaScript. Requires HTML5.',
            url: canonical,
            provider: {
              '@type': 'Organization',
              name: 'freeVideo',
              url: canonical,
            },
            offers: {
              '@type': 'Offer',
              price: '0',
              priceCurrency: 'CNY',
            },
          },
        ],
      }
      const block = `
    <link rel="canonical" href="${canonical}" />
    <meta property="og:url" content="${canonical}" />
    <meta name="twitter:url" content="${canonical}" />
    <script type="application/ld+json">${JSON.stringify(structuredData)}</script>`
      return html.replace('</head>', `${block}</head>`)
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const siteUrl = env.VITE_SITE_URL ?? ''

  return {
    plugins: [vue(), tailwindcss(), seoInjectPlugin(siteUrl)],
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
      },
    },
  }
})

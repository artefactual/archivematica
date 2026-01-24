/// <reference types="vitest" />
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, type ProxyOptions } from 'vite'
import vue from '@vitejs/plugin-vue'
import type { IncomingMessage, ClientRequest, IncomingHttpHeaders } from 'node:http'

const __dirname = dirname(fileURLToPath(import.meta.url))

const VITE_PROXY_TARGET = 'http://127.0.0.1:62080'

// Common proxy configuration for development server.
const createProxyConfig = (target: string, includeAuth = false): ProxyOptions => ({
  target,
  changeOrigin: true,
  secure: false,
  cookieDomainRewrite: '',
  configure: (proxy) => {
    proxy.on('proxyReq', (proxyReq: ClientRequest, req: IncomingMessage) => {
      if (includeAuth) {
        proxyReq.setHeader('Authorization', 'ApiKey test:test')
      }
      if (req.headers.cookie) {
        proxyReq.setHeader('Cookie', req.headers.cookie)
      }
    })
    proxy.on('proxyRes', (proxyRes: IncomingMessage & { headers: IncomingHttpHeaders }, req, res) => {
      const cookies = proxyRes.headers['set-cookie']
      if (cookies) {
        proxyRes.headers['set-cookie'] = cookies.map((cookie: string) =>
          cookie.replace(/Domain=[^;]+;?/gi, ''),
        )
      }
      if (req.headers.origin) {
        res.setHeader('Access-Control-Allow-Origin', req.headers.origin)
        res.setHeader('Access-Control-Allow-Credentials', 'true')
      }
    })
  },
})

export default defineConfig(({ command }) => {
  const isServing = command === 'serve'

  return {
    plugins: [vue()],
    appType: 'spa', // Single page application mode.
    test: {
      globals: true,
      environment: 'jsdom',
    },
    server: {
      port: 3000,
      cors: {
        origin: true, // Allow all origins for development.
        credentials: true,
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
      },
      proxy: {
        '/api': createProxyConfig(VITE_PROXY_TARGET, true),
        '/transfer': createProxyConfig(VITE_PROXY_TARGET),
        '/filesystem': createProxyConfig(VITE_PROXY_TARGET),
        '/administration': createProxyConfig(VITE_PROXY_TARGET),
        '/media': createProxyConfig(VITE_PROXY_TARGET),
      },
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, './lib'),
        ...(isServing
          ? {}
          : {
              vue: 'vue/dist/vue.esm-browser.prod.js',
            }),
      },
    },
    define: isServing
      ? {}
      : {
          'process.env.NODE_ENV': '"production"',
        },
    build: isServing
      ? {}
      : {
          lib: {
            name: 'Archivematica',
            entry: {
              browser: resolve(__dirname, 'lib/browser/index.ts'),
              topbar: resolve(__dirname, 'lib/topbar/index.ts'),
            },
            formats: ['es'],
          },
          cssCodeSplit: true,
        },
  }
})

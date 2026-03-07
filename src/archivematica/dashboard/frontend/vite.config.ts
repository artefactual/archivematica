/// <reference types="vitest" />
import { basename, dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, normalizePath } from 'vite'
import vue from '@vitejs/plugin-vue'

const __dirname = dirname(fileURLToPath(import.meta.url))

// Define manual chunks for better control over code splitting.
const CHUNK_ROUTES = [
  {
    name: 'icons',
    match: [
      'lib/shared/icons/',
    ],
  },
  {
    name: 'tanstack-table',
    match: [
      'node_modules/@tanstack/table-core/',
      'node_modules/@tanstack/vue-table/',
    ],
  },
  {
    name: 'runtime',
    match: [
      'node_modules/vue/',
      'node_modules/vue-i18n/',
      'node_modules/base64-helpers/',
      'lib/shared/encoding/base64',
    ],
  },
  {
    name: 'treeview',
    match: ['node_modules/reka-ui/', 'lib/shared/components/Tree'],
  },
] as const

const CORE_FEATURE_FACADE_RE = /\/lib\/core\/features\/([^/]+)\/index\.ts$/
const LOCALE_FACADE_PATH = '/lib/shared/i18n/locales/'

const getCoreFeatureChunkName = (normalizedFacade: string): string | null => {
  const featureMatch = normalizedFacade.match(CORE_FEATURE_FACADE_RE)
  if (!featureMatch?.[1]) {
    return null
  }
  return `core-feature-${featureMatch[1]}-[hash].js`
}

const getLocaleChunkName = (facade: string): string | null => {
  if (!facade.includes(LOCALE_FACADE_PATH)) {
    return null
  }
  const locale = basename(facade).replace('.json', '')
  return `locale-${locale}-[hash].js`
}

// Convert a chunk's source module path into our desired output filename.
// We use it to apply stable naming conventions for special cases and
// fall back to Vite's default naming for everything else.
const chunkFileNameForFacade = (facadeModuleId?: string | null): string => {
  if (!facadeModuleId) {
    return '[name]-[hash].js'
  }

  const normalizedFacade = normalizePath(facadeModuleId)
  return (
    getCoreFeatureChunkName(normalizedFacade)
    ?? getLocaleChunkName(normalizedFacade)
    ?? '[name]-[hash].js'
  )
}

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
    plugins: [vue()],
    appType: 'spa', // Single page application mode.
    test: {
      globals: true,
      environment: 'jsdom',
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, './lib'),
      },
    },
    define: {
      'process.env.NODE_ENV': isProduction ? '"production"' : '"development"',
      '__VUE_OPTIONS_API__': false,
      '__VUE_PROD_DEVTOOLS__': false,
      '__VUE_PROD_HYDRATION_MISMATCH_DETAILS__': true,
    },
    build: {
      manifest: 'manifest.json',
      sourcemap: !isProduction,
      minify: isProduction,
      lib: {
        name: 'Archivematica',
        entry: {
          'core': resolve(__dirname, 'lib/core/index.ts'),
          'transfer-browser': resolve(__dirname, 'lib/transfer-browser/index.ts'),
          'aip-browser': resolve(__dirname, 'lib/aip-browser/index.ts'),
          'as-matcher': resolve(__dirname, 'lib/as-matcher/index.ts'),
          'archival-storage': resolve(__dirname, 'lib/archival-storage/index.ts'),
          'md-editor': resolve(__dirname, 'lib/md-editor/index.ts'),
          'topbar': resolve(__dirname, 'lib/topbar/index.ts'),
          'monitor': resolve(__dirname, 'lib/monitor/index.ts'),
          'fpr-tables': resolve(__dirname, 'lib/fpr-tables/index.ts'),
        },
        formats: ['es'],
      },
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            const normalized = normalizePath(id)
            for (const route of CHUNK_ROUTES) {
              if (route.match.some(pattern => normalized.includes(pattern))) {
                return route.name
              }
            }
            return undefined
          },
          chunkFileNames: (chunkInfo) => {
            return chunkFileNameForFacade(chunkInfo.facadeModuleId)
          },
        },
      },
    },
  }
})

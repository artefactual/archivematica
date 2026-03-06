import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'

async function bootstrap() {
  const mountEl = document.getElementById('archival-storage-app')
  if (!mountEl) {
    throw new Error('Mount element not found.')
  }

  await initI18n()

  const filesIndexedRaw = mountEl.getAttribute('data-files-indexed-count') ?? ''
  const filesIndexedCount = filesIndexedRaw ? Number.parseInt(filesIndexedRaw, 10) : 0
  const app = createApp(App, {
    totalSize: mountEl.getAttribute('data-total-size') ?? '',
    filesIndexedCount: Number.isNaN(filesIndexedCount) ? 0 : filesIndexedCount,
  })
  app.use(i18n)
  app.mount(mountEl)
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap app:', err)
})

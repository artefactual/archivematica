import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'

async function bootstrap() {
  const mountEl = document.getElementById('aip-browser')
  if (!mountEl) {
    throw new Error('Mount element not found.')
  }
  await initI18n()
  const directory = mountEl.getAttribute('data-directory') || ''
  const app = createApp(App, { directory })
  app.use(i18n)
  app.mount(mountEl)
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap app:', err)
})

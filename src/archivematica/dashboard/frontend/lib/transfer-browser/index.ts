import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'

async function bootstrap() {
  await initI18n()
  const app = createApp(App)
  app.use(i18n)
  app.mount('#transfer-browser')
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap app:', err)
})

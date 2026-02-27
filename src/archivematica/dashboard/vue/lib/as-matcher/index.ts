import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'
import type { MatcherBootstrapData } from './types'

const normalizeMatcherData = (raw: MatcherBootstrapData): MatcherBootstrapData => {
  return {
    ...raw,
    resetAvailable: Boolean(raw.resetAvailable),
  }
}

const getMatcherData = (): MatcherBootstrapData => {
  const el = document.getElementById('as-matcher-data')
  if (!(el instanceof HTMLScriptElement)) {
    throw new Error('#as-matcher-data not found or not a <script> tag.')
  }

  const raw = el.textContent?.trim()
  if (!raw) {
    throw new Error('#as-matcher-data is empty.')
  }

  try {
    return Object.freeze(normalizeMatcherData(JSON.parse(raw) as MatcherBootstrapData))
  } catch {
    throw new Error('Invalid JSON in #as-matcher-data.')
  }
}

async function bootstrap() {
  await initI18n()
  const matcherData = getMatcherData()
  const app = createApp(App, matcherData)
  app.use(i18n)
  app.mount('#as_matcher')
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap ArchivesSpace matcher:', err)
})

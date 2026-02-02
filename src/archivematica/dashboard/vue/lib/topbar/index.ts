import { createApp } from 'vue'
import TopbarApp from '@/topbar/TopbarApp.vue'
import { i18n, initI18n } from '@/shared/i18n'

const ROOT_ID = 'archivematica-topbar-vue'

const ensureRoot = (): HTMLElement => {
  let root = document.getElementById(ROOT_ID)
  if (root) return root
  root = document.createElement('div')
  root.id = ROOT_ID
  document.body.appendChild(root)
  return root
}

function domReady(): Promise<void> {
  if (document.readyState !== 'loading') {
    return Promise.resolve()
  }
  return new Promise((resolve) => {
    document.addEventListener('DOMContentLoaded', () => resolve(), { once: true })
  })
}

async function bootstrap() {
  await domReady()
  await initI18n()
  const root = ensureRoot()
  if (root.dataset.mounted) return
  createApp(TopbarApp).use(i18n).mount(root)
  root.dataset.mounted = 'true'
}

bootstrap().catch(console.error)

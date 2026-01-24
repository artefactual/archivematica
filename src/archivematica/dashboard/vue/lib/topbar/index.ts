import { createApp } from 'vue'
import TopbarApp from '@/topbar/TopbarApp.vue'
import { i18n } from '@/shared/i18n'

const ROOT_ID = 'archivematica-topbar-vue'

const ensureRoot = (): HTMLElement => {
  let root = document.getElementById(ROOT_ID)
  if (root) return root

  root = document.createElement('div')
  root.id = ROOT_ID
  document.body.appendChild(root)
  return root
}

const mountTopbarApp = () => {
  const root = ensureRoot()
  const app = createApp(TopbarApp)
  app.use(i18n)
  app.mount(root)
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountTopbarApp, { once: true })
} else {
  mountTopbarApp()
}

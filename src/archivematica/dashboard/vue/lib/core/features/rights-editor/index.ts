import { initI18n } from '@/shared/i18n'
import { initGrantsPage } from './grants-page'
import { initMainPage } from './main-page'

const PAGE_IDS = {
  main: 'page-rights-editor-main',
  grants: 'page-rights-editor-grants',
} as const

export async function init(): Promise<void> {
  await initI18n()

  const pageId = document.body.id

  if (pageId === PAGE_IDS.main) {
    await initMainPage()
    return
  }

  if (pageId === PAGE_IDS.grants) {
    await initGrantsPage()
  }
}

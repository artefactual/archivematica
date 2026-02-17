import { applyDateInputMask } from './inputmask'

const PAGE_IDS = {
  main: 'page-rights-editor-main',
  grants: 'page-rights-editor-grants',
} as const

function initMainPage(): void {
  applyDateInputMask()
}

function initGrantsPage(): void {
  applyDateInputMask()
}

export function init(): void {
  const pageId = document.body.id

  if (pageId === PAGE_IDS.main) {
    initMainPage()
    return
  }

  if (pageId === PAGE_IDS.grants) {
    initGrantsPage()
  }
}

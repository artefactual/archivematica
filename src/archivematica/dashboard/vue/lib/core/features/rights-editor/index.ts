import $ from 'jquery'

const PAGE_IDS = {
  main: 'page-rights-editor-main',
  grants: 'page-rights-editor-grants',
} as const

function initMainPage(): void {
  window.alert('rights-editor main init')
}

function initGrantsPage(): void {
  window.alert('rights-editor grants init')
}

export function init(): void {
  const pageId = $('body').attr('id') ?? ''

  if (pageId === PAGE_IDS.main) {
    initMainPage()
    return
  }

  if (pageId === PAGE_IDS.grants) {
    initGrantsPage()
  }
}

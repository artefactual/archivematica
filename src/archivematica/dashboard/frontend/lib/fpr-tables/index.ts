import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'

type FprTableRoot = HTMLElement & {
  dataset: DOMStringMap & {
    fprTableScriptId?: string
  }
}

type FormTogglePair = {
  formId: string
  selectId: string
}

const parsePayload = (scriptId: string): unknown => {
  const script = document.getElementById(scriptId)
  if (!script?.textContent) {
    throw new Error(`FPR table payload script not found: ${scriptId}`)
  }
  return JSON.parse(script.textContent)
}

const mountFprTables = () => {
  const roots = document.querySelectorAll<HTMLElement>('[data-fpr-table-root]')
  roots.forEach((rootEl) => {
    const root = rootEl as FprTableRoot
    const scriptId = root.dataset.fprTableScriptId
    if (!scriptId) {
      console.error('Missing data-fpr-table-script-id on FPR table root', root)
      return
    }
    try {
      const payload = parsePayload(scriptId)
      createApp(App, { payload }).use(i18n).mount(root)
    } catch (error) {
      console.error('Failed to mount FPR table', error)
    }
  })
}

const toggleExtraForm = (selectEl: HTMLSelectElement, formEl: HTMLElement): void => {
  if (selectEl.value === 'new') {
    formEl.style.display = ''
    if (window.getComputedStyle(formEl).display === 'none') {
      formEl.style.display = 'block'
    }
    return
  }

  formEl.style.display = 'none'
}

const initFprFormToggle = (): void => {
  const toggles: FormTogglePair[] = [
    {
      formId: 'fprule_command_form',
      selectId: 'id_f-command',
    },
    {
      formId: 'format_group_form',
      selectId: 'id_f-group',
    },
  ]

  toggles.forEach(({ formId, selectId }) => {
    const selectEl = document.getElementById(selectId)
    const formEl = document.getElementById(formId)
    if (!(selectEl instanceof HTMLSelectElement) || !(formEl instanceof HTMLElement)) {
      return
    }

    selectEl.addEventListener('change', () => {
      toggleExtraForm(selectEl, formEl)
    })

    toggleExtraForm(selectEl, formEl)
  })
}

async function bootstrap() {
  await initI18n()
  mountFprTables()
  initFprFormToggle()
}

bootstrap().catch((error) => {
  console.error('Failed to bootstrap FPR tables', error)
})

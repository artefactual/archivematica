import { applyTemplateDateMask } from '@/core/features/datemask'
import { translate } from '@/shared/i18n/plain'
import { RIGHTS_EDITOR_FORMDATA_TYPES } from '@/shared/http'
import { initRepeaters } from './repeater'
import type { RepeaterConfig } from './repeater'
import { applyGrantsPageTitleAttributes } from './tooltips'

const GRANTS_PAGE_REPEATERS: RepeaterConfig[] = [
  {
    idPrefix: 'rightsrestrictions_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.rightsRestriction,
    fields: [
      {
        name: 'restriction',
        type: 'select',
        options: [
          { value: '', label: '' },
          { value: 'Allow', labelKey: 'rights.allow' },
          { value: 'Disallow', labelKey: 'rights.disallow' },
          { value: 'Conditional', labelKey: 'rights.conditional' },
        ],
      },
    ],
  },
  {
    idPrefix: 'rightsfields_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.rightsNote,
    fields: [
      {
        name: 'rightsgrantednote',
        type: 'textarea',
      },
    ],
  },
]
const DATE_INPUT_SELECTOR = 'input[type="text"][name*="date"]'

const appendRevealButton = (elements: HTMLElement[], dataType: string): void => {
  if (elements.length <= 1) {
    return
  }

  const last = elements[elements.length - 1]
  if (!last) {
    return
  }
  last.style.display = 'none'

  const message = translate('rights.createNewRecordPrompt', { recordType: dataType })
  const toggleButton = document.createElement('h3')
  toggleButton.className = 'btn btn-default'
  toggleButton.style.float = 'right'
  toggleButton.textContent = message

  toggleButton.addEventListener('click', () => {
    toggleButton.style.display = 'none'
    last.style.removeProperty('display')
  })

  const previous = last.previousElementSibling
  if (!previous) {
    return
  }

  previous.append(toggleButton)
  const clearBreak = document.createElement('br')
  clearBreak.setAttribute('clear', 'all')
  previous.append(clearBreak)
}

const applyGrantFieldsetStyling = (): void => {
  const grantFieldsets = document.querySelectorAll<HTMLElement>('.grant-fieldset')
  grantFieldsets.forEach((fieldset, index) => {
    if (index > 0) {
      fieldset.style.marginTop = '4em'
    }
  })
}

const repositionRestrictionField = (): void => {
  document.querySelectorAll<HTMLElement>('.rights-grant-restrictions').forEach((restriction) => {
    const parent = restriction.parentElement
    if (!parent) {
      return
    }

    const target = parent.children.item(2)
    if (target) {
      target.insertAdjacentElement('afterend', restriction)
    }
  })
}

export const initGrantsLayoutBehavior = (): void => {
  appendRevealButton(
    Array.from(document.querySelectorAll<HTMLElement>('.grant-fieldset')),
    translate('rights.grantRestriction').toLowerCase(),
  )
  applyGrantFieldsetStyling()
  repositionRestrictionField()
}

export const initGrantsPage = async (): Promise<void> => {
  applyTemplateDateMask(DATE_INPUT_SELECTOR)
  initGrantsLayoutBehavior()
  applyGrantsPageTitleAttributes()
  await initRepeaters(GRANTS_PAGE_REPEATERS)
  applyGrantsPageTitleAttributes()
}

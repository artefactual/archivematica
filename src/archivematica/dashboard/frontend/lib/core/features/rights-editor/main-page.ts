import { applyTemplateDateMask } from '@/core/features/datemask'
import { translate } from '@/shared/i18n/plain'
import { RIGHTS_EDITOR_FORMDATA_TYPES } from '@/shared/http'
import { initRepeaters } from './repeater'
import type { RepeaterConfig } from './repeater'
import { applyMainPageTitleAttributes } from './tooltips'

const MAIN_PAGE_REPEATERS: RepeaterConfig[] = [
  {
    idPrefix: 'copyrightdocidfields_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.copyrightDocumentationIdentifier,
    fields: [
      {
        name: 'copyrightdocumentationidentifiertype',
        type: 'input',
        labelKey: 'rights.type',
      },
      {
        name: 'copyrightdocumentationidentifiervalue',
        type: 'input',
        labelKey: 'rights.value',
      },
      {
        name: 'copyrightdocumentationidentifierrole',
        type: 'input',
        labelKey: 'rights.role',
      },
    ],
  },
  {
    idPrefix: 'copyrightnotes_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.copyrightNote,
    fields: [
      {
        name: 'copyrightnote',
        type: 'textarea',
      },
    ],
  },
  {
    idPrefix: 'statutedocidfields_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.statuteDocumentationIdentifier,
    fields: [
      {
        name: 'statutedocumentationidentifiertype',
        type: 'input',
        labelKey: 'rights.type',
      },
      {
        name: 'statutedocumentationidentifiervalue',
        type: 'input',
        labelKey: 'rights.value',
      },
      {
        name: 'statutedocumentationidentifierrole',
        type: 'input',
        labelKey: 'rights.role',
      },
    ],
  },
  {
    idPrefix: 'statutenotes_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.statuteNote,
    fields: [
      {
        name: 'statutenote',
        type: 'textarea',
      },
    ],
  },
  {
    idPrefix: 'licensedocidfields_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.licenseDocumentationIdentifier,
    fields: [
      {
        name: 'licensedocumentationidentifiertype',
        type: 'input',
        labelKey: 'rights.type',
      },
      {
        name: 'licensedocumentationidentifiervalue',
        type: 'input',
        labelKey: 'rights.value',
      },
      {
        name: 'licensedocumentationidentifierrole',
        type: 'input',
        labelKey: 'rights.role',
      },
    ],
  },
  {
    idPrefix: 'licensenotes_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.licenseNote,
    fields: [
      {
        name: 'licensenote',
        type: 'textarea',
      },
    ],
  },
  {
    idPrefix: 'otherrightsdocidfields_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.otherRightsDocumentationIdentifier,
    fields: [
      {
        name: 'otherrightsdocumentationidentifiertype',
        type: 'input',
        labelKey: 'rights.type',
      },
      {
        name: 'otherrightsdocumentationidentifiervalue',
        type: 'input',
        labelKey: 'rights.value',
      },
      {
        name: 'otherrightsdocumentationidentifierrole',
        type: 'input',
        labelKey: 'rights.role',
      },
    ],
  },
  {
    idPrefix: 'otherrightsnotes_',
    formdataType: RIGHTS_EDITOR_FORMDATA_TYPES.otherRightsNote,
    fields: [
      {
        name: 'otherrightsnote',
        type: 'textarea',
      },
    ],
  },
]

const FORMSETS_BY_BASIS: Record<string, string> = {
  Copyright: 'copyright_formset',
  Statute: 'statute_formset',
  License: 'license_formset',
  Policy: 'other_formset',
  Donor: 'other_formset',
  Other: 'other_formset',
}

const OTHER_BASIS_FIELD = '#id_rightsstatementotherrightsinformation_set-0-otherrightsbasis'
const OTHER_DOC_ID_LABEL = '#other_documentation_identifier_label'
const OTHER_NOTE_LABEL = '#other_rights_notes_label'
const OTHER_START_DATE_LABEL
  = 'label[for=\'id_rightsstatementotherrightsinformation_set-0-otherrightsapplicablestartdate\']'
const OTHER_END_DATE_LABEL
  = 'label[for=\'id_rightsstatementotherrightsinformation_set-0-otherrightsapplicableenddate\']'
const DATE_INPUT_SELECTOR = 'input[type="text"][name*="date"]'

const revealSelectedBasis = (): void => {
  const basisField = document.querySelector<HTMLSelectElement>('#id_rightsbasis')
  if (!basisField) {
    return
  }

  const selectedBasis = basisField.value
  Object.entries(FORMSETS_BY_BASIS).forEach(([basis, formsetId]) => {
    const formset = document.getElementById(formsetId)
    if (basis !== selectedBasis) {
      formset?.style.setProperty('display', 'none')
    }
  })

  const selectedFormsetId = FORMSETS_BY_BASIS[selectedBasis]
  if (selectedFormsetId) {
    document.getElementById(selectedFormsetId)?.style.removeProperty('display')
  }

  const isDonorOrPolicy = selectedBasis === 'Donor' || selectedBasis === 'Policy'
  const otherBasisContainer = document
    .querySelector<HTMLElement>(OTHER_BASIS_FIELD)
    ?.parentElement
    ?.parentElement
  if (isDonorOrPolicy) {
    otherBasisContainer?.style.setProperty('display', 'none')
  } else {
    otherBasisContainer?.style.removeProperty('display')
    const otherNoteLabel = document.querySelector<HTMLElement>(OTHER_NOTE_LABEL)
    if (otherNoteLabel) {
      otherNoteLabel.textContent = translate('rights.note')
    }
  }

  const otherDocLabel = document.querySelector<HTMLElement>(OTHER_DOC_ID_LABEL)
  if (otherDocLabel) {
    otherDocLabel.textContent = translate('rights.documentationIdentifierForBasis', {
      basis: selectedBasis,
    })
  }

  const noteBasis = selectedBasis === 'Donor' ? translate('rights.donorAgreement') : selectedBasis
  const otherNoteLabel = document.querySelector<HTMLElement>(OTHER_NOTE_LABEL)
  if (selectedBasis === 'Donor' || selectedBasis === 'Policy') {
    if (otherNoteLabel) {
      otherNoteLabel.textContent = translate('rights.noteForBasis', { basis: noteBasis })
    }
  } else {
    if (otherNoteLabel) {
      otherNoteLabel.textContent = translate('rights.note')
    }
  }

  const dateBasis = selectedBasis === 'Donor' ? translate('rights.donorAgreement') : selectedBasis
  const startDateLabel = document.querySelector<HTMLElement>(OTHER_START_DATE_LABEL)
  if (startDateLabel) {
    startDateLabel.textContent = translate('rights.startDateForBasis', { basis: dateBasis })
  }

  const endDateLabel = document.querySelector<HTMLElement>(OTHER_END_DATE_LABEL)
  if (endDateLabel) {
    endDateLabel.textContent = translate('rights.endDateForBasis', { basis: dateBasis })
  }
}

export const initBasisBehavior = (): void => {
  const basisField = document.querySelector<HTMLElement>('#id_rightsbasis')
  if (!basisField) {
    return
  }

  basisField.addEventListener('change', revealSelectedBasis)
  revealSelectedBasis()
}

export const initMainPage = async (): Promise<void> => {
  applyTemplateDateMask(DATE_INPUT_SELECTOR)
  initBasisBehavior()
  applyMainPageTitleAttributes()
  await initRepeaters(MAIN_PAGE_REPEATERS)
  applyMainPageTitleAttributes()
}

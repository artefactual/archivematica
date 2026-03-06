import $ from 'jquery'
import { translate } from '@/shared/i18n/plain'
import { RIGHTS_EDITOR_FORMDATA_TYPES } from '@/shared/http'
import { applyDateInputMask } from './inputmask'
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

const appendRevealButton = ($list: ReturnType<typeof $>, dataType: string): void => {
  if ($list.length <= 1) {
    return
  }

  const $last = $list.last()
  $last.hide()

  const message = translate('rights.createNewRecordPrompt', { recordType: dataType })
  const $toggleButton = $(`<h3 class="btn btn-default" style="float:right">${message}</h3>`)

  $toggleButton.on('click', () => {
    $toggleButton.fadeOut()
    $last.slideDown()
  })

  $last.prev().append($toggleButton).append('<br clear="all"></br>')
}

const applyGrantFieldsetStyling = (): void => {
  $('.grant-fieldset:not(:first)').css('margin-top', '4em')
}

const repositionRestrictionField = (): void => {
  $('.rights-grant-restrictions').each((_: number, element: Element) => {
    const $restriction = $(element as HTMLElement)
    const target = $restriction.parent().children().first().next().next()
    if (target.length) {
      target.after($restriction)
    }
  })
}

export const initGrantsLayoutBehavior = (): void => {
  appendRevealButton($('.grant-fieldset'), translate('rights.grantRestriction').toLowerCase())
  applyGrantFieldsetStyling()
  repositionRestrictionField()
}

export const initGrantsPage = async (): Promise<void> => {
  applyDateInputMask()
  initGrantsLayoutBehavior()
  applyGrantsPageTitleAttributes()
  await initRepeaters(GRANTS_PAGE_REPEATERS)
  applyGrantsPageTitleAttributes()
}

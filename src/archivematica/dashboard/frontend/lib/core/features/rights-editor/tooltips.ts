import $ from 'jquery'
import { translate } from '@/shared/i18n/plain'

type TitleBinding = {
  selector: string
  titleKey: string
}

const applyBindings = (bindings: TitleBinding[]): void => {
  bindings.forEach(({ selector, titleKey }) => {
    $(selector).attr('title', translate(titleKey))
  })
}

const applyLabelTooltipByContainer = (
  containerPrefix: string,
  titleKey: string,
): void => {
  $(`[id^="${containerPrefix}"]`).each((_: number, element: Element) => {
    $(element).closest('.repeating-ajax-data-fieldset').children('label').attr('title', translate(titleKey))
  })
}

export const applyMainPageTitleAttributes = (): void => {
  applyLabelTooltipByContainer(
    'copyrightdocidfields_',
    'rights.tooltipCopyrightDocumentationIdentifier',
  )
  applyLabelTooltipByContainer(
    'licensedocidfields_',
    'rights.tooltipDocumentationIdentifierRole',
  )

  applyBindings([
    {
      selector: '[name=copyrightdocumentationidentifiertype],[name=copyright_documentation_identifier_type]',
      titleKey: 'rights.tooltipDocumentationIdentifierType',
    },
    {
      selector: '[name=copyrightdocumentationidentifiervalue],[name=copyright_documentation_identifier_value]',
      titleKey: 'rights.tooltipDocumentationIdentifierValue',
    },
    {
      selector: '[name=copyrightdocumentationidentifierrole],[name=copyright_documentation_identifier_role]',
      titleKey: 'rights.tooltipDocumentationIdentifierRole',
    },
    {
      selector: '[name=copyright_note],[name=copyrightnote]',
      titleKey: 'rights.tooltipCopyrightNote',
    },
    {
      selector: '[name=statutedocumentationidentifiertype],[name^=statute_documentation_identifier_type_]',
      titleKey: 'rights.tooltipDocumentationIdentifierType',
    },
    {
      selector: '[name=statutedocumentationidentifiervalue],[name^=statute_documentation_identifier_value_]',
      titleKey: 'rights.tooltipDocumentationIdentifierValue',
    },
    {
      selector: '[name=statutedocumentationidentifierrole],[name^=statute_documentation_identifier_role_]',
      titleKey: 'rights.tooltipDocumentationIdentifierRole',
    },
    {
      selector: '[name=statutenote],[name^=new_statute_note_]',
      titleKey: 'rights.tooltipStatuteNote',
    },
    {
      selector: '[name=licensedocumentationidentifiertype],[name=license_documentation_identifier_type]',
      titleKey: 'rights.tooltipDocumentationIdentifierType',
    },
    {
      selector: '[name=licensedocumentationidentifiervalue],[name=license_documentation_identifier_value]',
      titleKey: 'rights.tooltipDocumentationIdentifierValue',
    },
    {
      selector: '[name=licensedocumentationidentifierrole],[name=license_documentation_identifier_role]',
      titleKey: 'rights.tooltipDocumentationIdentifierRole',
    },
    {
      selector: '[name=license_note],[name=licensenote]',
      titleKey: 'rights.tooltipLicenseNote',
    },
    {
      selector:
        '[name=otherrightsdocumentationidentifiertype],[name=other_documentation_identifier_type]',
      titleKey: 'rights.tooltipDocumentationIdentifierType',
    },
    {
      selector:
        '[name=otherrightsdocumentationidentifiervalue],[name=other_documentation_identifier_value]',
      titleKey: 'rights.tooltipDocumentationIdentifierValue',
    },
    {
      selector:
        '[name=otherrightsdocumentationidentifierrole],[name=other_documentation_identifier_role]',
      titleKey: 'rights.tooltipDocumentationIdentifierRole',
    },
  ])
}

export const applyGrantsPageTitleAttributes = (): void => {
  applyBindings([
    {
      selector: '[name=restriction],[name^=new_rights_restriction_]',
      titleKey: 'rights.tooltipRestriction',
    },
    {
      selector: '[name=rightsgrantednote],[name^=new_rights_note_]',
      titleKey: 'rights.tooltipRightsGrantedNote',
    },
  ])

  const openEndDateTooltip = translate('rights.tooltipOpenEndDate')
  $('input.js-rights-open-end-date')
    .attr('title', openEndDateTooltip)
    .closest('label')
    .attr('title', openEndDateTooltip)
    .find('span')
    .attr('title', openEndDateTooltip)
}

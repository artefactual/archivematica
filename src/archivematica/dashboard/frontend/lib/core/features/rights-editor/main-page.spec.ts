import { beforeEach, describe, expect, it, vi } from 'vitest'
import { initBasisBehavior, initMainPage } from './main-page'

const { listRightsFormdataMock, saveRightsFormdataMock, applyTemplateDateMaskMock } = vi.hoisted(
  () => ({
    listRightsFormdataMock: vi.fn(),
    saveRightsFormdataMock: vi.fn(),
    applyTemplateDateMaskMock: vi.fn(),
  }),
)

vi.mock('@/shared/http', () => ({
  RIGHTS_EDITOR_FORMDATA_TYPES: {
    copyrightDocumentationIdentifier: 'copyrightdocumentationidentifier',
    copyrightNote: 'copyrightnote',
    statuteDocumentationIdentifier: 'statutedocumentationidentifier',
    statuteNote: 'statutenote',
    licenseDocumentationIdentifier: 'licensedocumentationidentifier',
    licenseNote: 'licensenote',
    otherRightsDocumentationIdentifier: 'otherrightsdocumentationidentifier',
    otherRightsNote: 'otherrightsnote',
    rightsRestriction: 'rightsrestriction',
    rightsNote: 'rightsnote',
  },
  listRightsFormdata: listRightsFormdataMock,
  saveRightsFormdata: saveRightsFormdataMock,
}))

vi.mock('@/core/features/datemask', () => ({
  applyTemplateDateMask: applyTemplateDateMaskMock,
}))

vi.mock('@/shared/i18n/plain', () => ({
  translate: (key: string, params?: Record<string, string>) => {
    const basis = params?.basis ?? ''
    const messages: Record<string, string> = {
      'rights.type': 'Type',
      'rights.value': 'Value',
      'rights.role': 'Role',
      'rights.note': 'Note',
      'rights.donorAgreement': 'Donor agreement',
      'rights.documentationIdentifierForBasis': `${basis} documentation identifier`,
      'rights.noteForBasis': `${basis} note`,
      'rights.startDateForBasis': `${basis} start date`,
      'rights.endDateForBasis': `${basis} end date`,
      'rights.tooltipCopyrightDocumentationIdentifier':
        'Designation used to uniquely identify documentation supporting copyright rights granted.',
      'rights.tooltipDocumentationIdentifierType':
        'A designation of the domain within which the documentation identifier is unique.',
      'rights.tooltipDocumentationIdentifierValue': 'The value of the documentation identifier.',
      'rights.tooltipDocumentationIdentifierRole':
        'A value indicating the purpose or expected use of the documentation being identified.',
      'rights.tooltipCopyrightNote': 'Additional information about the copyright status of the object.',
      'rights.tooltipStatuteNote': 'Additional information about the statute.',
      'rights.tooltipLicenseNote': 'Additional information about the license.',
    }
    return messages[key] ?? key
  },
}))

const MAIN_PAGE_TYPES = [
  'copyrightdocumentationidentifier',
  'copyrightnote',
  'statutedocumentationidentifier',
  'statutenote',
  'licensedocumentationidentifier',
  'licensenote',
  'otherrightsdocumentationidentifier',
  'otherrightsnote',
]

describe('rights-editor main page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = `
      <div class="repeating-ajax-data-fieldset">
        <label>Copyright documentation identifier:</label>
        <div id="copyrightdocidfields_10" class="repeating-data repeating-data-multifield"></div>
        <div class="repeating-ajax-data-row repeating-data-multifield">
          <input name="copyright_documentation_identifier_type" class="form-control" />
          <input name="copyright_documentation_identifier_value" class="form-control" />
          <input name="copyright_documentation_identifier_role" class="form-control" />
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <div id="copyrightnotes_10" class="repeating-data"></div>
        <div class="repeating-ajax-data-row">
          <textarea name="copyright_note" class="form-control"></textarea>
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <div id="statutedocidfields_10" class="repeating-data repeating-data-multifield"></div>
        <div class="repeating-ajax-data-row repeating-data-multifield">
          <input name="statute_documentation_identifier_type_10" class="form-control" />
          <input name="statute_documentation_identifier_value_10" class="form-control" />
          <input name="statute_documentation_identifier_role_10" class="form-control" />
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <div id="statutenotes_10" class="repeating-data"></div>
        <div class="repeating-ajax-data-row">
          <textarea name="new_statute_note_10" class="form-control"></textarea>
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <label>License documentation identifier:</label>
        <div id="licensedocidfields_10" class="repeating-data repeating-data-multifield"></div>
        <div class="repeating-ajax-data-row repeating-data-multifield">
          <input name="license_documentation_identifier_type" class="form-control" />
          <input name="license_documentation_identifier_value" class="form-control" />
          <input name="license_documentation_identifier_role" class="form-control" />
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <div id="licensenotes_10" class="repeating-data"></div>
        <div class="repeating-ajax-data-row">
          <textarea name="license_note" class="form-control"></textarea>
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <div id="otherrightsdocidfields_10" class="repeating-data repeating-data-multifield"></div>
        <div class="repeating-ajax-data-row repeating-data-multifield">
          <input name="other_documentation_identifier_type" class="form-control" />
          <input name="other_documentation_identifier_value" class="form-control" />
          <input name="other_documentation_identifier_role" class="form-control" />
        </div>
      </div>
      <div class="repeating-ajax-data-fieldset">
        <div id="otherrightsnotes_10" class="repeating-data"></div>
        <div class="repeating-ajax-data-row">
          <textarea name="otherrights_note" class="form-control"></textarea>
        </div>
      </div>
    `
  })

  it('loads all main repeaters and hides manual rows when existing data is present', async () => {
    listRightsFormdataMock.mockImplementation(async (type: string) => {
      const payloads: Record<string, unknown> = {
        copyrightdocumentationidentifier: {
          results: [
            {
              id: 7,
              values: {
                copyrightdocumentationidentifiertype: 'UUID',
                copyrightdocumentationidentifiervalue: 'abc',
                copyrightdocumentationidentifierrole: 'primary',
              },
            },
          ],
        },
        copyrightnote: {
          results: [{ id: 8, values: { copyrightnote: 'Saved note' } }],
        },
        statutedocumentationidentifier: {
          results: [
            {
              id: 9,
              values: {
                statutedocumentationidentifiertype: 'Act',
                statutedocumentationidentifiervalue: 'X-1',
                statutedocumentationidentifierrole: 'reference',
              },
            },
          ],
        },
        statutenote: {
          results: [{ id: 10, values: { statutenote: 'Saved statute note' } }],
        },
        licensedocumentationidentifier: {
          results: [
            {
              id: 11,
              values: {
                licensedocumentationidentifiertype: 'Agreement',
                licensedocumentationidentifiervalue: 'L-42',
                licensedocumentationidentifierrole: 'primary',
              },
            },
          ],
        },
        licensenote: {
          results: [{ id: 12, values: { licensenote: 'Saved license note' } }],
        },
        otherrightsdocumentationidentifier: {
          results: [
            {
              id: 13,
              values: {
                otherrightsdocumentationidentifiertype: 'Memo',
                otherrightsdocumentationidentifiervalue: 'O-2',
                otherrightsdocumentationidentifierrole: 'reference',
              },
            },
          ],
        },
        otherrightsnote: {
          results: [{ id: 14, values: { otherrightsnote: 'Saved other note' } }],
        },
      }
      return payloads[type] ?? { results: [] }
    })

    await initMainPage()

    expect(applyTemplateDateMaskMock).toHaveBeenCalledTimes(1)
    MAIN_PAGE_TYPES.forEach((type) => {
      expect(listRightsFormdataMock).toHaveBeenCalledWith(type, '10')
    })

    const noteValue = (
      document.querySelector('#statutenotes_10 textarea[name="statutenote"]') as HTMLTextAreaElement
    )?.value
    expect(noteValue).toBe('Saved statute note')

    const manualRows = Array.from(
      document.querySelectorAll('.repeating-ajax-data-fieldset > .repeating-ajax-data-row'),
    ) as HTMLElement[]
    expect(manualRows.every(row => row.style.display === 'none')).toBe(true)
  })

  it('posts updates when a rendered repeater field changes', async () => {
    listRightsFormdataMock.mockImplementation(async (type: string) => {
      if (type === 'copyrightdocumentationidentifier') {
        return {
          results: [
            {
              id: 7,
              values: {
                copyrightdocumentationidentifiertype: 'UUID',
                copyrightdocumentationidentifiervalue: 'abc',
                copyrightdocumentationidentifierrole: 'primary',
              },
            },
          ],
        }
      }

      return { results: [] }
    })

    await initMainPage()

    const input = document.querySelector(
      '#copyrightdocidfields_10 input[name="copyrightdocumentationidentifiervalue"]',
    ) as HTMLInputElement
    input.value = 'updated'
    input.dispatchEvent(new Event('change', { bubbles: true }))
    await Promise.resolve()
    await Promise.resolve()

    expect(saveRightsFormdataMock).toHaveBeenCalledWith(
      'copyrightdocumentationidentifier',
      '10',
      {
        copyrightdocumentationidentifiertype: 'UUID',
        copyrightdocumentationidentifiervalue: 'updated',
        copyrightdocumentationidentifierrole: 'primary',
      },
      7,
    )
  })

  it('applies native title attributes to manual and rendered fields', async () => {
    listRightsFormdataMock.mockImplementation(async (type: string) => {
      if (type === 'copyrightdocumentationidentifier') {
        return {
          results: [
            {
              id: 7,
              values: {
                copyrightdocumentationidentifiertype: 'UUID',
                copyrightdocumentationidentifiervalue: 'abc',
                copyrightdocumentationidentifierrole: 'primary',
              },
            },
          ],
        }
      }
      return { results: [] }
    })

    await initMainPage()

    expect(
      (
        document.querySelector('#copyrightdocidfields_10')
          ?.closest('.repeating-ajax-data-fieldset')
          ?.querySelector('label') as HTMLElement
      ).title,
    ).toBe('Designation used to uniquely identify documentation supporting copyright rights granted.')

    expect(
      (
        document.querySelector(
          '#copyrightdocidfields_10 input[name="copyrightdocumentationidentifiertype"]',
        ) as HTMLInputElement
      ).title,
    ).toBe('A designation of the domain within which the documentation identifier is unique.')

    expect((document.querySelector('[name="license_note"]') as HTMLTextAreaElement).title).toBe(
      'Additional information about the license.',
    )
  })
})

describe('rights-editor basis behavior', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <select id="id_rightsbasis">
        <option value="">Choose</option>
        <option value="Copyright">Copyright</option>
        <option value="Donor">Donor</option>
        <option value="Policy">Policy</option>
      </select>

      <div id="copyright_formset"></div>
      <div id="statute_formset"></div>
      <div id="license_formset"></div>
      <div id="other_formset"></div>

      <div>
        <div>
          <input id="id_rightsstatementotherrightsinformation_set-0-otherrightsbasis" />
        </div>
      </div>

      <label id="other_documentation_identifier_label">Documentation identifier</label>
      <label id="other_rights_notes_label">Note</label>
      <label for="id_rightsstatementotherrightsinformation_set-0-otherrightsapplicablestartdate">Start</label>
      <label for="id_rightsstatementotherrightsinformation_set-0-otherrightsapplicableenddate">End</label>
    `
  })

  it('shows selected basis formset and updates labels', () => {
    const basis = document.getElementById('id_rightsbasis') as HTMLSelectElement
    basis.value = 'Copyright'

    initBasisBehavior()

    expect((document.getElementById('copyright_formset') as HTMLElement).style.display).toBe('')
    expect((document.getElementById('other_formset') as HTMLElement).style.display).toBe('none')
    expect((document.getElementById('other_documentation_identifier_label') as HTMLElement).textContent).toBe(
      'Copyright documentation identifier',
    )
    expect((document.getElementById('other_rights_notes_label') as HTMLElement).textContent).toBe('Note')
  })

  it('handles donor basis specific relabeling and basis-field hiding', () => {
    const basis = document.getElementById('id_rightsbasis') as HTMLSelectElement
    basis.value = 'Donor'

    initBasisBehavior()

    expect((document.getElementById('other_formset') as HTMLElement).style.display).toBe('')
    expect(
      (
        document.getElementById('id_rightsstatementotherrightsinformation_set-0-otherrightsbasis')
          ?.parentElement?.parentElement as HTMLElement
      ).style.display,
    ).toBe('none')
    expect((document.getElementById('other_rights_notes_label') as HTMLElement).textContent).toBe(
      'Donor agreement note',
    )
  })

  it('hides all basis formsets when no basis is selected', () => {
    const basis = document.getElementById('id_rightsbasis') as HTMLSelectElement
    basis.value = ''

    initBasisBehavior()

    expect((document.getElementById('copyright_formset') as HTMLElement).style.display).toBe('none')
    expect((document.getElementById('statute_formset') as HTMLElement).style.display).toBe('none')
    expect((document.getElementById('license_formset') as HTMLElement).style.display).toBe('none')
    expect((document.getElementById('other_formset') as HTMLElement).style.display).toBe('none')
  })
})

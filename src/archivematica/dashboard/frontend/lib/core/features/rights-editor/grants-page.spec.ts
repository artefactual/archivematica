import { beforeEach, describe, expect, it, vi } from 'vitest'
import { initGrantsPage } from './grants-page'

const { listRightsFormdataMock, saveRightsFormdataMock, applyTemplateDateMaskMock } = vi.hoisted(
  () => ({
    listRightsFormdataMock: vi.fn(),
    saveRightsFormdataMock: vi.fn(),
    applyTemplateDateMaskMock: vi.fn(),
  }),
)

vi.mock('@/shared/i18n/plain', () => ({
  translate: (key: string, params?: Record<string, string>) => {
    const messages: Record<string, string> = {
      'rights.grantRestriction': 'Grant/restriction',
      'rights.createNewRecordPrompt': `Create new ${params?.recordType ?? ''}?`,
      'rights.allow': 'Allow',
      'rights.disallow': 'Disallow',
      'rights.conditional': 'Conditional',
      'rights.tooltipRestriction': 'A condition or limitation on the act.',
      'rights.tooltipRightsGrantedNote': 'Additional information about the rights granted.',
      'rights.tooltipOpenEndDate':
        'Use "OPEN" for an open ended term of restriction. Omit endDate if the ending date is unknown.',
    }
    return messages[key] ?? key
  },
}))

vi.mock('@/shared/http', () => ({
  RIGHTS_EDITOR_FORMDATA_TYPES: {
    copyrightDocumentationIdentifier: 'copyrightdocumentationidentifier',
    copyrightNote: 'copyrightnote',
    rightsRestriction: 'rightsrestriction',
    rightsNote: 'rightsnote',
  },
  listRightsFormdata: listRightsFormdataMock,
  saveRightsFormdata: saveRightsFormdataMock,
}))

vi.mock('@/core/features/datemask', () => ({
  applyTemplateDateMask: applyTemplateDateMaskMock,
}))

describe('rights-editor grants page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = `
      <div class='grant-fieldset' id='grant-1'>
        <div class='first'>first</div>
        <div class='second'>second</div>
        <div class='third'>third</div>
        <div class='rights-grant-restrictions repeating-ajax-data-fieldset'>
          <label>Grant/restriction</label>
          <div id="rightsrestrictions_10" class="repeating-data"></div>
          <div class="repeating-ajax-data-row">
            <select name="new_rights_restriction_10" class="form-control">
              <option value=""></option>
              <option value="Allow">Allow</option>
              <option value="Disallow">Disallow</option>
              <option value="Conditional">Conditional</option>
            </select>
          </div>
        </div>
      </div>
      <div class='grant-fieldset' id='grant-2'>
        <div class='first'>first</div>
        <div class='second'>second</div>
        <div class='third'>third</div>
        <div class='repeating-ajax-data-fieldset'>
          <label>Grant/restriction note</label>
          <label><input type="checkbox" class="js-rights-open-end-date" /><span>Open End Date</span></label>
          <div id="rightsfields_10" class="repeating-data"></div>
          <div class="repeating-ajax-data-row">
            <textarea name="new_rights_note_10" class="form-control"></textarea>
          </div>
        </div>
      </div>
    `
  })

  it('loads grants repeaters and hides manual rows when existing data is present', async () => {
    listRightsFormdataMock.mockImplementation(async (type: string) => {
      if (type === 'rightsrestriction') {
        return {
          results: [{ id: 7, values: { restriction: 'Allow' } }],
        }
      }

      return {
        results: [{ id: 8, values: { rightsgrantednote: 'Saved grant note' } }],
      }
    })

    await initGrantsPage()

    expect(applyTemplateDateMaskMock).toHaveBeenCalledTimes(1)
    expect(listRightsFormdataMock).toHaveBeenCalledWith('rightsrestriction', '10')
    expect(listRightsFormdataMock).toHaveBeenCalledWith('rightsnote', '10')

    const grant2 = document.getElementById('grant-2') as HTMLElement
    expect(grant2.style.display).toBe('none')
    expect(grant2.style.marginTop).toBe('4em')

    const revealButton = document.querySelector('#grant-1 h3.btn.btn-default') as HTMLElement
    expect(revealButton).toBeTruthy()
    expect(revealButton.textContent).toContain('Create new grant/restriction?')

    const restriction = document.querySelector('#grant-1 .rights-grant-restrictions') as HTMLElement
    const third = document.querySelector('#grant-1 .third') as HTMLElement
    expect(third.nextElementSibling).toBe(restriction)

    const select = document.querySelector(
      '#rightsrestrictions_10 select[name="restriction"]',
    ) as HTMLSelectElement
    expect(select.value).toBe('Allow')
    expect(select.title).toBe('A condition or limitation on the act.')
    expect((document.querySelector('[name="new_rights_restriction_10"]') as HTMLSelectElement).title).toBe(
      'A condition or limitation on the act.',
    )

    const noteValue = (
      document.querySelector('#rightsfields_10 textarea[name="rightsgrantednote"]') as HTMLTextAreaElement
    )?.value
    expect(noteValue).toBe('Saved grant note')
    expect((document.querySelector('[name="new_rights_note_10"]') as HTMLTextAreaElement).title).toBe(
      'Additional information about the rights granted.',
    )
    expect((document.querySelector('span') as HTMLElement).title).toBe(
      'Use "OPEN" for an open ended term of restriction. Omit endDate if the ending date is unknown.',
    )

    const manualRows = Array.from(
      document.querySelectorAll('.repeating-ajax-data-fieldset > .repeating-ajax-data-row'),
    ) as HTMLElement[]
    expect(manualRows.every(row => row.style.display === 'none')).toBe(true)
  })

  it('posts updates when a rendered grants field changes', async () => {
    listRightsFormdataMock.mockResolvedValueOnce({
      results: [{ id: 7, values: { restriction: 'Allow' } }],
    })
    listRightsFormdataMock.mockResolvedValueOnce({
      results: [],
    })

    await initGrantsPage()

    const select = document.querySelector(
      '#rightsrestrictions_10 select[name="restriction"]',
    ) as HTMLSelectElement
    select.value = 'Disallow'
    select.dispatchEvent(new Event('change', { bubbles: true }))
    await Promise.resolve()
    await Promise.resolve()

    expect(saveRightsFormdataMock).toHaveBeenCalledWith(
      'rightsrestriction',
      '10',
      { restriction: 'Disallow' },
      7,
    )
  })
})

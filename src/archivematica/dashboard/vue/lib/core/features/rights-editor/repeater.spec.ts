import { beforeEach, describe, expect, it, vi } from 'vitest'
import { initRepeaters } from './repeater'
import type { RepeaterConfig } from './repeater'

const { listRightsFormdataMock, saveRightsFormdataMock } = vi.hoisted(() => ({
  listRightsFormdataMock: vi.fn(),
  saveRightsFormdataMock: vi.fn(),
}))

vi.mock('@/shared/http', () => ({
  listRightsFormdata: listRightsFormdataMock,
  saveRightsFormdata: saveRightsFormdataMock,
}))

const repeaterConfig: RepeaterConfig = {
  idPrefix: 'copyrightdocidfields_',
  formdataType: 'copyrightdocumentationidentifier',
  fields: [
    { name: 'copyrightdocumentationidentifiertype', type: 'input', label: 'Type' },
    { name: 'copyrightdocumentationidentifiervalue', type: 'input', label: 'Value' },
    { name: 'copyrightdocumentationidentifierrole', type: 'input', label: 'Role' },
  ],
}

const flushAsync = async (): Promise<void> => {
  await Promise.resolve()
  await Promise.resolve()
  await new Promise(resolve => setTimeout(resolve, 0))
}

describe('rights-editor repeater', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = `
      <div class="repeating-ajax-data-fieldset">
        <div id="copyrightdocidfields_10" class="repeating-data repeating-data-multifield"></div>
        <div class="repeating-ajax-data-row repeating-data-multifield">
          <input name="copyright_documentation_identifier_type" class="form-control" />
        </div>
      </div>
    `
  })

  it('renders records from API and hides manual row when data exists', async () => {
    listRightsFormdataMock.mockResolvedValueOnce({
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
    })

    await initRepeaters([repeaterConfig])

    expect(listRightsFormdataMock).toHaveBeenCalledWith(
      'copyrightdocumentationidentifier',
      '10',
    )

    const input = document.querySelector(
      '#copyrightdocidfields_10 input[name="copyrightdocumentationidentifiervalue"]',
    ) as HTMLInputElement
    expect(input.value).toBe('abc')

    const manualRow = document.querySelector(
      '.repeating-ajax-data-fieldset > .repeating-ajax-data-row',
    ) as HTMLElement
    expect(manualRow.style.display).toBe('none')
  })

  it('posts updated values when a field changes', async () => {
    listRightsFormdataMock.mockResolvedValueOnce({
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
    })

    await initRepeaters([repeaterConfig])

    const input = document.querySelector(
      '#copyrightdocidfields_10 input[name="copyrightdocumentationidentifiervalue"]',
    ) as HTMLInputElement
    input.value = 'updated'
    input.dispatchEvent(new Event('change', { bubbles: true }))
    await flushAsync()

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

  it('shows a load warning and keeps manual rows visible when initial fetch fails', async () => {
    listRightsFormdataMock.mockRejectedValueOnce(new Error('load failed'))

    await initRepeaters([repeaterConfig])

    const alert = document.querySelector('.repeating-ajax-data-alert') as HTMLElement
    expect(alert).toBeTruthy()
    expect(alert.textContent).toContain('Failed to load existing records')

    const manualRow = document.querySelector(
      '.repeating-ajax-data-fieldset > .repeating-ajax-data-row',
    ) as HTMLElement
    expect(manualRow.style.display).toBe('')
  })

  it('shows save failure feedback and recovers with subtle saved status', async () => {
    listRightsFormdataMock.mockResolvedValueOnce({
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
    })
    saveRightsFormdataMock.mockRejectedValueOnce(new Error('save failed'))
    saveRightsFormdataMock.mockResolvedValueOnce({ message: 'Saved.' })

    await initRepeaters([repeaterConfig])

    const input = document.querySelector(
      '#copyrightdocidfields_10 input[name="copyrightdocumentationidentifiervalue"]',
    ) as HTMLInputElement

    input.value = 'first'
    input.dispatchEvent(new Event('change', { bubbles: true }))
    await flushAsync()

    const status = document.querySelector('.repeating-ajax-data-status') as HTMLElement
    expect(status.textContent).toContain('Could not save changes')

    input.value = 'second'
    input.dispatchEvent(new Event('change', { bubbles: true }))
    await flushAsync()

    expect(status.textContent).toContain('Saved')
    expect(saveRightsFormdataMock).toHaveBeenCalledTimes(2)
  })

  it('serializes saves per row to avoid out-of-order writes', async () => {
    listRightsFormdataMock.mockResolvedValueOnce({
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
    })

    let resolveFirstSave: (() => void) | undefined
    saveRightsFormdataMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveFirstSave = () => resolve({ message: 'Saved.' })
        }),
    )
    saveRightsFormdataMock.mockResolvedValueOnce({ message: 'Saved.' })

    await initRepeaters([repeaterConfig])

    const input = document.querySelector(
      '#copyrightdocidfields_10 input[name="copyrightdocumentationidentifiervalue"]',
    ) as HTMLInputElement

    input.value = 'first'
    input.dispatchEvent(new Event('change', { bubbles: true }))

    input.value = 'second'
    input.dispatchEvent(new Event('change', { bubbles: true }))

    await flushAsync()
    expect(saveRightsFormdataMock).toHaveBeenCalledTimes(1)

    resolveFirstSave?.()
    await flushAsync()
    await flushAsync()

    expect(saveRightsFormdataMock).toHaveBeenCalledTimes(2)
    expect(saveRightsFormdataMock).toHaveBeenNthCalledWith(
      2,
      'copyrightdocumentationidentifier',
      '10',
      {
        copyrightdocumentationidentifiertype: 'UUID',
        copyrightdocumentationidentifiervalue: 'second',
        copyrightdocumentationidentifierrole: 'primary',
      },
      7,
    )
  })
})

import { beforeEach, describe, expect, it } from 'vitest'
import { applyTemplateDateMask } from './index'

const triggerKey = (input: HTMLInputElement, key: string): void => {
  const event = new KeyboardEvent('keydown', {
    bubbles: true,
    cancelable: true,
    key,
  })
  input.dispatchEvent(event)
}

const typeValue = (input: HTMLInputElement, value: string): void => {
  for (const ch of value) {
    triggerKey(input, ch)
  }
}

describe('core datemask', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <input id="date" type="text" />
      <input id="other" type="text" />
    `
  })

  it('applies a template and accepts year/month/day typing', () => {
    applyTemplateDateMask('#date')

    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.focus()
    expect(dateInput.value).toBe('yyyy-mm-dd')

    typeValue(dateInput, '19850512')
    expect(dateInput.value).toBe('1985-05-12')
  })

  it('blocks invalid month/day combinations', () => {
    applyTemplateDateMask('#date')

    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.focus()
    typeValue(dateInput, '1980')

    triggerKey(dateInput, '3')
    expect(dateInput.value).toBe('1980-mm-dd')

    triggerKey(dateInput, '1')
    triggerKey(dateInput, '3')
    expect(dateInput.value).toBe('1980-1m-dd')

    triggerKey(dateInput, '2')
    triggerKey(dateInput, '3')
    expect(dateInput.value).toBe('1980-12-3d')

    triggerKey(dateInput, '2')
    expect(dateInput.value).toBe('1980-12-3d')
  })

  it('supports paste and clears untouched template on blur', () => {
    applyTemplateDateMask('#date')

    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.focus()

    const paste = new Event('paste', { bubbles: true, cancelable: true })
    Object.defineProperty(paste, 'clipboardData', {
      value: {
        getData: () => '1999-12-30',
      },
    })
    dateInput.dispatchEvent(paste)
    expect(dateInput.value).toBe('1999-12-30')

    dateInput.blur()
    expect(dateInput.value).toBe('1999-12-30')

    dateInput.value = ''
    dateInput.focus()
    dateInput.blur()
    expect(dateInput.value).toBe('')
  })

  it('collapses optional tail on blur like inputmask clearMaskOnLostFocus', () => {
    applyTemplateDateMask('#date')

    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.focus()
    typeValue(dateInput, '1980')
    expect(dateInput.value).toBe('1980-mm-dd')
    dateInput.blur()
    expect(dateInput.value).toBe('1980')

    dateInput.focus()
    dateInput.setSelectionRange(5, 5)
    typeValue(dateInput, '1')
    expect(dateInput.value).toBe('1980-1m-dd')
    dateInput.blur()
    expect(dateInput.value).toBe('1980-1')

    dateInput.focus()
    dateInput.setSelectionRange(6, 6)
    typeValue(dateInput, '2')
    expect(dateInput.value).toBe('1980-12-dd')
    dateInput.blur()
    expect(dateInput.value).toBe('1980-12')
  })

  it('is idempotent when binding twice', () => {
    applyTemplateDateMask('#date')
    applyTemplateDateMask('#date')

    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.focus()
    triggerKey(dateInput, '1')

    expect(dateInput.value).toBe('1yyy-mm-dd')
  })

  it('moves caret to the first position on focus for prefilled values', () => {
    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.value = '1985-05-12'

    applyTemplateDateMask('#date')
    dateInput.focus()

    expect(dateInput.selectionStart).toBe(0)
    expect(dateInput.selectionEnd).toBe(0)
  })

  it.each([
    ['2020', '2020-mm-dd'],
    ['2026-1', '2026-1m-dd'],
    ['2026-10', '2026-10-dd'],
  ])(
    'keeps prefilled partial date %s unchanged until focus',
    (storedValue, maskedValue) => {
      const dateInput = document.getElementById('date') as HTMLInputElement
      dateInput.value = storedValue

      applyTemplateDateMask('#date')
      expect(dateInput.value).toBe(storedValue)

      dateInput.focus()
      expect(dateInput.value).toBe(maskedValue)

      dateInput.blur()
      expect(dateInput.value).toBe(storedValue)
    },
  )

  it('keeps caret at first position when clicking inside the mask', () => {
    const dateInput = document.getElementById('date') as HTMLInputElement
    dateInput.value = '1985-05-12'

    applyTemplateDateMask('#date')
    dateInput.focus()
    dateInput.setSelectionRange(7, 7)
    dateInput.dispatchEvent(new MouseEvent('click', { bubbles: true }))

    expect(dateInput.selectionStart).toBe(0)
    expect(dateInput.selectionEnd).toBe(0)
  })
})

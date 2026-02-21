import { beforeEach, describe, expect, it } from 'vitest'
import { applyDateInputMask } from './inputmask'

type MaskedInput = HTMLInputElement & {
  inputmask?: {
    setValue: (value: string) => void
    getemptymask: () => string
  }
}

const setupDom = (): MaskedInput => {
  document.body.innerHTML = `
    <input type="text" name="copyrightstartdate" id="date-field" />
    <input type="text" name="title" id="non-date-field" />
  `
  return document.getElementById('date-field') as MaskedInput
}

const setMaskedValue = (input: MaskedInput, value: string): string => {
  input.inputmask?.setValue(value)
  return input.value
}

describe('rights-editor inputmask', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  it('applies mask only to date-like inputs', () => {
    const input = setupDom()
    const nonDateInput = document.getElementById('non-date-field') as MaskedInput

    applyDateInputMask()

    expect(input.inputmask).toBeDefined()
    expect(nonDateInput.inputmask).toBeUndefined()
  })

  it('uses yyyy-mm-dd placeholder contract', () => {
    const input = setupDom()

    applyDateInputMask()

    expect(input.inputmask?.getemptymask()).toBe('yyyy-mm-dd')
  })

  it('accepts year, year-month, and full date', () => {
    const input = setupDom()
    applyDateInputMask()

    expect(setMaskedValue(input, '1980')).toBe('1980-mm-dd')
    expect(setMaskedValue(input, '1980-01')).toBe('1980-01-dd')
    expect(setMaskedValue(input, '1980-01-30')).toBe('1980-01-30')
  })

  it('rejects invalid month/day patterns', () => {
    const input = setupDom()
    applyDateInputMask()

    expect(setMaskedValue(input, '1980-30')).not.toBe('1980-30')
    expect(setMaskedValue(input, '1980-13')).not.toBe('1980-13')
    expect(setMaskedValue(input, '1980-12-32')).not.toBe('1980-12-32')
  })

  it('is idempotent when applied multiple times', () => {
    const input = setupDom()
    applyDateInputMask()
    const firstMask = input.inputmask

    applyDateInputMask()

    expect(input.inputmask).toBe(firstMask)
  })
})

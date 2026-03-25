const MASK_TEMPLATE = 'yyyy-mm-dd'
const MASK_LENGTH = MASK_TEMPLATE.length
const EDITABLE_POSITIONS = [0, 1, 2, 3, 5, 6, 8, 9] as const
const YEAR_POSITIONS = [0, 1, 2, 3] as const
const MONTH_POSITIONS = [5, 6] as const
const DAY_POSITIONS = [8, 9] as const
const NAVIGATION_KEYS = new Set([
  'Tab',
  'ArrowLeft',
  'ArrowRight',
  'ArrowUp',
  'ArrowDown',
  'Home',
  'End',
  'Escape',
  'Enter',
])

const attachedInputs = new WeakSet<HTMLInputElement>()

type EditablePosition = (typeof EDITABLE_POSITIONS)[number]

const placeholderForPosition = (pos: EditablePosition): string => {
  if (pos <= 3) {
    return 'y'
  }
  if (pos <= 6) {
    return 'm'
  }
  return 'd'
}

const isEditablePosition = (pos: number): pos is EditablePosition =>
  EDITABLE_POSITIONS.includes(pos as EditablePosition)

const getSelection = (input: HTMLInputElement): [number, number] => [
  input.selectionStart ?? 0,
  input.selectionEnd ?? 0,
]

const getChars = (value: string): string[] => {
  const chars = MASK_TEMPLATE.split('')
  const source = value.slice(0, MASK_LENGTH)
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i]
    if (!ch) {
      continue
    }
    if (ch === '-' || !isEditablePosition(i)) {
      continue
    }
    chars[i] = /[0-9]/.test(ch) ? ch : placeholderForPosition(i)
  }
  return chars
}

const isDigit = (ch: string): boolean => /[0-9]/.test(ch)

const hasDigits = (chars: string[]): boolean => chars.some(ch => /[0-9]/.test(ch))

const serializeOptionalSegment = (
  chars: string[],
  positions: readonly EditablePosition[],
): string => {
  let lastDigit = -1
  positions.forEach((position, index) => {
    const ch = chars[position]
    if (ch && isDigit(ch)) {
      lastDigit = index
    }
  })

  if (lastDigit === -1) {
    return ''
  }

  return positions
    .slice(0, lastDigit + 1)
    .map(position => chars[position] ?? '')
    .join('')
}

const serializeOnBlur = (chars: string[]): string => {
  if (!hasDigits(chars)) {
    return ''
  }

  const year = YEAR_POSITIONS.map(position => chars[position] ?? '').join('')
  const month = serializeOptionalSegment(chars, MONTH_POSITIONS)
  const day = serializeOptionalSegment(chars, DAY_POSITIONS)

  if (!month) {
    return year
  }
  if (!day) {
    return `${year}-${month}`
  }
  return `${year}-${month}-${day}`
}

const findPreviousEditablePosition = (pos: number): EditablePosition | null => {
  for (let i = pos; i >= 0; i -= 1) {
    if (isEditablePosition(i)) {
      return i
    }
  }
  return null
}

const findNextEditablePosition = (pos: number): EditablePosition | null => {
  for (let i = pos; i < MASK_LENGTH; i += 1) {
    if (isEditablePosition(i)) {
      return i
    }
  }
  return null
}

const canInsertDigitAtPosition = (chars: string[], pos: EditablePosition, digit: string): boolean => {
  if (!/[0-9]/.test(digit)) {
    return false
  }

  if (pos <= 3) {
    return true
  }

  if (pos === 5) {
    return /[01]/.test(digit)
  }

  if (pos === 6) {
    if (chars[5] === '0') {
      return /[1-9]/.test(digit)
    }
    if (chars[5] === '1') {
      return /[0-2]/.test(digit)
    }
    return false
  }

  if (pos === 8) {
    return /[0-3]/.test(digit)
  }

  if (chars[8] === '0') {
    return /[1-9]/.test(digit)
  }
  if (chars[8] === '3') {
    return /[0-1]/.test(digit)
  }
  return /[0-9]/.test(digit)
}

const clearEditableRange = (chars: string[], start: number, end: number): void => {
  for (let i = start; i < end; i += 1) {
    if (!isEditablePosition(i)) {
      continue
    }
    chars[i] = placeholderForPosition(i)
  }
}

const setMaskedValue = (input: HTMLInputElement, chars: string[], caretPos: number): void => {
  input.value = chars.join('')
  input.setSelectionRange(caretPos, caretPos)
}

const firstPlaceholderOrEnd = (chars: string[]): number => {
  const next = chars.findIndex((ch, index) =>
    isEditablePosition(index) && ch === placeholderForPosition(index),
  )
  return next === -1 ? MASK_LENGTH : next
}

const insertDigits = (
  chars: string[],
  digits: string,
  selectionStart: number,
  selectionEnd: number,
): number => {
  if (selectionStart !== selectionEnd) {
    clearEditableRange(chars, selectionStart, selectionEnd)
  }

  let pos = findNextEditablePosition(selectionStart)
  let lastInserted: EditablePosition | null = null

  for (const digit of digits) {
    if (pos === null) {
      break
    }

    if (!canInsertDigitAtPosition(chars, pos, digit)) {
      break
    }

    chars[pos] = digit
    lastInserted = pos
    pos = findNextEditablePosition(pos + 1)
  }

  if (lastInserted === null) {
    return selectionStart
  }

  return findNextEditablePosition(lastInserted + 1) ?? MASK_LENGTH
}

const normalizeFromRaw = (rawValue: string): string => {
  const chars = MASK_TEMPLATE.split('')
  const digits = rawValue.replace(/\D/g, '')
  insertDigits(chars, digits, 0, 0)
  return chars.join('')
}

const onFocus = (input: HTMLInputElement): void => {
  if (!input.value) {
    input.value = MASK_TEMPLATE
    input.setSelectionRange(0, 0)
    return
  }

  const normalized = normalizeFromRaw(input.value)
  input.value = normalized
  input.setSelectionRange(0, 0)
}

const onClick = (input: HTMLInputElement): void => {
  input.setSelectionRange(0, 0)
}

const onBlur = (input: HTMLInputElement): void => {
  const chars = getChars(input.value)
  input.value = serializeOnBlur(chars)
}

const onBackspace = (input: HTMLInputElement): void => {
  if (!input.value) {
    return
  }

  const chars = getChars(input.value)
  const [start, end] = getSelection(input)

  if (start !== end) {
    clearEditableRange(chars, start, end)
    const caret = findNextEditablePosition(start) ?? start
    setMaskedValue(input, chars, caret)
    return
  }

  const previous = findPreviousEditablePosition(start - 1)
  if (previous === null) {
    return
  }

  chars[previous] = placeholderForPosition(previous)
  setMaskedValue(input, chars, previous)
}

const onDelete = (input: HTMLInputElement): void => {
  if (!input.value) {
    return
  }

  const chars = getChars(input.value)
  const [start, end] = getSelection(input)

  if (start !== end) {
    clearEditableRange(chars, start, end)
    const caret = findNextEditablePosition(start) ?? start
    setMaskedValue(input, chars, caret)
    return
  }

  const next = findNextEditablePosition(start)
  if (next === null) {
    return
  }

  chars[next] = placeholderForPosition(next)
  setMaskedValue(input, chars, next)
}

const onDigit = (input: HTMLInputElement, digit: string): void => {
  const chars = getChars(input.value || MASK_TEMPLATE)
  const [start, end] = getSelection(input)
  const caret = insertDigits(chars, digit, start, end)
  setMaskedValue(input, chars, caret)
}

const onPaste = (input: HTMLInputElement, event: ClipboardEvent): void => {
  event.preventDefault()
  const text = event.clipboardData?.getData('text') ?? ''
  const digits = text.replace(/\D/g, '')
  if (!digits) {
    return
  }

  const chars = getChars(input.value || MASK_TEMPLATE)
  const [start, end] = getSelection(input)
  const caret = insertDigits(chars, digits, start, end)
  setMaskedValue(input, chars, caret)
}

const onInput = (input: HTMLInputElement): void => {
  if (!input.value) {
    return
  }

  const normalized = normalizeFromRaw(input.value)
  if (normalized !== input.value) {
    input.value = normalized
    const caret = firstPlaceholderOrEnd(normalized.split(''))
    input.setSelectionRange(caret, caret)
  }
}

const attachDateMask = (input: HTMLInputElement): void => {
  if (attachedInputs.has(input)) {
    return
  }
  attachedInputs.add(input)

  input.placeholder ||= MASK_TEMPLATE

  input.addEventListener('focus', () => onFocus(input))
  input.addEventListener('click', () => onClick(input))
  input.addEventListener('blur', () => onBlur(input))
  input.addEventListener('paste', event => onPaste(input, event))
  input.addEventListener('input', () => onInput(input))
  input.addEventListener('keydown', (event) => {
    if (event.defaultPrevented) {
      return
    }

    if (event.ctrlKey || event.metaKey || event.altKey) {
      return
    }

    if (NAVIGATION_KEYS.has(event.key)) {
      return
    }

    if (event.key === '-') {
      event.preventDefault()
      const [start] = getSelection(input)
      const next = findNextEditablePosition(start + 1)
      if (next !== null) {
        input.setSelectionRange(next, next)
      }
      return
    }

    if (event.key === 'Backspace') {
      event.preventDefault()
      onBackspace(input)
      return
    }

    if (event.key === 'Delete') {
      event.preventDefault()
      onDelete(input)
      return
    }

    if (/[0-9]/.test(event.key)) {
      event.preventDefault()
      onDigit(input, event.key)
      return
    }

    event.preventDefault()
  })
}

export function applyTemplateDateMask(selector: string): void {
  const inputs = document.querySelectorAll<HTMLInputElement>(selector)
  inputs.forEach(attachDateMask)
}

export { MASK_TEMPLATE }

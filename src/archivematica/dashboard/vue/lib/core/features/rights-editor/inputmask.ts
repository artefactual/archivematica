import Inputmask from 'inputmask/dist/inputmask.es6.js'
import $ from 'jquery'

const DATE_INPUT_SELECTOR = 'input[type="text"][name*="date"]'

type InputmaskMaskset = {
  validPositions: Record<number, { input?: string }>
}

const getPreviousInput = (maskset: InputmaskMaskset, pos: number): string =>
  String(maskset.validPositions[pos - 1]?.input ?? '')

const MONTH_RULES = {
  0: /[1-9]/,
  1: /[0-2]/,
} as const

const DAY_RULES = {
  0: /[1-9]/,
  3: /[0-1]/,
} as const

const ANY_DIGIT_RE = /[0-9]/

const validateByPreviousDigit = (
  ch: string,
  maskset: InputmaskMaskset,
  pos: number,
  rules: Record<string, RegExp>,
  fallback = false,
): boolean => {
  // For the second digit in month/day, decide validity from the first digit.
  // Example: month tens "1" only allows units 0-2.
  const previous = getPreviousInput(maskset, pos)
  const rule = rules[previous]
  if (rule) {
    return rule.test(ch)
  }
  return fallback ? ANY_DIGIT_RE.test(ch) : false
}

const RIGHTS_DATE_MASK_OPTIONS = {
  // Supports: yyyy, yyyy-mm, yyyy-mm-dd
  // `mM` and `dD` split month/day into two positions so we can enforce ranges.
  mask: 'yyyy[-mM[-dD]]',
  greedy: true,
  noValuePatching: true,
  definitions: {
    // Custom year token so placeholder renders as "yyyy" (instead of "____").
    y: {
      validator: '[0-9]',
      placeholder: 'y',
    },
    // Month tens: 0 or 1.
    m: {
      validator: '[01]',
      placeholder: 'm',
    },
    // Month units depend on the previous month tens digit.
    M: {
      placeholder: 'm',
      validator: (ch: string, maskset: InputmaskMaskset, pos: number): boolean =>
        validateByPreviousDigit(ch, maskset, pos, MONTH_RULES),
    },
    // Day tens: 0-3.
    d: {
      validator: '[0-3]',
      placeholder: 'd',
    },
    // Day units depend on day tens digit; defaults to any digit for 1x/2x.
    D: {
      placeholder: 'd',
      validator: (ch: string, maskset: InputmaskMaskset, pos: number): boolean =>
        validateByPreviousDigit(ch, maskset, pos, DAY_RULES, true),
    },
  },
} as const

export function applyDateInputMask(selector = DATE_INPUT_SELECTOR): void {
  $(selector).each((_: number, el: Element) => {
    const input = el as HTMLInputElement & { inputmask?: unknown }
    if (input.inputmask) {
      return
    }

    Inputmask(RIGHTS_DATE_MASK_OPTIONS).mask(input)
  })
}

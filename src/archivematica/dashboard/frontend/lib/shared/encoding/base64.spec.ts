import { describe, it, expect } from 'vitest'
import { encodeBase64, decodeBase64 } from '@/shared/encoding/base64'

describe('base64 encoding helpers', () => {
  it.each([
    ['hello', 'aGVsbG8='],
    ['hi', 'aGk='],
  ])('produces expected base64 output for %s', (input, expected) => {
    expect(encodeBase64(input)).toBe(expected)
  })

  it('round-trips unicode safely', () => {
    expect(decodeBase64(encodeBase64('mañana'))).toBe('mañana')
  })

  it('decodes known base64 back to raw text', () => {
    expect(decodeBase64('a25vd24=' as ReturnType<typeof encodeBase64>)).toBe('known')
  })
})

import { describe, expect, it } from 'vitest'
import { formatDateTime } from './date'

describe('shared/date', () => {
  it.each([
    { timestamp: 0 },
    { timestamp: 1700000000 },
    { timestamp: -1 },
    { timestamp: 9999999999 },
  ])('returns fixed-format local date-time text for timestamp $timestamp', ({ timestamp }) => {
    expect(formatDateTime(timestamp)).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/)
  })

  it('uses minute-level precision for sub-second values', () => {
    expect(formatDateTime(1700000000.5)).toBe(formatDateTime(1700000000))
  })

  it('changes output when the minute changes', () => {
    expect(formatDateTime(1700000000 + 60)).not.toBe(formatDateTime(1700000000))
  })
})

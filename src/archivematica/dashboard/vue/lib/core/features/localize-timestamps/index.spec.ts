import { describe, expect, it } from 'vitest'
import { localizeTimestampElements } from './index'

describe('localize-timestamps feature', () => {
  it.each([
    { raw: '0' },
    { raw: '1700000000' },
    { raw: '1700000000.5' },
    { raw: '-1' },
  ])('localizes .timestamp values for $raw', ({ raw }) => {
    document.body.innerHTML = `<span class="timestamp">${raw}</span>`
    localizeTimestampElements()

    const timestamp = document.querySelector('.timestamp') as HTMLElement
    const expected = (() => {
      const date = new Date(Number(raw) * 1000)
      const pad = (n: number) => String(n).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
    })()
    expect(timestamp.textContent).toBe(expected)
  })

  it.each([
    { raw: '2024-01-02T03:04:05+00:00' },
    { raw: '2025-12-31T23:59:59+00:00' },
  ])('localizes .datetime values for $raw', ({ raw }) => {
    document.body.innerHTML = `<span class="datetime">${raw}</span>`
    localizeTimestampElements()

    const datetime = document.querySelector('.datetime') as HTMLElement
    expect(datetime.textContent).toBe(new Date(raw).toLocaleString())
  })

  it.each([
    {
      cssClass: 'timestamp',
      raw: 'not-a-number',
    },
    {
      cssClass: 'datetime',
      raw: 'not-a-date',
    },
  ])('clears invalid .$cssClass value "$raw"', ({ cssClass, raw }) => {
    document.body.innerHTML = `<span class="${cssClass}">${raw}</span>`
    localizeTimestampElements()

    const element = document.querySelector(`.${cssClass}`) as HTMLElement
    expect(element.textContent).toBe('')
  })
})

import { describe, expect, it, beforeEach, vi } from 'vitest'
import { useArchivalStorageUrlState } from './useArchivalStorageUrlState'
import type { SearchRow } from '../types'

const replaceStateSpy = vi.spyOn(window.history, 'replaceState')
const getLastReplacedUrl = () => {
  const calls = replaceStateSpy.mock.calls as [unknown, unknown, string][]
  const lastCall = calls[calls.length - 1]
  return lastCall?.[2]
}

describe('useArchivalStorageUrlState', () => {
  beforeEach(() => {
    replaceStateSpy.mockClear()
    window.history.replaceState(null, '', '/archival-storage/')
  })

  it('hydrates initial showFiles state from file_mode param', () => {
    window.history.replaceState(null, '', '/archival-storage/?file_mode=true')

    const { getInitialShowFiles } = useArchivalStorageUrlState()

    expect(getInitialShowFiles()).toBe(true)
  })

  it('hydrates initial rows from repeated query params', () => {
    window.history.replaceState(
      null,
      '',
      '/archival-storage/?query=one&field=&fieldName=&type=term&op=and&query=two&field=AIPUUID&fieldName=&type=string',
    )

    const { getInitialRows } = useArchivalStorageUrlState()

    const rows = getInitialRows()
    expect(rows).toHaveLength(2)
    expect(rows[0]?.query).toBe('one')
    expect(rows[1]?.op).toBe('and')
    expect(rows[1]?.query).toBe('two')
  })

  it('syncs search URL with serialized rows and file mode', () => {
    const { syncSearchUrl } = useArchivalStorageUrlState()
    const rows: SearchRow[] = [
      { id: 'search-row-1', op: '', query: 'foo', field: '', fieldName: '', type: 'term' },
      { id: 'search-row-2', op: 'or', query: 'bar', field: 'FILEUUID', fieldName: '', type: 'term' },
    ]

    syncSearchUrl(rows, true)

    expect(replaceStateSpy).toHaveBeenCalled()
    const url = getLastReplacedUrl()
    expect(url).toContain('/archival-storage/?')
    expect(url).toContain('query=foo')
    expect(url).toContain('query=bar')
    expect(url).toContain('op=or')
    expect(url).toContain('file_mode=true')
  })

  it('syncs reset URL and preserves file mode when enabled', () => {
    const { syncResetUrl } = useArchivalStorageUrlState()

    syncResetUrl(true)

    expect(replaceStateSpy).toHaveBeenCalled()
    const url = getLastReplacedUrl()
    expect(url).toBe('/archival-storage/?file_mode=true')
  })

  it('syncs reset URL to clean path when file mode is disabled', () => {
    const { syncResetUrl } = useArchivalStorageUrlState()

    syncResetUrl(false)

    expect(replaceStateSpy).toHaveBeenCalled()
    const url = getLastReplacedUrl()
    expect(url).toBe('/archival-storage/')
  })
})

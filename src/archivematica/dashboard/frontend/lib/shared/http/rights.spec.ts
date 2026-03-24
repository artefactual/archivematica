import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { listRightsFormdata, saveRightsFormdata, deleteRightsFormdata } from '@/shared/http/rights'

const mockFetch = vi.fn()

describe('rights http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('lists rights formdata records', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ results: [] }),
    })

    await listRightsFormdata('copyrightnote', 123)

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/formdata/copyrightnote/123/')
    expect(init?.method ?? 'GET').toBe('GET')
  })

  it('saves rights formdata records with form body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ message: 'Added.' }),
    })

    await saveRightsFormdata('rightsnote', 99, { rightsgrantednote: 'note value' }, 7)

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/formdata/rightsnote/99/')
    expect(init?.method).toBe('POST')
    const body = init?.body as URLSearchParams
    expect(body.get('rightsgrantednote')).toBe('note value')
    expect(body.get('id')).toBe('7')
  })

  it('deletes rights formdata records', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ message: 'Deleted.' }),
    })

    await deleteRightsFormdata('rightsrestriction', 42, 17)

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/formdata/rightsrestriction/42/17/')
    expect(init?.method).toBe('DELETE')
    const body = init?.body as URLSearchParams
    expect(body.get('id')).toBe('17')
  })
})

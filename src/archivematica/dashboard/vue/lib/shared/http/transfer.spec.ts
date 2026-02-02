import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getSourceLocations, getTransferStatus, createMetadataSetUuid } from '@/shared/http/transfer'

const mockFetch = vi.fn()

describe('transfer http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('fetches source locations without CSRF header', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ objects: [] }),
    })

    await getSourceLocations()

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/transfer/locations/')
    const headers = new Headers(init?.headers as HeadersInit)
    expect(headers.has('X-CSRFToken')).toBe(false)
  })

  it('fetches transfer status for a UUID', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ status: 'ok' }),
    })

    await getTransferStatus('transfer-uuid')

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/transfer/status/transfer-uuid/')
  })

  it('creates metadata set UUID', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ uuid: 'metadata-uuid' }),
    })

    const result = await createMetadataSetUuid()

    expect(result).toBe('metadata-uuid')
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/transfer/create_metadata_set_uuid/')
  })
})

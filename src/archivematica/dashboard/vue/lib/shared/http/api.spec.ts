import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getProcessingConfigurations, createTransferPackage } from '@/shared/http/api'

const mockFetch = vi.fn()

describe('api http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('fetches processing configurations without CSRF header', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ processing_configurations: ['default'] }),
    })

    await getProcessingConfigurations()

    expect(mockFetch).toHaveBeenCalled()
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/api/processing-configuration/')
    const headers = new Headers(init?.headers as HeadersInit)
    expect(headers.has('X-CSRFToken')).toBe(false)
  })

  it('creates transfer packages with JSON payload', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ uuid: 'transfer-uuid', name: 'Test', status: 'processing' }),
    })

    await createTransferPackage({
      name: 'Test',
      type: 'standard',
      accession: 'ACC',
      access_system_id: 'SYS',
      processing_config: 'config',
      auto_approve: false,
      path: 'encoded-path',
      metadata_set_id: 'metadata-1',
    })

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)
    expect(init?.method).toBe('POST')
    expect(headers.has('X-CSRFToken')).toBe(true)
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(init?.body).toBe(
      JSON.stringify({
        name: 'Test',
        type: 'standard',
        accession: 'ACC',
        access_system_id: 'SYS',
        processing_config: 'config',
        auto_approve: false,
        path: 'encoded-path',
        metadata_set_id: 'metadata-1',
      }),
    )
  })
})

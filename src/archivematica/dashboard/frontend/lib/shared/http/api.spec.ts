import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getProcessingConfigurations,
  createTransferPackage,
} from '@/shared/http/api'
import { encodeBase64 } from '@/shared/encoding/base64'

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

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/api/processing-configuration/')
    const headers = new Headers(init?.headers as HeadersInit)
    expect(headers.has('X-CSRFToken')).toBe(false)
  })

  it('creates transfer packages with JSON payload', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ id: 'transfer-uuid' }),
    })

    const response = await createTransferPackage({
      name: 'Test',
      type: 'standard',
      accession: 'ACC',
      access_system_id: 'SYS',
      processing_config: 'config',
      auto_approve: false,
      path: encodeBase64('path-1'),
      metadata_set_id: 'metadata-1',
    })

    expect(response).toEqual({ id: 'transfer-uuid' })

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)
    expect(init?.method).toBe('POST')
    expect(headers.has('X-CSRFToken')).toBe(true)
    expect(new URL(url).pathname).toBe('/api/v2beta/package/')
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(init?.body).toBe(
      JSON.stringify({
        name: 'Test',
        type: 'standard',
        accession: 'ACC',
        access_system_id: 'SYS',
        processing_config: 'config',
        auto_approve: false,
        path: encodeBase64('path-1'),
        metadata_set_id: 'metadata-1',
      }),
    )
  })

  it('throws when transfer package create response is missing id', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({}),
    })

    await expect(createTransferPackage({
      name: 'Test',
      type: 'standard',
      accession: 'ACC',
      access_system_id: 'SYS',
      processing_config: 'config',
      auto_approve: false,
      path: encodeBase64('path-1'),
      metadata_set_id: 'metadata-1',
    })).rejects.toThrow('Expected "id" field in transfer package create response.')
  })
})

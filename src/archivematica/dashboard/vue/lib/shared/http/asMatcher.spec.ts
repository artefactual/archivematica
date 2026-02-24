import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createArchivesSpacePair,
  deleteArchivesSpacePair,
} from '@/shared/http/asMatcher'

const mockFetch = vi.fn()

describe('asMatcher http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('creates a matcher pair with the expected payload', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      text: async () => '',
    })

    const result = await createArchivesSpacePair({
      dipUuid: 'dip-1',
      resourceId: '/repositories/2/resources/9',
      fileUuid: 'file-1',
    })

    expect(result).toBe('created')

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect(new URL(url).pathname).toBe('/ingest/dip-1/upload/as/match/')
    expect(init.method).toBe('POST')
    expect(new Headers(init.headers as HeadersInit).get('X-CSRFToken')).toBe('test-csrf-token')
    expect(JSON.parse(String(init.body))).toEqual({
      resource_id: '/repositories/2/resources/9',
      file_uuid: 'file-1',
    })
  })

  it('returns duplicate for a 409 response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      statusText: 'Conflict',
      text: async () => 'duplicate',
    })

    const result = await createArchivesSpacePair({
      dipUuid: 'dip-1',
      resourceId: '/repositories/2/resources/9',
      fileUuid: 'file-1',
    })

    expect(result).toBe('duplicate')
  })

  it('deletes a matcher pair with the expected payload', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      text: async () => '',
    })

    await deleteArchivesSpacePair({
      dipUuid: 'dip-1',
      resourceId: '/repositories/2/resources/9',
      fileUuid: 'file-1',
    })

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect(new URL(url).pathname).toBe('/ingest/dip-1/upload/as/match/')
    expect(init.method).toBe('DELETE')
    expect(JSON.parse(String(init.body))).toEqual({
      resource_id: '/repositories/2/resources/9',
      file_uuid: 'file-1',
    })
  })
})

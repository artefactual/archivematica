import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getSourceLocations,
  getTransferSummaries,
  getTransferJobGroups,
  createMetadataSetUuid,
} from '@/shared/http/transfer'

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
      text: async () => JSON.stringify([
        {
          uuid: 'location-uuid',
          description: null,
          enabled: true,
          path: '/var/archivematica/sharedDirectory/watchedDirectories',
          purpose: 'TS',
          relative_path: 'watchedDirectories',
          space: '/api/v2/space/space-uuid/',
          pipeline: ['/api/v2/pipeline/pipeline-uuid/'],
          resource_uri: '/api/v2/location/location-uuid/',
          used: 0,
          quota: null,
        },
      ]),
    })

    const locations = await getSourceLocations()
    expect(locations[0]).toMatchObject({
      uuid: 'location-uuid',
      purpose: 'TS',
      description: null,
    })

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/transfer/locations/')
    const headers = new Headers(init?.headers as HeadersInit)
    expect(headers.has('X-CSRFToken')).toBe(false)
  })

  it('throws for invalid source location payloads', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify([{ uuid: 'location-uuid' }]),
    })

    await expect(getSourceLocations()).rejects.toThrow('Expected source location')
  })

  it('fetches internal transfer summaries with unchanged checks', async () => {
    const raw = JSON.stringify({ results: [] })
    mockFetch.mockResolvedValueOnce({ ok: true, text: async () => raw })

    const response = await getTransferSummaries({})

    expect(response).toMatchObject({ changed: true, data: { results: [] } })
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/transfer/status/')
  })

  it('fetches grouped jobs for one transfer', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ results: [] }),
    })

    await getTransferJobGroups('transfer-uuid')

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/transfer/transfer-uuid/job-groups/')
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

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getIngestStatuses,
  getIngestStatus,
  getUploadTarget,
  setUploadTarget,
  checkUploadDestinationStatusCode,
  getIngestNormalizationReportUrl,
  getIngestUploadAsUrl,
  getIngestPreviewUrl,
} from '@/shared/http/ingest'

const mockFetch = vi.fn()

describe('ingest http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('fetches ingest statuses with cache busting', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ objects: [], mcp: true }),
    })

    await getIngestStatuses()

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/ingest/status/')
    expect(url).toMatch(/[_]=\d+/)
  })

  it('fetches one ingest status with cache busting', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ objects: [], mcp: true }),
    })

    await getIngestStatus('sip-uuid')

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/ingest/status/sip-uuid/')
    expect(url).toMatch(/[_]=\d+/)
  })

  it('supports raw-response unchanged checks for ingest statuses', async () => {
    const raw = JSON.stringify({ objects: [], mcp: true })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => raw,
    })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => raw,
    })

    const first = await getIngestStatuses({})
    const second = await getIngestStatuses({ previousRaw: first.raw })

    expect(first).toMatchObject({
      changed: true,
      data: { objects: [], mcp: true },
    })
    expect(second).toEqual({
      changed: false,
      raw,
    })
  })

  it('gets and sets upload target with proper methods', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ target: 'demo-slug' }),
    })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ ready: true }),
    })

    const target = await getUploadTarget('sip-uuid')
    const result = await setUploadTarget('sip-uuid', 'demo-slug')

    expect(target).toEqual({ target: 'demo-slug' })
    expect(result).toEqual({ ready: true })

    const [, getInit] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const [, postInit] = mockFetch.mock.calls[1] as [string, RequestInit?]
    const postHeaders = new Headers(postInit?.headers as HeadersInit)
    const postBody = new URLSearchParams(postInit?.body as string)

    expect(getInit?.method).toBe('GET')
    expect(postInit?.method).toBe('POST')
    expect(postHeaders.get('X-CSRFToken')).toBe('test-csrf-token')
    expect(postBody.get('target')).toBe('demo-slug')
  })

  it('parses plain status code from upload destination check', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => '200',
    })

    const statusCode = await checkUploadDestinationStatusCode('target-slug')

    expect(statusCode).toBe(200)
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const parsed = new URL(url)
    expect(parsed.pathname).toBe('/ingest/upload/url/check/')
    expect(parsed.searchParams.get('target')).toBe('target-slug')
  })

  it('throws when upload destination check body is not numeric', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => 'OK',
    })

    await expect(checkUploadDestinationStatusCode('target-slug')).rejects.toThrow(
      'Expected numeric HTTP status code response',
    )
  })

  it('builds ingest monitor URLs', () => {
    expect(getIngestNormalizationReportUrl('sip-1')).toContain('/ingest/normalization-report/sip-1/')
    expect(getIngestUploadAsUrl('sip-1')).toContain('/ingest/sip-1/upload/as/')
    expect(getIngestPreviewUrl('aip', 'job-1')).toContain('/ingest/preview/aip/job-1/')
  })
})

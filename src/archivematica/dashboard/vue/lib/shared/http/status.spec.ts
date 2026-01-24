import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { HttpError, toHttpErrorInfo } from '@/shared/http'
import { getStatus } from '@/shared/http/status'

const mockFetch = vi.fn()

describe('status api', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('calls /status/ with cache busting', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ sip: 0, transfer: 0, dip: 0 }),
    })

    await getStatus()

    expect(mockFetch).toHaveBeenCalled()
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/status/?')
    expect(url).toMatch(/[_]=\d+/)
  })

  it('returns parsed status counts', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ sip: 1, transfer: 2, dip: 3 }),
    })

    await expect(getStatus()).resolves.toEqual({ sip: 1, transfer: 2, dip: 3 })
  })

  it('throws when response is empty', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => '',
    })

    await expect(getStatus()).rejects.toThrow('Expected JSON response')
  })

  it('throws HttpError on non-ok responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Server Error',
      url: '/status/',
      text: async () => '<html>error</html>',
    })

    const err = await getStatus().catch(error => error)
    expect(err).toBeInstanceOf(HttpError)
    const info = toHttpErrorInfo(err)
    expect(info?.status).toBe(500)
    expect(info?.url).toContain('/status/')
  })
})

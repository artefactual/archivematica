import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { executeChoice } from '@/shared/http/mcp'

const mockFetch = vi.fn()

describe('mcp http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('posts execute payload as form-urlencoded', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => 'ok',
    })

    await executeChoice({ uuid: 'job-uuid', choice: 'approve' })

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)
    const body = new URLSearchParams(init?.body as string)

    expect(url).toContain('/mcp/execute/')
    expect(init?.method).toBe('POST')
    expect(headers.get('X-CSRFToken')).toBe('test-csrf-token')
    expect(body.get('uuid')).toBe('job-uuid')
    expect(body.get('choice')).toBe('approve')
  })
})

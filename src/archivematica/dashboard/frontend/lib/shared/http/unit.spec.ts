import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { deleteUnit, deleteCompletedUnits, getUnitDetailUrl } from '@/shared/http/unit'

const mockFetch = vi.fn()

describe('unit http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('deletes a single unit with csrf token', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ removed: true }),
    })

    const response = await deleteUnit('transfer', 'transfer-uuid')

    expect(response).toEqual({ removed: true })
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)
    expect(url).toContain('/transfer/transfer-uuid/delete/')
    expect(init?.method).toBe('DELETE')
    expect(headers.get('X-CSRFToken')).toBe('test-csrf-token')
  })

  it('deletes all completed units and returns removed list', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ removed: ['u1', 'u2'] }),
    })

    const response = await deleteCompletedUnits('ingest')

    expect(response).toEqual({ removed: ['u1', 'u2'] })
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/ingest/delete/')
    expect(init?.method).toBe('DELETE')
  })

  it('maps 409 response to removed=false payload for single delete', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      statusText: 'Conflict',
      url: '/transfer/uuid/delete/',
      text: async () => JSON.stringify({ removed: false }),
    })

    const response = await deleteUnit('transfer', 'uuid')
    expect(response).toEqual({ removed: false })
  })

  it('builds unit detail URLs', () => {
    expect(getUnitDetailUrl('transfer', 'u1')).toContain('/transfer/u1/')
    expect(getUnitDetailUrl('ingest', 'u2')).toContain('/ingest/u2/')
  })
})

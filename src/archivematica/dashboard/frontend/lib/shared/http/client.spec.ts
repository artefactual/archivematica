import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { toHttpErrorInfo } from '@/shared/http'
import { HttpError } from '@/shared/http/client'
import { createHttpClient } from '@/shared/http/client'

const mockFetch = vi.fn()

describe('shared http client', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('appends query params and cache buster', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ ok: true }),
    })

    const client = createHttpClient()
    await client.getJson('/status/', {
      query: { foo: 'bar', empty: null },
      cacheBust: true,
    })

    expect(mockFetch).toHaveBeenCalled()
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/status/?')
    expect(url).toContain('foo=bar')
    expect(url).toMatch(/[_]=\d+/)
  })

  it('sends JSON body with correct headers', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ ok: true }),
    })

    const client = createHttpClient()
    await client.requestJson('/api/test/', {
      method: 'POST',
      json: { a: 1 },
    })

    expect(mockFetch).toHaveBeenCalled()
    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)

    expect(init?.method).toBe('POST')
    expect(init?.body).toBe(JSON.stringify({ a: 1 }))
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(headers.get('X-Requested-With')).toBe('XMLHttpRequest')
  })

  it('throws HttpError for non-ok responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Server Error',
      url: '/status/',
      text: async () => '<html>error</html>',
    })

    const client = createHttpClient()
    await expect(client.getJson('/status/')).rejects.toBeInstanceOf(HttpError)
  })

  it('normalizes HttpError details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      url: '/status/',
      text: async () => JSON.stringify({ error: 'nope' }),
    })

    const client = createHttpClient()
    const err = await client.getJson('/status/').catch((error: unknown) => error)
    expect(err).toBeInstanceOf(HttpError)
    const info = toHttpErrorInfo(err)
    expect(info).toEqual({
      status: 400,
      statusText: 'Bad Request',
      url: '/status/',
      bodyText: JSON.stringify({ error: 'nope' }),
      bodyJson: { error: 'nope' },
    })
  })

  it('returns null for non-HttpError values', () => {
    expect(toHttpErrorInfo(new Error('nope'))).toBeNull()
  })

  it('returns null for empty responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => '',
    })

    const client = createHttpClient()
    const result = await client.getJson('/status/')
    expect(result).toBeNull()
  })

  it('returns null for non-JSON success bodies', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => '<html>ok</html>',
    })

    const client = createHttpClient()
    const result = await client.getJson('/status/')
    expect(result).toBeNull()
  })

  it('throws when strictJson is enabled and response is non-JSON', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => '<html>ok</html>',
    })

    const client = createHttpClient()
    await expect(client.getJson('/status/', { strictJson: true })).rejects.toThrow(
      'Expected JSON response',
    )
  })

  it('throws when strictJson is enabled and response is empty', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => '',
    })

    const client = createHttpClient()
    await expect(client.getJson('/status/', { strictJson: true })).rejects.toThrow(
      'Expected JSON response',
    )
  })

  it('returns plain text responses without JSON parsing', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => 'OK',
    })

    const client = createHttpClient()
    const result = await client.getText('/mcp/list/')

    expect(result).toBe('OK')
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/mcp/list/')
  })

  it('returns changed payload metadata when JSON response differs', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ objects: [], mcp: true }),
    })

    const client = createHttpClient()
    const result = await client.getJsonIfChanged('/transfer/status/', {
      previousRaw: '{"objects":[],"mcp":false}',
      strictJson: true,
      cacheBust: true,
    })

    expect(result).toMatchObject({
      changed: true,
      data: { objects: [], mcp: true },
    })
    expect(result.raw).toContain('"mcp":true')
  })

  it('returns unchanged payload metadata when raw response is identical', async () => {
    const raw = '{"objects":[],"mcp":true}'
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => raw,
    })

    const client = createHttpClient()
    const result = await client.getJsonIfChanged('/transfer/status/', {
      previousRaw: raw,
      strictJson: true,
      cacheBust: true,
    })

    expect(result).toEqual({
      changed: false,
      raw,
    })
  })

  it('sends CSRF header for unsafe API requests when csrftoken cookie exists', async () => {
    document.cookie = 'csrftoken=test-csrf-token'
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ ok: true }),
    })

    const client = createHttpClient()
    await client.requestJson('/api/test/', {
      method: 'POST',
      json: { a: 1 },
    })

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)
    expect(headers.get('X-CSRFToken')).toBe('test-csrf-token')
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getFilesystemContents,
  getFilesystemChildren,
  copyMetadataFiles,
  openFilesystemDownload,
} from '@/shared/http/filesystem'
import { encodeBase64 } from '@/shared/encoding/base64'

const mockFetch = vi.fn()
const mockOpen = vi.fn()

describe('filesystem api', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('open', mockOpen)
    mockFetch.mockReset()
    mockOpen.mockReset()
    document.cookie = 'csrftoken=token-123'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('requests filesystem contents with path query', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ name: 'root', children: [] }),
    })

    await getFilesystemContents('/tmp')

    expect(mockFetch).toHaveBeenCalled()
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const parsed = new URL(url)
    expect(parsed.pathname).toBe('/filesystem/contents/')
    expect(parsed.searchParams.get('path')).toBe('/tmp')
  })

  it('requests filesystem children for a location', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ entries: [], directories: [] }),
    })

    const path = encodeBase64('path')
    await getFilesystemChildren('location-123', path)

    expect(mockFetch).toHaveBeenCalled()
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const parsed = new URL(url)
    expect(parsed.pathname).toBe('/filesystem/children/location/location-123/')
    expect(parsed.searchParams.get('path')).toBe('cGF0aA==')
  })

  it('posts metadata files with csrf token and form body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({}),
    })

    const sourcePaths = [encodeBase64('a'), encodeBase64('b')]
    await copyMetadataFiles('sip-123', sourcePaths)

    expect(mockFetch).toHaveBeenCalled()
    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    const headers = new Headers(init?.headers as HeadersInit)
    const body = new URLSearchParams(init?.body as string)

    expect(init?.method).toBe('POST')
    expect(headers.get('Content-Type')).toContain('application/x-www-form-urlencoded')
    expect(headers.get('X-CSRFToken')).toBe('token-123')
    expect(body.get('sip_uuid')).toBe('sip-123')
    expect(body.getAll('source_paths[]')).toEqual(sourcePaths)
  })

  it('opens filesystem download in a new tab', () => {
    const filePath = encodeBase64('file')
    openFilesystemDownload(filePath)

    expect(mockOpen).toHaveBeenCalled()
    const [url, target, features] = mockOpen.mock.calls[0] as [string, string, string]
    expect(url).toContain('/filesystem/download_fs/?')
    expect(url).toContain('filepath=ZmlsZQ%3D%3D')
    expect(target).toBe('_blank')
    expect(features).toBe('noopener')
  })
})

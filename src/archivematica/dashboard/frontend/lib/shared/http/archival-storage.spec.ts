import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  createArchivalStorageAicUrl,
  createArchivalStorageAipFileDownloadUrl,
  createArchivalStorageAipUrl,
  createArchivalStorageRawFileUrl,
  createArchivalStorageSearchUrl,
  createArchivalStorageThumbnailUrl,
  loadArchivalStorageState,
  openArchivalStorageCsv,
  saveArchivalStorageState,
  searchArchivalStorage,
} from '@/shared/http/archival-storage'

const mockFetch = vi.fn()
const mockOpen = vi.fn()

describe('archival storage http', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('open', mockOpen)
    mockFetch.mockReset()
    mockOpen.mockReset()
    document.cookie = 'csrftoken=test-csrf-token'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('requests archival storage search with query string', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ iTotalRecords: 0, iTotalDisplayRecords: 0, sEcho: 1, aaData: [] }),
    })

    const params = new URLSearchParams('query=test&iDisplayStart=0')
    await searchArchivalStorage(params)

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/archival-storage/search/?query=test&iDisplayStart=0')
  })

  it('posts archival storage state with csrf header', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    })

    await saveArchivalStorageState('aips', {
      columns: [{ visible: true }],
    })

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/archival-storage/save_state/aips/')
    const headers = new Headers(init?.headers as HeadersInit)
    expect(init?.method).toBe('POST')
    expect(headers.get('X-CSRFToken')).toBe('test-csrf-token')
  })

  it('loads archival storage state', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ columns: [{ visible: false }] }),
    })

    const state = await loadArchivalStorageState('aipfiles')
    expect(state.columns?.[0]?.visible).toBe(false)

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit?]
    expect(url).toContain('/archival-storage/load_state/aipfiles/')
  })

  it('opens CSV export with query params and preserves repeated filters', () => {
    const params = new URLSearchParams('query=first&query=second&requestFile=true&mimeType=text%2Fcsv')
    openArchivalStorageCsv(params)

    const [url, target, features] = mockOpen.mock.calls[0] as [string, string, string]
    expect(url).toContain('/archival-storage/search/?query=first&query=second&requestFile=true&mimeType=text%2Fcsv')
    expect(target).toBe('_blank')
    expect(features).toBe('noopener')
  })

  it('builds create AIC endpoint URL with query params', () => {
    const params = new URLSearchParams('query=foo&type=term')
    const url = createArchivalStorageAicUrl(params)

    expect(url).toBe('/archival-storage/search/create_aic/?query=foo&type=term')
  })

  it('builds archival storage URLs', () => {
    expect(createArchivalStorageSearchUrl()).toBe('/archival-storage/search/')
    expect(createArchivalStorageSearchUrl(new URLSearchParams('query=test'))).toBe('/archival-storage/search/?query=test')
    expect(createArchivalStorageAipUrl('aip-uuid')).toBe('/archival-storage/aip-uuid/')
    expect(createArchivalStorageAipFileDownloadUrl('file-uuid')).toBe('/archival-storage/download/aip/file/file-uuid/')
    expect(createArchivalStorageThumbnailUrl('file-uuid')).toBe('/archival-storage/thumbnail/file-uuid/')
    expect(createArchivalStorageRawFileUrl('doc-id')).toBe('/archival-storage/search/json/file/doc-id/')
  })
})

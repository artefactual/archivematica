import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { encodeBase64, type Base64String } from '@/shared/encoding/base64'
import type { FilesystemBrowseResponse } from '@/shared/http'

vi.mock('@/shared/http', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http')>('@/shared/http')
  return {
    ...actual,
    getFilesystemChildren: vi.fn(),
  }
})

vi.mock('@/shared/encoding/base64', async () => {
  const actual = await vi.importActual<typeof import('@/shared/encoding/base64')>('@/shared/encoding/base64')
  return {
    ...actual,
    encodeBase64: vi.fn((str: string) => btoa(str) as Base64String),
    decodeBase64: vi.fn((str: string) => atob(str)),
  }
})

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

import { getFilesystemChildren } from '@/shared/http'

describe('useFilesystemTree', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const b64 = (str: string): Base64String => btoa(str) as Base64String

  const createMockResponse = (
    entries: Base64String[],
    directories: Base64String[] = [],
    properties?: Record<Base64String, Record<string, unknown>>,
  ): FilesystemBrowseResponse => ({
    entries,
    directories,
    properties: properties ?? {},
  })

  it('initializes with empty state', async () => {
    const { useFilesystemTree } = await import('./useFilesystemTree')
    const { items, loading, error } = useFilesystemTree()

    expect(items.value).toEqual([])
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  describe('loadRoot', () => {
    it('creates root node and loads children automatically', async () => {
      const mockResponse = createMockResponse(
        [b64('subfolder'), b64('file.txt')],
        [b64('subfolder')],
      )
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/home/user')
      await flushPromises()

      expect(items.value).toHaveLength(1)
      expect(items.value[0]).toMatchObject({
        id: '/home/user',
        path: '/home/user',
        label: 'user',
        kind: 'directory',
        loaded: true,
      })

      expect(items.value[0]?.children).toHaveLength(2)
      expect(items.value[0]?.children?.[0]).toMatchObject({
        id: '/home/user/subfolder',
        path: '/home/user/subfolder',
        label: 'subfolder',
        kind: 'directory',
      })
      expect(items.value[0]?.children?.[1]).toMatchObject({
        id: '/home/user/file.txt',
        path: '/home/user/file.txt',
        label: 'file.txt',
        kind: 'file',
      })
    })

    it('sets loading state during root load', async () => {
      let resolvePromise: ((value: FilesystemBrowseResponse) => void) | undefined
      vi.mocked(getFilesystemChildren).mockReturnValueOnce(
        new Promise<FilesystemBrowseResponse>((resolve) => {
          resolvePromise = resolve
        }),
      )

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loading, loadRoot } = useFilesystemTree()

      expect(loading.value).toBe(false)

      const loadPromise = loadRoot('loc-uuid', '/home/user')
      await flushPromises()

      expect(loading.value).toBe(true)

      resolvePromise?.(createMockResponse([], []))
      await loadPromise
      await flushPromises()

      expect(loading.value).toBe(false)
    })

    it('sets error when location is not provided', async () => {
      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { error, loadRoot } = useFilesystemTree()

      await loadRoot('', '')
      await flushPromises()

      expect(error.value).toBe('metadata.noDirectorySelected')
    })

    it('handles API errors gracefully', async () => {
      vi.mocked(getFilesystemChildren).mockRejectedValueOnce(
        new Error('Network error'),
      )

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { error, items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/home/user')
      await flushPromises()

      expect(error.value).toBe('Network error')
      expect(items.value).toEqual([])
    })

    it('extracts root label from path', async () => {
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(
        createMockResponse([], []),
      )

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/var/archivematica/storage')
      await flushPromises()

      expect(items.value[0]?.label).toBe('storage')
    })

    it('uses full path as label when no segments exist', async () => {
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(
        createMockResponse([], []),
      )

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/')
      await flushPromises()

      expect(items.value[0]?.label).toBe('/')
    })
  })

  describe('loadChildren', () => {
    it('loads children for a directory node', async () => {
      const mockResponse = createMockResponse(
        [b64('child1'), b64('child2')],
        [b64('child1')],
      )
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loadChildren } = useFilesystemTree()

      const node = {
        id: '/path/to/dir',
        path: '/path/to/dir',
        kind: 'directory' as const,
        label: 'dir',
        children: [],
        loaded: false,
      }

      await loadChildren(node, 'loc-uuid')
      await flushPromises()

      expect(node.loaded).toBe(true)
      expect(node.children).toHaveLength(2)
      expect(getFilesystemChildren).toHaveBeenCalledWith(
        'loc-uuid',
        encodeBase64('/path/to/dir'),
      )
    })

    it('does not load children for file nodes', async () => {
      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loadChildren } = useFilesystemTree()

      const node = {
        id: '/path/file.txt',
        path: '/path/file.txt',
        kind: 'file' as const,
        label: 'file.txt',
      }

      await loadChildren(node, 'loc-uuid')

      expect(getFilesystemChildren).not.toHaveBeenCalled()
    })

    it('skips loading if already loaded', async () => {
      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loadChildren } = useFilesystemTree()

      const node = {
        id: '/path/dir',
        path: '/path/dir',
        kind: 'directory' as const,
        label: 'dir',
        children: [],
        loaded: true,
      }

      await loadChildren(node, 'loc-uuid')

      expect(getFilesystemChildren).not.toHaveBeenCalled()
    })

    it('sets loadError on API failure', async () => {
      vi.mocked(getFilesystemChildren).mockRejectedValueOnce(
        new Error('Permission denied'),
      )

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loadChildren } = useFilesystemTree()

      const node = {
        id: '/restricted',
        path: '/restricted',
        kind: 'directory' as const,
        label: 'restricted',
        children: [],
        loaded: false,
        loadError: undefined,
      }

      await loadChildren(node, 'loc-uuid')
      await flushPromises()

      expect(node.loadError).toBe('Permission denied')
      expect(node.loaded).toBe(false)
      expect(node.children).toEqual([])
    })

    it('normalizes non-Error exceptions', async () => {
      vi.mocked(getFilesystemChildren).mockRejectedValueOnce('String error')

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loadChildren } = useFilesystemTree()

      const node = {
        id: '/path',
        path: '/path',
        kind: 'directory' as const,
        label: 'path',
        children: [],
        loaded: false,
        loadError: undefined,
      }

      await loadChildren(node, 'loc-uuid')
      await flushPromises()

      expect(node.loadError).toBe('String error')
    })

    it('uses fallback error message for unknown errors', async () => {
      vi.mocked(getFilesystemChildren).mockRejectedValueOnce({ code: 500 })

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { loadChildren } = useFilesystemTree()

      const node = {
        id: '/path',
        path: '/path',
        kind: 'directory' as const,
        label: 'path',
        children: [],
        loaded: false,
        loadError: undefined,
      }

      await loadChildren(node, 'loc-uuid')
      await flushPromises()

      expect(node.loadError).toBe('metadata.loadFailed')
    })
  })

  describe('retry', () => {
    it('clears error and reloads children', async () => {
      const mockResponse = createMockResponse([b64('file.txt')], [])
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { retry } = useFilesystemTree()

      const node = {
        id: '/path',
        path: '/path',
        kind: 'directory' as const,
        label: 'path',
        children: [],
        loaded: false,
        loadError: 'Previous error',
      }

      await retry(node, 'loc-uuid')
      await flushPromises()

      expect(node.loadError).toBeUndefined()
      expect(node.loaded).toBe(true)
      expect(node.children).toHaveLength(1)
    })
  })

  describe('label building', () => {
    it('includes display_string in label when available', async () => {
      const mockResponse = createMockResponse(
        [b64('folder')],
        [b64('folder')],
        {
          [b64('folder')]: { display_string: 'Special Folder' },
        },
      )
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/home')
      await flushPromises()

      expect(items.value[0]?.children?.[0]?.label).toBe('folder')
      expect(items.value[0]?.children?.[0]?.display).toBe('Special Folder')
    })

    it('uses name only when display_string is not available', async () => {
      const mockResponse = createMockResponse([b64('folder')], [b64('folder')])
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/home')
      await flushPromises()

      expect(items.value[0]?.children?.[0]?.label).toBe('folder')
      expect(items.value[0]?.children?.[0]?.display).toBeUndefined()
    })
  })

  describe('path joining', () => {
    it('joins paths correctly', async () => {
      const mockResponse = createMockResponse([b64('file.txt')], [])
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/parent')
      await flushPromises()

      expect(items.value[0]?.children?.[0]?.path).toBe('/parent/file.txt')
    })

    it('handles trailing slashes in base path', async () => {
      const mockResponse = createMockResponse([b64('file.txt')], [])
      vi.mocked(getFilesystemChildren).mockResolvedValueOnce(mockResponse)

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      await loadRoot('loc-uuid', '/parent/')
      await flushPromises()

      expect(items.value[0]?.children?.[0]?.path).toBe('/parent/file.txt')
    })
  })

  describe('request cancellation', () => {
    it('cancels pending requests on new loadRoot call', async () => {
      let firstResolve: ((value: FilesystemBrowseResponse) => void) | undefined
      let secondResolve: ((value: FilesystemBrowseResponse) => void) | undefined

      vi.mocked(getFilesystemChildren)
        .mockReturnValueOnce(
          new Promise<FilesystemBrowseResponse>((resolve) => {
            firstResolve = resolve
          }),
        )
        .mockReturnValueOnce(
          new Promise<FilesystemBrowseResponse>((resolve) => {
            secondResolve = resolve
          }),
        )

      const { useFilesystemTree } = await import('./useFilesystemTree')
      const { items, loadRoot } = useFilesystemTree()

      // Start first request
      void loadRoot('loc1', '/path1')
      await flushPromises()

      // Start second request (should cancel first)
      const secondLoad = loadRoot('loc2', '/path2')
      await flushPromises()

      // Complete first request (should be ignored)
      firstResolve?.(createMockResponse([b64('ignored')], []))
      await flushPromises()

      // Complete second request (should apply)
      secondResolve?.(createMockResponse([b64('valid')], []))
      await secondLoad
      await flushPromises()

      expect(items.value).toHaveLength(1)
      expect(items.value[0]?.path).toBe('/path2')
      expect(items.value[0]?.children?.[0]?.label).toBe('valid')
    })
  })
})

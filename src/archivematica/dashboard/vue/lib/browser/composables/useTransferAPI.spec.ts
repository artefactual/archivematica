import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useTransferAPI } from '@/browser/composables/useTransferAPI'
import type { TransferComponent } from '@/shared/models'

// Mock base64-helpers
vi.mock('base64-helpers', () => ({
  encode: (str: string) => btoa(str),
  decode: (str: string) => atob(str),
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock window.open
const mockWindowOpen = vi.fn()
vi.stubGlobal('window', {
  ...window,
  open: mockWindowOpen,
})

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: 'csrftoken=test-csrf-token',
})

const getHeadersFromFetchCall = (callIndex: number): Headers => {
  const call = mockFetch.mock.calls[callIndex]
  if (!call) {
    throw new Error(`Expected fetch to be called at least ${callIndex + 1} time(s)`)
  }
  const requestInit = call[1] as RequestInit | undefined
  if (!requestInit) {
    throw new Error('Expected fetch to include request init options')
  }
  const headers = requestInit.headers as Headers | undefined
  if (!headers) {
    throw new Error('Expected fetch to include headers')
  }
  return headers
}

describe('useTransferAPI', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    mockWindowOpen.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getProcessingConfigs', () => {
    it('should fetch processing configurations successfully', async () => {
      const mockConfigs = {
        processing_configurations: ['Default', 'Automated'],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfigs,
      })

      const { getProcessingConfigs } = useTransferAPI()
      const result = await getProcessingConfigs()

      expect(mockFetch).toHaveBeenCalledWith('/api/processing-configuration/', {
        headers: expect.any(Headers),
        credentials: 'same-origin',
      })

      const firstCall = mockFetch.mock.calls[0]
      if (!firstCall) {
        throw new Error('Expected fetch to be called at least once')
      }
      const requestInit = firstCall[1] as RequestInit | undefined
      if (!requestInit) {
        throw new Error('Expected fetch to be called with request init options')
      }
      const headers = requestInit.headers as Headers | undefined
      if (!headers) {
        throw new Error('Expected fetch to include headers')
      }
      expect(headers.get('X-CSRFToken')).toBe('test-csrf-token')

      expect(result).toEqual([
        { pk: 'Default', name: 'Default' },
        { pk: 'Automated', name: 'Automated' },
      ])
    })

    it('should handle errors when fetching processing configurations', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      })

      const { getProcessingConfigs, error } = useTransferAPI()

      await expect(getProcessingConfigs()).rejects.toThrow(
        'Failed to fetch processing configurations',
      )
      expect(error.value).toBe('Failed to fetch processing configurations')
    })
  })

  describe('getSourceLocations', () => {
    it('should fetch and filter enabled transfer source locations', async () => {
      const mockLocations = {
        objects: [
          { uuid: '1', description: 'Location 1', enabled: true, purpose: 'TS' },
          { uuid: '2', description: 'Location 2', enabled: false, purpose: 'TS' },
          { uuid: '3', description: 'Location 3', enabled: true, purpose: 'AS' },
          { uuid: '4', description: 'Location 4', enabled: true, purpose: 'TS' },
        ],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockLocations,
      })

      const { getSourceLocations } = useTransferAPI()
      const result = await getSourceLocations()

      expect(mockFetch).toHaveBeenCalledWith('/transfer/locations/', {
        headers: expect.any(Headers),
        credentials: 'same-origin',
      })

      expect(result).toEqual([
        { uuid: '1', description: 'Location 1', enabled: true, purpose: 'TS' },
        { uuid: '4', description: 'Location 4', enabled: true, purpose: 'TS' },
      ])
    })
  })

  describe('browseLocation', () => {
    it('should browse root location without path', async () => {
      // Mock the API response with base64-encoded data
      const mockFiles = {
        entries: [btoa('folder1'), btoa('file1.txt')],
        directories: [btoa('folder1')],
        properties: {
          [btoa('file1.txt')]: { size: 1024 },
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFiles,
      })

      const { browseLocation } = useTransferAPI()
      const result = await browseLocation('location-uuid')

      expect(mockFetch).toHaveBeenCalledWith('/filesystem/children/location/location-uuid/', {
        method: 'GET',
        headers: expect.any(Headers),
        credentials: 'same-origin',
      })

      const firstCall = mockFetch.mock.calls[0]
      if (!firstCall) {
        throw new Error('Expected fetch to be called at least once')
      }
      const requestInit = firstCall[1] as RequestInit | undefined
      if (!requestInit) {
        throw new Error('Expected fetch to include request init options')
      }
      const headers = requestInit.headers as Headers | undefined
      if (!headers) {
        throw new Error('Expected fetch to include headers')
      }
      expect(headers.get('X-Requested-With')).toBe('XMLHttpRequest')

      expect(result).toEqual([
        {
          name: 'folder1',
          path: 'folder1',
          type: 'directory',
          size: undefined,
          modified: undefined,
          children: [],
          children_fetched: false,
        },
        {
          name: 'file1.txt',
          path: 'file1.txt',
          type: 'file',
          size: 1024,
          modified: undefined,
          children: undefined,
          children_fetched: false,
        },
      ])
    })

    it('should browse location with encoded path', async () => {
      const mockFiles = {
        entries: [],
        directories: [],
        properties: {},
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFiles,
      })

      const { browseLocation } = useTransferAPI()
      await browseLocation('location-uuid', '/some/path')

      // The implementation uses Base64.encode which keeps padding
      const expectedEncodedPath = btoa('/some/path')
      expect(mockFetch).toHaveBeenCalledWith(
        `/filesystem/children/location/location-uuid/?path=${expectedEncodedPath}`,
        {
          method: 'GET',
          headers: expect.any(Headers),
          credentials: 'same-origin',
        },
      )
    })
  })

  describe('createTransfer', () => {
    it('should create a transfer successfully', async () => {
      // Mock transfer creation
      const mockTransferResponse = {
        uuid: 'transfer-uuid',
        name: 'Test Transfer',
        status: 'processing',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTransferResponse,
      })

      const { createTransfer } = useTransferAPI()
      const result = await createTransfer({
        name: 'Test Transfer',
        type: 'standard',
        accession: 'ACC-001',
        accessSystemId: 'SYS-001',
        processingConfig: 'config-1',
        autoApprove: false,
        components: [
          {
            id: '1',
            uuid: 'metadata-1',
            path: '/test/path',
            location: 'loc-uuid',
          },
        ],
      })

      // Check transfer creation call
      expect(mockFetch).toHaveBeenCalledWith('/api/v2beta/package/', {
        method: 'POST',
        body: JSON.stringify({
          name: 'Test Transfer',
          type: 'standard',
          accession: 'ACC-001',
          access_system_id: 'SYS-001',
          processing_config: 'config-1',
          auto_approve: false,
          path: btoa('loc-uuid:/test/path'),
          metadata_set_id: 'metadata-1',
        }),
        headers: expect.any(Headers),
        credentials: 'same-origin',
      })

      expect(result).toEqual(mockTransferResponse)
    })

    it('should handle transfer creation errors', async () => {
      // Mock transfer creation failure
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: 'Transfer creation failed' }),
      })

      const { createTransfer, error } = useTransferAPI()

      await expect(
        createTransfer({
          name: 'Test Transfer',
          type: 'standard',
          accession: '',
          accessSystemId: '',
          processingConfig: 'config-1',
          autoApprove: false,
          components: [{ id: '1', path: '/test/path', location: 'loc-uuid' }],
        }),
      ).rejects.toThrow('Transfer creation failed')

      expect(error.value).toBe('Transfer creation failed')
    })

    it('should omit metadata_set_id when component lacks UUID', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          uuid: 'transfer-uuid',
          name: 'Test Transfer',
          status: 'processing',
        }),
      })

      const { createTransfer } = useTransferAPI()
      await createTransfer({
        name: 'Test Transfer',
        type: 'standard',
        accession: 'ACC-001',
        accessSystemId: 'SYS-001',
        processingConfig: 'config-1',
        autoApprove: false,
        components: [
          {
            id: '1',
            path: '/test/path',
            location: 'loc-uuid',
          },
        ],
      })

      const firstCall = mockFetch.mock.calls[0]
      if (!firstCall) {
        throw new Error('Expected fetch to be called for transfer creation')
      }
      const requestInit = firstCall[1] as Record<string, unknown> | undefined
      if (!requestInit) {
        throw new Error('Expected fetch call to include request init options')
      }
      const body = requestInit.body
      if (typeof body !== 'string') {
        throw new Error('Expected request body to be a stringified payload')
      }
      const payload = JSON.parse(body)
      expect(payload.metadata_set_id).toBe('')
    })
  })

  describe('loading state', () => {
    it('should manage loading state during API calls', async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({ processing_configurations: ['default'] }),
      }

      mockFetch.mockImplementation(async () => {
        return mockResponse
      })

      const { getProcessingConfigs, loading } = useTransferAPI()

      expect(loading.value).toBe(false)

      const promise = getProcessingConfigs()

      // Loading should be true immediately after calling
      expect(loading.value).toBe(true)

      await promise

      // Loading should be false after completion
      expect(loading.value).toBe(false)
    })
  })

  describe('CSRF token handling', () => {
    it('should get valid CSRF token for requests', async () => {
      document.cookie = 'csrftoken=new-test-token; sessionid=abc123'

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ processing_configurations: [] }),
      })

      const { getProcessingConfigs } = useTransferAPI()
      await getProcessingConfigs()

      const headers = getHeadersFromFetchCall(0)
      expect(headers.get('X-CSRFToken')).toBe('new-test-token')
    })

    it('should handle requests without CSRF token', async () => {
      document.cookie = 'sessionid=abc123'

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ processing_configurations: [] }),
      })

      const { getProcessingConfigs } = useTransferAPI()
      await getProcessingConfigs()

      const headers = getHeadersFromFetchCall(0)
      expect(headers.get('X-CSRFToken')).toBeNull()
    })

    it('should read CSRF token from cookie each time', async () => {
      // Start with initial token
      document.cookie = 'csrftoken=initial-token; sessionid=abc123'

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ processing_configurations: [] }),
      })

      const { getProcessingConfigs } = useTransferAPI()
      await getProcessingConfigs()

      let headers = getHeadersFromFetchCall(0)
      expect(headers.get('X-CSRFToken')).toBe('initial-token')

      // Change cookie value
      document.cookie = 'csrftoken=updated-token; sessionid=abc123'

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ processing_configurations: [] }),
      })

      // Make another request
      await getProcessingConfigs()

      headers = getHeadersFromFetchCall(1)
      expect(headers.get('X-CSRFToken')).toBe('updated-token')
    })
  })

  describe('Component Editor', () => {
    describe('openComponentEditor', () => {
      it('should open edit page for disk image components with existing UUID', async () => {
        const { openComponentEditor } = useTransferAPI()

        const component = {
          id: 'component-1',
          path: '/test/path',
          location: 'location-1',
          uuid: 'existing-uuid-123',
        }

        await openComponentEditor(component, 'disk image')

        // Should open window with existing UUID
        expect(mockWindowOpen).toHaveBeenCalledWith(
          '/transfer/component/existing-uuid-123',
          '_blank',
        )
        expect(mockFetch).not.toHaveBeenCalled()
      })

      it('should generate UUID and open edit page for disk image components without UUID', async () => {
        document.cookie = 'csrftoken=test-csrf-token; sessionid=abc123'

        // Mock UUID creation endpoint (no need to mock token refresh since we have a valid token)
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ uuid: 'test-uuid-123' }),
        })

        const { openComponentEditor } = useTransferAPI()

        const component: TransferComponent = {
          id: 'component-1',
          path: '/test/path',
          location: 'location-1',
        }

        await openComponentEditor(component, 'disk image')

        // Should fetch UUID first, then open window
        expect(mockFetch).toHaveBeenCalledWith(
          '/transfer/create_metadata_set_uuid/',
          expect.objectContaining({
            method: 'GET',
            headers: expect.any(Headers),
            credentials: 'same-origin',
          }),
        )
        expect(mockWindowOpen).toHaveBeenCalledWith('/transfer/component/test-uuid-123', '_blank')

        // Should update component with UUID
        expect(component.uuid).toBe('test-uuid-123')
      })

      it('should not allow editing for non-disk-image transfers', async () => {
        const { openComponentEditor } = useTransferAPI()

        const component = {
          id: 'component-1',
          path: '/test/path',
          location: 'location-1',
        }

        await expect(openComponentEditor(component, 'standard')).rejects.toThrow(
          'Edit functionality is only available for disk image transfers',
        )

        // Should not open window or generate UUID
        expect(mockWindowOpen).not.toHaveBeenCalled()
        expect(mockFetch).not.toHaveBeenCalled()
      })

      it('should handle UUID generation failure', async () => {
        document.cookie = 'csrftoken=test-csrf-token; sessionid=abc123'

        // Mock UUID creation endpoint failure
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 500,
        })

        const { openComponentEditor } = useTransferAPI()

        const component = {
          id: 'component-1',
          path: '/test/path',
          location: 'location-1',
        }

        await expect(openComponentEditor(component, 'disk image')).rejects.toThrow(
          'Failed to create metadata set UUID',
        )

        expect(mockWindowOpen).not.toHaveBeenCalled()
      })
    })

    describe('canEditComponents', () => {
      it('should return true for disk image transfers', () => {
        const { canEditComponents } = useTransferAPI()
        expect(canEditComponents('disk image')).toBe(true)
      })

      it('should return false for non-disk-image transfers', () => {
        const { canEditComponents } = useTransferAPI()
        expect(canEditComponents('standard')).toBe(false)
        expect(canEditComponents('zipfile')).toBe(false)
        expect(canEditComponents('zipped bag')).toBe(false)
      })
    })

    describe('getComponentEditUrl', () => {
      it('should return correct edit URL', () => {
        const { getComponentEditUrl } = useTransferAPI()
        expect(getComponentEditUrl('test-uuid')).toBe('/transfer/component/test-uuid')
      })
    })
  })
})

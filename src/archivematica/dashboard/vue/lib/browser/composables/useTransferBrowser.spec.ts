import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useTransferBrowser } from '@/browser/composables/useTransferBrowser'
import { encodeBase64 } from '@/shared/encoding/base64'
import type { TransferComponent } from '@/browser/types'

const mockGetProcessingConfigurations = vi.fn()
const mockCreateTransferPackage = vi.fn()
const mockGetSourceLocations = vi.fn()
const mockGetTransferStatus = vi.fn()
const mockCreateMetadataSetUuid = vi.fn()
const mockGetFilesystemChildren = vi.fn()

vi.mock('@/shared/http/api', () => ({
  getProcessingConfigurations: (...args: unknown[]) => mockGetProcessingConfigurations(...args),
  createTransferPackage: (...args: unknown[]) => mockCreateTransferPackage(...args),
}))

vi.mock('@/shared/http/transfer', () => ({
  getSourceLocations: (...args: unknown[]) => mockGetSourceLocations(...args),
  getTransferStatus: (...args: unknown[]) => mockGetTransferStatus(...args),
  createMetadataSetUuid: (...args: unknown[]) => mockCreateMetadataSetUuid(...args),
}))

vi.mock('@/shared/http/filesystem', () => ({
  getFilesystemChildren: (...args: unknown[]) => mockGetFilesystemChildren(...args),
}))

const mockWindowOpen = vi.fn()

describe('useTransferBrowser', () => {
  beforeEach(() => {
    mockGetProcessingConfigurations.mockReset()
    mockCreateTransferPackage.mockReset()
    mockGetSourceLocations.mockReset()
    mockGetTransferStatus.mockReset()
    mockCreateMetadataSetUuid.mockReset()
    mockGetFilesystemChildren.mockReset()
    mockWindowOpen.mockReset()
    vi.spyOn(window, 'open').mockImplementation(mockWindowOpen)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  describe('getProcessingConfigs', () => {
    it('maps processing configuration names to ProcessingConfig objects', async () => {
      mockGetProcessingConfigurations.mockResolvedValueOnce({
        processing_configurations: ['Default', 'Automated'],
      })

      const { getProcessingConfigs } = useTransferBrowser()
      const result = await getProcessingConfigs()

      expect(result).toEqual([
        { pk: 'Default', name: 'Default' },
        { pk: 'Automated', name: 'Automated' },
      ])
    })

    it('sets error when fetching processing configurations fails', async () => {
      mockGetProcessingConfigurations.mockRejectedValueOnce(
        new Error('Failed to fetch processing configurations'),
      )

      const { getProcessingConfigs, error } = useTransferBrowser()

      await expect(getProcessingConfigs()).rejects.toThrow('Failed to fetch processing configurations')
      expect(error.value).toBe('Failed to fetch processing configurations')
    })
  })

  describe('getSourceLocations', () => {
    it('filters enabled transfer source locations', async () => {
      mockGetSourceLocations.mockResolvedValueOnce({
        objects: [
          { uuid: '1', description: 'Location 1', enabled: true, purpose: 'TS' },
          { uuid: '2', description: 'Location 2', enabled: false, purpose: 'TS' },
          { uuid: '3', description: 'Location 3', enabled: true, purpose: 'AS' },
          { uuid: '4', description: 'Location 4', enabled: true, purpose: 'TS' },
        ],
      })

      const { getSourceLocations } = useTransferBrowser()
      const result = await getSourceLocations()

      expect(result).toEqual([
        { uuid: '1', description: 'Location 1', enabled: true, purpose: 'TS' },
        { uuid: '4', description: 'Location 4', enabled: true, purpose: 'TS' },
      ])
    })

    it('throws when response is not an array of locations', async () => {
      mockGetSourceLocations.mockResolvedValueOnce({ objects: 'nope' })

      const { getSourceLocations, error } = useTransferBrowser()

      await expect(getSourceLocations()).rejects.toThrow('Failed to fetch source locations')
      expect(error.value).toBe('Failed to fetch source locations')
    })
  })

  describe('browseLocation', () => {
    it('decodes base64 entries and returns file nodes', async () => {
      const entries = [encodeBase64('folder1'), encodeBase64('file1.txt')]
      const directories = [encodeBase64('folder1')]
      mockGetFilesystemChildren.mockResolvedValueOnce({
        entries,
        directories,
        properties: {
          [encodeBase64('file1.txt')]: { size: 1024 },
        },
      })

      const { browseLocation } = useTransferBrowser()
      const result = await browseLocation('location-uuid')

      expect(mockGetFilesystemChildren).toHaveBeenCalledWith('location-uuid', undefined)
      expect(result).toEqual([
        {
          name: 'folder1',
          path: 'folder1',
          type: 'directory',
          size: undefined,
          modified: undefined,
          display_string: undefined,
          children: [],
          children_fetched: false,
          loading: false,
        },
        {
          name: 'file1.txt',
          path: 'file1.txt',
          type: 'file',
          size: 1024,
          modified: undefined,
          display_string: undefined,
          children: undefined,
          children_fetched: false,
          loading: false,
        },
      ])
    })

    it('encodes the path when browsing subdirectories', async () => {
      mockGetFilesystemChildren.mockResolvedValueOnce({ entries: [], directories: [], properties: {} })

      const { browseLocation } = useTransferBrowser()
      await browseLocation('location-uuid', '/some/path')

      expect(mockGetFilesystemChildren).toHaveBeenCalledWith(
        'location-uuid',
        encodeBase64('/some/path'),
      )
    })
  })

  describe('createTransfer', () => {
    it('submits one transfer request per component', async () => {
      mockCreateTransferPackage.mockResolvedValueOnce({
        uuid: 'transfer-uuid',
        name: 'Test Transfer',
        status: 'processing',
      })

      const { createTransfer } = useTransferBrowser()
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

      expect(mockCreateTransferPackage).toHaveBeenCalledWith({
        name: 'Test Transfer',
        type: 'standard',
        accession: 'ACC-001',
        access_system_id: 'SYS-001',
        processing_config: 'config-1',
        auto_approve: false,
        path: encodeBase64('loc-uuid:/test/path'),
        metadata_set_id: 'metadata-1',
      })

      expect(result).toEqual({
        uuid: 'transfer-uuid',
        name: 'Test Transfer',
        status: 'processing',
      })
    })

    it('throws when no components are provided', async () => {
      const { createTransfer, error } = useTransferBrowser()

      await expect(
        createTransfer({
          name: 'Test Transfer',
          type: 'standard',
          accession: 'ACC-001',
          accessSystemId: 'SYS-001',
          processingConfig: 'config-1',
          autoApprove: false,
          components: [],
        }),
      ).rejects.toThrow('Transfer requires at least one component')

      expect(error.value).toBe('Transfer requires at least one component')
    })

    it('omits metadata_set_id when component lacks UUID', async () => {
      mockCreateTransferPackage.mockResolvedValueOnce({
        uuid: 'transfer-uuid',
        name: 'Test Transfer',
        status: 'processing',
      })

      const { createTransfer } = useTransferBrowser()
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

      expect(mockCreateTransferPackage).toHaveBeenCalledWith({
        name: 'Test Transfer',
        type: 'standard',
        accession: 'ACC-001',
        access_system_id: 'SYS-001',
        processing_config: 'config-1',
        auto_approve: false,
        path: encodeBase64('loc-uuid:/test/path'),
        metadata_set_id: '',
      })
    })
  })

  describe('loading state', () => {
    it('tracks pending requests', async () => {
      let resolvePromise!: (value: unknown) => void
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockGetProcessingConfigurations.mockReturnValueOnce(pendingPromise)

      const { getProcessingConfigs, loading } = useTransferBrowser()

      expect(loading.value).toBe(false)
      const promise = getProcessingConfigs()
      expect(loading.value).toBe(true)

      resolvePromise?.({ processing_configurations: ['default'] })
      await promise

      expect(loading.value).toBe(false)
    })
  })

  describe('component editor', () => {
    it('opens edit page for disk image components with existing UUID', async () => {
      const { openComponentEditor } = useTransferBrowser()

      const component: TransferComponent = {
        id: 'component-1',
        path: '/test/path',
        location: 'location-1',
        uuid: 'existing-uuid-123',
      }

      await openComponentEditor(component, 'disk image')

      expect(mockWindowOpen).toHaveBeenCalledWith(
        '/transfer/component/existing-uuid-123',
        '_blank',
      )
      expect(mockCreateMetadataSetUuid).not.toHaveBeenCalled()
    })

    it('creates UUID and opens edit page for disk image components without UUID', async () => {
      mockCreateMetadataSetUuid.mockResolvedValueOnce('test-uuid-123')

      const { openComponentEditor } = useTransferBrowser()

      const component: TransferComponent = {
        id: 'component-1',
        path: '/test/path',
        location: 'location-1',
      }

      await openComponentEditor(component, 'disk image')

      expect(mockCreateMetadataSetUuid).toHaveBeenCalled()
      expect(mockWindowOpen).toHaveBeenCalledWith('/transfer/component/test-uuid-123', '_blank')
      expect(component.uuid).toBe('test-uuid-123')
    })

    it('rejects editing for non-disk-image transfers', async () => {
      const { openComponentEditor } = useTransferBrowser()

      const component: TransferComponent = {
        id: 'component-1',
        path: '/test/path',
        location: 'location-1',
      }

      await expect(openComponentEditor(component, 'standard')).rejects.toThrow(
        'Edit functionality is only available for disk image transfers',
      )
      expect(mockWindowOpen).not.toHaveBeenCalled()
      expect(mockCreateMetadataSetUuid).not.toHaveBeenCalled()
    })
  })

  describe('transfer helpers', () => {
    it('returns transfer edit eligibility', () => {
      const { canEditComponents } = useTransferBrowser()
      expect(canEditComponents('disk image')).toBe(true)
      expect(canEditComponents('standard')).toBe(false)
    })

    it('builds component edit URLs', () => {
      const { getComponentEditUrl } = useTransferBrowser()
      expect(getComponentEditUrl('test-uuid')).toBe('/transfer/component/test-uuid')
    })
  })
})

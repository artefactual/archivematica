import { ref, computed } from 'vue'
import type {
  ProcessingConfig,
  TransferFormData,
  TransferComponent,
  FileNode,
} from '@/browser/types'
import type { SourceLocation } from '@/shared/http/transfer'
import { encodeBase64, decodeBase64 } from '@/shared/encoding/base64'
import type { Base64String } from '@/shared/encoding/base64'
import { toHttpErrorInfo } from '@/shared/http'
import { getFilesystemChildren } from '@/shared/http/filesystem'
import {
  getProcessingConfigurations,
  createTransferPackage,
  type TransferCreatePayload,
  type TransferCreateResponse,
} from '@/shared/http/api'
import {
  getSourceLocations as fetchSourceLocations,
  getTransferStatus,
  createMetadataSetUuid,
} from '@/shared/http/transfer'
import type { FilesystemBrowseResponse } from '@/shared/http/filesystem'

interface BrowseResponse {
  entries: string[]
  directories: string[]
  properties?: Record<
    string,
    {
      size?: number
      modified?: string
      display_string?: string
      [key: string]: unknown
    }
  >
  [key: string]: unknown
}

const getErrorMessage = (err: unknown): string => {
  if (err instanceof Error) {
    const info = toHttpErrorInfo(err)
    if (info) {
      if (info.bodyJson && typeof info.bodyJson === 'object') {
        const message = (info.bodyJson as { message?: unknown }).message
        if (typeof message === 'string' && message.trim()) {
          return message
        }
      }
      if (typeof info.bodyText === 'string' && info.bodyText.trim()) {
        return info.bodyText
      }
    }
    return err.message || 'An error occurred'
  }
  return 'An error occurred'
}

export function useTransferBrowser() {
  const pendingRequests = ref(0)
  const error = ref<string | null>(null)
  const loading = computed(() => pendingRequests.value > 0)

  const runWithPending = async <T>(operation: () => Promise<T>): Promise<T> => {
    pendingRequests.value += 1
    error.value = null

    try {
      return await operation()
    } catch (err) {
      if (error.value === null) {
        error.value = getErrorMessage(err)
      }
      throw err
    } finally {
      pendingRequests.value = Math.max(0, pendingRequests.value - 1)
    }
  }

  const getProcessingConfigs = async (): Promise<ProcessingConfig[]> => {
    return runWithPending(async () => {
      const data = await getProcessingConfigurations()
      return data.processing_configurations.map((configName: string) => ({
        pk: configName,
        name: configName,
      }))
    })
  }

  const getSourceLocations = async (): Promise<SourceLocation[]> => {
    return runWithPending(async () => {
      const data = await fetchSourceLocations()
      const locations
        = (data as { objects?: SourceLocation[] }).objects
          ?? (data as { results?: SourceLocation[] }).results
          ?? data

      if (!Array.isArray(locations)) {
        throw new Error('Failed to fetch source locations')
      }

      return locations.filter(
        (location: SourceLocation) => location.enabled && location.purpose === 'TS',
      )
    })
  }

  const browseLocation = async (locationUuid: string, path: string = ''): Promise<FileNode[]> => {
    return runWithPending(async () => {
      const encodedPath = path ? encodeBase64(path) : undefined
      const data = await getFilesystemChildren(locationUuid, encodedPath)
      const decodedData = decodeBrowseResponse(data)
      return formatEntriesAsFileNodes(decodedData, path)
    })
  }

  const decodeBrowseResponse = (response: FilesystemBrowseResponse): BrowseResponse => {
    const newResponse: BrowseResponse = {
      ...response,
      entries: [],
      directories: [],
    }

    const listKeys: Array<'entries' | 'directories'> = ['entries', 'directories']
    for (const key of listKeys) {
      const encodedList = response[key]
      if (Array.isArray(encodedList)) {
        newResponse[key] = encodedList.map(encoded => decodeBase64(encoded))
      }
    }

    if (response.properties) {
      newResponse.properties = {}
      for (const [key, propertyValue] of Object.entries(response.properties)) {
        if (propertyValue !== undefined) {
          newResponse.properties[decodeBase64(key as Base64String)] = propertyValue
        }
      }
    }

    return newResponse
  }

  const formatEntriesAsFileNodes = (data: BrowseResponse, parentPath: string): FileNode[] => {
    if (!data.entries || !Array.isArray(data.entries)) {
      return []
    }

    const directories: FileNode[] = []
    const files: FileNode[] = []

    for (const entry of data.entries) {
      const isDirectory = data.directories?.includes(entry) ?? false
      const fullPath = parentPath ? `${parentPath.replace(/\/$/, '')}/${entry}` : entry
      const properties = data.properties?.[entry] ?? null

      const node: FileNode = {
        name: entry,
        path: fullPath,
        type: isDirectory ? 'directory' : 'file',
        size: properties?.size,
        modified: properties?.modified,
        display_string: properties?.display_string,
        children: isDirectory ? [] : undefined,
        children_fetched: false,
        loading: false,
      }

      if (isDirectory) {
        directories.push(node)
      } else {
        files.push(node)
      }
    }

    return [...directories, ...files]
  }

  const createTransfer = async (
    data: TransferFormData & { components: TransferComponent[] },
  ): Promise<TransferCreateResponse> => {
    return runWithPending(async () => {
      if (data.components.length === 0) {
        throw new Error('Transfer requires at least one component')
      }

      const requests = data.components.map((component) => {
        const fullPath = `${component.location}:${component.path}`
        const encodedPath = encodeBase64(fullPath)

        const payload: TransferCreatePayload = {
          name: data.name,
          type: data.type,
          accession: data.accession,
          access_system_id: data.accessSystemId,
          processing_config: data.processingConfig,
          auto_approve: data.autoApprove,
          path: encodedPath,
          metadata_set_id: component.uuid || '',
        }

        return createTransferPackage(payload)
      })

      const responses = await Promise.all(requests)
      const [firstResponse] = responses
      if (!firstResponse) {
        throw new Error('Transfer request produced no response')
      }
      return firstResponse
    })
  }

  const fetchTransferStatus = async (uuid: string): Promise<Record<string, unknown>> => {
    return runWithPending(async () => {
      return getTransferStatus(uuid)
    })
  }

  const openComponentEditor = async (
    component: TransferComponent,
    transferType: string,
  ): Promise<void> => {
    return runWithPending(async () => {
      if (transferType !== 'disk image') {
        const errorMsg = 'Edit functionality is only available for disk image transfers'
        error.value = errorMsg
        throw new Error(errorMsg)
      }

      let componentUuid = component.uuid
      if (!componentUuid) {
        componentUuid = await createMetadataSetUuid()
        component.uuid = componentUuid
      }

      window.open(`/transfer/component/${componentUuid}`, '_blank')
    })
  }

  const canEditComponents = (transferType: string): boolean => {
    return transferType === 'disk image'
  }

  const getComponentEditUrl = (componentUuid: string): string => {
    return `/transfer/component/${componentUuid}`
  }

  return {
    loading,
    error: computed(() => error.value),
    getProcessingConfigs,
    getSourceLocations,
    browseLocation,
    createTransfer,
    getTransferStatus: fetchTransferStatus,
    createMetadataSetUuid,
    openComponentEditor,
    canEditComponents,
    getComponentEditUrl,
  }
}

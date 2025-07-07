import { ref, computed } from 'vue'
import * as Base64 from 'base64-helpers'
import type {
  ProcessingConfig,
  SourceLocation,
  TransferFormData,
  TransferComponent,
  FileNode,
} from '@/shared/models'
import { useCSRFToken } from '@/browser/composables/useCSRFToken'

interface TransferCreateResponse {
  uuid: string
  name: string
  status: string
  message?: string
}

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

export function useTransferAPI() {
  const pendingRequests = ref(0)
  const error = ref<string | null>(null)
  const csrfToken = useCSRFToken()
  const loading = computed(() => pendingRequests.value > 0)

  const runWithPending = async <T>(operation: () => Promise<T>): Promise<T> => {
    pendingRequests.value += 1
    error.value = null

    try {
      return await operation()
    } catch (err) {
      if (error.value === null) {
        error.value = err instanceof Error ? err.message : 'An error occurred'
      }
      throw err
    } finally {
      pendingRequests.value = Math.max(0, pendingRequests.value - 1)
    }
  }

  const fetchWithCsrf = async (url: string, options: RequestInit = {}): Promise<Response> => {
    const token = csrfToken.getToken()

    const headers = new Headers(options.headers || {})
    if (token) {
      headers.set('X-CSRFToken', token)
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'same-origin',
    })

    return response
  }

  const getProcessingConfigs = async (): Promise<ProcessingConfig[]> => {
    return runWithPending(async () => {
      const response = await fetchWithCsrf('/api/processing-configurations/')
      if (!response.ok) {
        throw new Error('Failed to fetch processing configurations')
      }

      const data = await response.json()
      // API returns array of strings like: {"processing_configurations": ["automated", "default"]}.
      return data.processing_configurations.map((configName: string) => ({
        pk: configName,
        name: configName,
      }))
    })
  }

  const getSourceLocations = async (): Promise<SourceLocation[]> => {
    return runWithPending(async () => {
      const response = await fetchWithCsrf('/transfer/locations/')
      if (!response.ok) {
        throw new Error('Failed to fetch source locations')
      }

      const data = await response.json()

      // Handle different possible response structures for compatibility.
      const locations = data.objects || data.results || data || []

      if (!Array.isArray(locations)) {
        // Expected array of locations, got invalid response.
        return []
      }

      return locations.filter(
        (location: SourceLocation) => location.enabled && location.purpose === 'TS',
      )
    })
  }

  const browseLocation = async (locationUuid: string, path: string = ''): Promise<FileNode[]> => {
    return runWithPending(async () => {
      // For the root directory, we need to pass an empty path.
      // For subdirectories, we need to encode the path.
      let url = `/filesystem/children/location/${locationUuid}/`

      if (path) {
        // Use Base64.encode to align with API expectations.
        const encodedPath = Base64.encode(path)
        url += `?path=${encodedPath}`
      }

      const response = await fetchWithCsrf(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to browse location')
      }

      const data = await response.json()

      // The API returns base64-encoded keys that need to be decoded.
      const decodedData = decodeBrowseResponse(data)
      const nodes = formatEntriesAsFileNodes(decodedData, path)
      return nodes
    })
  }

  const decodeBrowseResponse = (response: BrowseResponse) => {
    const newResponse: BrowseResponse = { ...response }

    const listKeys: Array<'entries' | 'directories'> = ['entries', 'directories']
    for (const key of listKeys) {
      const encodedList = response[key]
      if (Array.isArray(encodedList)) {
        newResponse[key] = encodedList.map((encoded: string) => Base64.decode(encoded))
      }
    }

    if (response.properties) {
      newResponse.properties = {}
      for (const key of Object.keys(response.properties)) {
        const propertyValue = response.properties[key]
        if (propertyValue !== undefined) {
          newResponse.properties[Base64.decode(key)] = propertyValue
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
      // Ensure we don't have double slashes in paths.
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
      }

      if (isDirectory) {
        directories.push(node)
      } else {
        files.push(node)
      }
    }

    // Return directories first, then files for better organization.
    return [...directories, ...files]
  }

  const createMetadataSetUuid = async (): Promise<string> => {
    return runWithPending(async () => {
      const response = await fetchWithCsrf('/transfer/create_metadata_set_uuid/', {
        method: 'GET',
      })

      if (!response.ok) {
        throw new Error('Failed to create metadata set UUID')
      }

      const data = await response.json()
      return data.uuid
    })
  }

  const createTransfer = async (
    data: TransferFormData & { components: TransferComponent[] },
  ): Promise<TransferCreateResponse> => {
    return runWithPending(async () => {
      // Submit one request per component as required by the API.
      const requests = data.components.map((component) => {
        const fullPath = `${component.location}:${component.path}`
        const encodedPath = Base64.encode(fullPath)

        const payload = {
          name: data.name,
          type: data.type,
          accession: data.accession,
          access_system_id: data.accessSystemId,
          processing_config: data.processingConfig,
          auto_approve: data.autoApprove,
          path: encodedPath,
          metadata_set_id: component.uuid || '',
        }

        return fetchWithCsrf('/api/v2beta/package/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
          },
          body: JSON.stringify(payload),
        })
      })

      if (requests.length === 0) {
        throw new Error('Transfer requires at least one component')
      }

      // Execute all requests in parallel.
      const responses = await Promise.all(requests)

      // Check if all requests were successful.
      for (const response of responses) {
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.message || 'Failed to create transfer')
        }
      }

      // Return the response from the first request.
      const [firstResponse] = responses
      if (!firstResponse) {
        throw new Error('Transfer request produced no response')
      }
      return firstResponse.json()
    })
  }

  const getTransferStatus = async (uuid: string): Promise<Record<string, unknown>> => {
    return runWithPending(async () => {
      const response = await fetchWithCsrf(`/transfer/status/${uuid}/`)
      if (!response.ok) {
        throw new Error('Failed to get transfer status')
      }
      return response.json()
    })
  }

  const openComponentEditor = async (
    component: TransferComponent,
    transferType: string,
  ): Promise<void> => {
    return runWithPending(async () => {
      // Only allow editing for disk image transfers.
      if (transferType !== 'disk image') {
        const errorMsg = 'Edit functionality is only available for disk image transfers'
        error.value = errorMsg
        throw new Error(errorMsg)
      }

      // Generate UUID for component if it doesn't have one.
      let componentUuid = component.uuid
      if (!componentUuid) {
        componentUuid = await createMetadataSetUuid()

        // Update the component with the UUID.
        component.uuid = componentUuid
      }

      // Open edit page in a new tab for operator convenience.
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
    // State exports.
    loading,
    error: computed(() => error.value),

    // Method exports.
    getProcessingConfigs,
    getSourceLocations,
    browseLocation,
    createTransfer,
    getTransferStatus,
    createMetadataSetUuid,
    openComponentEditor,
    canEditComponents,
    getComponentEditUrl,
  }
}

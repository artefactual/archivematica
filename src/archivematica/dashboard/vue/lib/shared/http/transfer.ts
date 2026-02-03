import { createHttpClient } from './client'
import type { JsonIfChangedResult } from './client'
import type { ProcessingStatusesResponse } from './processing'

export type SourceLocationPurpose = 'AR' | 'AS' | 'CP' | 'DS' | 'SD' | 'SS' | 'BL' | 'TS' | 'RP'

export interface SourceLocation {
  uuid: string
  description: string | null
  enabled: boolean
  path: string
  purpose: SourceLocationPurpose
  relative_path: string
  space: string
  pipeline?: string[]
  resource_uri?: string
  used: number
  quota: number | null
}

export type TransferLocationsResponse = SourceLocation[]
export type TransferStatusResponse = ProcessingStatusesResponse
export type TransferStatusesResponse = ProcessingStatusesResponse
export type TransferStatusesIfChangedResponse = JsonIfChangedResult<TransferStatusesResponse>
export type TransferStatusesIfChangedOptions = {
  previousRaw?: string
}

const client = createHttpClient()
const SOURCE_LOCATION_PURPOSES: SourceLocationPurpose[] = ['AR', 'AS', 'CP', 'DS', 'SD', 'SS', 'BL', 'TS', 'RP']

const isStringArray = (value: unknown): value is string[] => {
  return Array.isArray(value) && value.every(item => typeof item === 'string')
}

const isSourceLocationPurpose = (value: string): value is SourceLocationPurpose => {
  return SOURCE_LOCATION_PURPOSES.includes(value as SourceLocationPurpose)
}

const parseSourceLocation = (value: unknown): SourceLocation => {
  if (!value || typeof value !== 'object') {
    throw new Error('Expected each source location to be an object.')
  }
  const obj = value as Record<string, unknown>
  const {
    uuid,
    description,
    enabled,
    path,
    purpose,
    relative_path: relativePath,
    space,
    pipeline,
    resource_uri: resourceUri,
    used,
    quota,
  } = obj

  if (typeof uuid !== 'string') throw new Error('Expected source location "uuid" to be a string.')
  if (!(typeof description === 'string' || description === null)) {
    throw new Error('Expected source location "description" to be a string or null.')
  }
  if (typeof enabled !== 'boolean') throw new Error('Expected source location "enabled" to be a boolean.')
  if (typeof path !== 'string') throw new Error('Expected source location "path" to be a string.')
  if (typeof purpose !== 'string') throw new Error('Expected source location "purpose" to be a string.')
  if (!isSourceLocationPurpose(purpose)) {
    throw new Error('Expected source location "purpose" to be a valid location purpose code.')
  }
  if (typeof relativePath !== 'string') {
    throw new Error('Expected source location "relative_path" to be a string.')
  }
  if (typeof space !== 'string') throw new Error('Expected source location "space" to be a string.')
  if (!(pipeline === undefined || isStringArray(pipeline))) {
    throw new Error('Expected source location "pipeline" to be a string array when provided.')
  }
  if (!(resourceUri === undefined || typeof resourceUri === 'string')) {
    throw new Error('Expected source location "resource_uri" to be a string when provided.')
  }
  if (typeof used !== 'number') throw new Error('Expected source location "used" to be a number.')
  if (!(typeof quota === 'number' || quota === null)) {
    throw new Error('Expected source location "quota" to be a number or null.')
  }

  return {
    uuid,
    description,
    enabled,
    path,
    purpose,
    relative_path: relativePath,
    space,
    pipeline,
    resource_uri: resourceUri,
    used,
    quota,
  }
}

const parseSourceLocations = (data: unknown): TransferLocationsResponse => {
  if (Array.isArray(data)) {
    return data.map(parseSourceLocation)
  }
  if (data && typeof data === 'object') {
    const obj = data as { objects?: unknown, results?: unknown }
    const wrapped = obj.objects ?? obj.results
    if (Array.isArray(wrapped)) {
      return wrapped.map(parseSourceLocation)
    }
  }
  throw new Error('Expected source locations response to be an array or wrapped array.')
}

export const getSourceLocations = async (): Promise<TransferLocationsResponse> => {
  const data = await client.getJson<unknown>('/transfer/locations/', {
    strictJson: true,
  })
  return parseSourceLocations(data)
}

export const getTransferStatus = async (uuid: string): Promise<TransferStatusResponse> => {
  return client.getJson<TransferStatusResponse>(`/transfer/status/${uuid}/`, {
    cacheBust: true,
    strictJson: true,
  })
}

export function getTransferStatuses(
  options: TransferStatusesIfChangedOptions,
): Promise<TransferStatusesIfChangedResponse>
export function getTransferStatuses(): Promise<TransferStatusesResponse>
export function getTransferStatuses(
  options?: TransferStatusesIfChangedOptions,
): Promise<TransferStatusesResponse | TransferStatusesIfChangedResponse> {
  if (options === undefined) {
    return client.getJson<TransferStatusesResponse>('/transfer/status/', {
      cacheBust: true,
      strictJson: true,
    })
  }

  return client.getJsonIfChanged<TransferStatusesResponse>('/transfer/status/', {
    cacheBust: true,
    strictJson: true,
    previousRaw: options.previousRaw,
  })
}

export const createMetadataSetUuid = async (): Promise<string> => {
  const data = await client.getJson<{ uuid: string }>('/transfer/create_metadata_set_uuid/', {
    strictJson: true,
  })
  return data.uuid
}

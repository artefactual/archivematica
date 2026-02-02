import { createHttpClient } from './client'

export interface SourceLocation {
  uuid: string
  description: string
  enabled: boolean
  path: string
  purpose: string
  relative_path: string
  space: string
  used: number
  quota: number | null
}

export type TransferLocationsResponse
  = | SourceLocation[]
    | {
      objects?: SourceLocation[]
      results?: SourceLocation[]
      [key: string]: unknown
    }

export type TransferStatusResponse = Record<string, unknown>

const client = createHttpClient()

export const getSourceLocations = async (): Promise<TransferLocationsResponse> => {
  return client.getJson<TransferLocationsResponse>('/transfer/locations/', {
    strictJson: true,
  })
}

export const getTransferStatus = async (uuid: string): Promise<TransferStatusResponse> => {
  return client.getJson<TransferStatusResponse>(`/transfer/status/${uuid}/`, {
    strictJson: true,
  })
}

export const createMetadataSetUuid = async (): Promise<string> => {
  const data = await client.getJson<{ uuid: string }>('/transfer/create_metadata_set_uuid/', {
    strictJson: true,
  })
  return data.uuid
}

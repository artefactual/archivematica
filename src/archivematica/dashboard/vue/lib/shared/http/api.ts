import { createHttpClient } from './client'
import type { Base64String } from '@/shared/encoding/base64'

export type ProcessingConfigurationsResponse = {
  processing_configurations: string[]
}

export type TransferCreatePayload = {
  name: string
  type: string
  accession: string
  access_system_id: string
  processing_config: string
  auto_approve: boolean
  path: Base64String
  metadata_set_id: string
}

export type TransferCreateResponse = {
  id: string
}

const client = createHttpClient()

const parseTransferCreateResponse = (data: unknown): TransferCreateResponse => {
  if (!data || typeof data !== 'object' || !('id' in data)) {
    throw new Error('Expected "id" field in transfer package create response.')
  }
  const id = (data as { id: unknown }).id
  if (typeof id !== 'string') {
    throw new Error('Expected transfer package create response "id" to be a string.')
  }
  return { id }
}

export const getProcessingConfigurations = async (): Promise<ProcessingConfigurationsResponse> => {
  return client.getJson<ProcessingConfigurationsResponse>('/api/processing-configuration/', {
    strictJson: true,
  })
}

export const createTransferPackage = async (
  payload: TransferCreatePayload,
): Promise<TransferCreateResponse> => {
  const data = await client.requestJson<unknown>('/api/v2beta/package/', {
    method: 'POST',
    json: payload,
    strictJson: true,
  })
  return parseTransferCreateResponse(data)
}

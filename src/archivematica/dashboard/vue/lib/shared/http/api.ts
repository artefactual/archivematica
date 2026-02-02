import { createHttpClient } from './client'

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
  path: string
  metadata_set_id: string
}

export type TransferCreateResponse = {
  uuid: string
  name: string
  status: string
  message?: string
}

const client = createHttpClient()

export const getProcessingConfigurations = async (): Promise<ProcessingConfigurationsResponse> => {
  return client.getJson<ProcessingConfigurationsResponse>('/api/processing-configuration/', {
    strictJson: true,
  })
}

export const createTransferPackage = async (
  payload: TransferCreatePayload,
): Promise<TransferCreateResponse> => {
  return client.requestJson<TransferCreateResponse>('/api/v2beta/package/', {
    method: 'POST',
    json: payload,
    strictJson: true,
  })
}

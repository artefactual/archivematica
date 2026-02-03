import { createHttpClient, createUrl } from './client'
import type { JsonIfChangedResult } from './client'
import type { ProcessingStatusesResponse } from './processing'

export type IngestStatusResponse = ProcessingStatusesResponse
export type IngestStatusesIfChangedResponse = JsonIfChangedResult<IngestStatusResponse>
export type IngestPreviewType = 'aip' | 'normalization' | 'dip'
export type IngestStatusesIfChangedOptions = {
  previousRaw?: string
}

export type IngestUploadTargetResponse = {
  target: string
}

export type IngestUploadReadyResponse = {
  ready: boolean
}

const client = createHttpClient()

export function getIngestStatuses(
  options: IngestStatusesIfChangedOptions,
): Promise<IngestStatusesIfChangedResponse>
export function getIngestStatuses(): Promise<IngestStatusResponse>
export function getIngestStatuses(
  options?: IngestStatusesIfChangedOptions,
): Promise<IngestStatusResponse | IngestStatusesIfChangedResponse> {
  if (options === undefined) {
    return client.getJson<IngestStatusResponse>('/ingest/status/', {
      cacheBust: true,
      strictJson: true,
    })
  }

  return client.getJsonIfChanged<IngestStatusResponse>('/ingest/status/', {
    cacheBust: true,
    strictJson: true,
    previousRaw: options.previousRaw,
  })
}

export const getIngestStatus = async (uuid: string): Promise<IngestStatusResponse> => {
  return client.getJson<IngestStatusResponse>(`/ingest/status/${uuid}/`, {
    cacheBust: true,
    strictJson: true,
  })
}

export const getUploadTarget = async (sipUuid: string): Promise<IngestUploadTargetResponse> => {
  return client.getJson<IngestUploadTargetResponse>(`/ingest/${sipUuid}/upload/`, {
    strictJson: true,
  })
}

export const setUploadTarget = async (
  sipUuid: string,
  target: string,
): Promise<IngestUploadReadyResponse> => {
  const body = new URLSearchParams()
  body.set('target', target)

  return client.requestJson<IngestUploadReadyResponse>(`/ingest/${sipUuid}/upload/`, {
    method: 'POST',
    body: body.toString(),
    strictJson: true,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    },
  })
}

export const checkUploadDestinationStatusCode = async (target: string): Promise<number> => {
  const raw = await client.getText('/ingest/upload/url/check/', {
    query: { target },
  })
  const statusCode = Number.parseInt(raw, 10)
  if (Number.isNaN(statusCode)) {
    throw new Error('Expected numeric HTTP status code response from /ingest/upload/url/check/.')
  }
  return statusCode
}

export const getIngestNormalizationReportUrl = (sipUuid: string): string => {
  return createUrl(`/ingest/normalization-report/${sipUuid}/`)
}

export const getIngestUploadAsUrl = (sipUuid: string): string => {
  return createUrl(`/ingest/${sipUuid}/upload/as/`)
}

export const getIngestPreviewUrl = (previewType: IngestPreviewType, jobUuid: string): string => {
  return createUrl(`/ingest/preview/${previewType}/${jobUuid}/`)
}

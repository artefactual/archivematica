import { HttpError, createHttpClient, createUrl } from './client'
import type { JsonIfChangedResult } from './client'
import type {
  ProcessingJobGroupsResponse,
  ProcessingUnitSummariesResponse,
} from './processing'

export type IngestPreviewType = 'aip' | 'normalization' | 'dip'
export type IngestSummariesIfChangedOptions = {
  previousRaw?: string
}
export type IngestSummariesIfChangedResponse = JsonIfChangedResult<ProcessingUnitSummariesResponse>

export type IngestUploadTargetResponse = {
  target: string
}

export type IngestUploadReadyResponse = {
  ready: boolean
}

export type IngestAsMatcherPairRequest = {
  dipUuid: string
  resourceId: string
  fileUuid: string
}

export type IngestAsMatcherPairResult = 'created' | 'duplicate'

const client = createHttpClient()

export const getIngestSummaries = (
  options: IngestSummariesIfChangedOptions,
): Promise<IngestSummariesIfChangedResponse> => {
  return client.getJsonIfChanged<ProcessingUnitSummariesResponse>('/ingest/status/', {
    cacheBust: true,
    strictJson: true,
    previousRaw: options.previousRaw,
  })
}

export const getIngestJobGroups = async (
  uuid: string,
): Promise<ProcessingJobGroupsResponse> => {
  return client.getJson<ProcessingJobGroupsResponse>(
    `/ingest/${uuid}/job-groups/`,
    { cacheBust: true, strictJson: true },
  )
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

export const getIngestUploadAsMatchUrl = (sipUuid: string): string => {
  return createUrl(`/ingest/${sipUuid}/upload/as/match/`)
}

export const getIngestUploadAsResetUrl = (sipUuid: string): string => {
  return createUrl(`/ingest/${sipUuid}/upload/as/reset/`)
}

export const getIngestUploadAsReviewMatchesUrl = (sipUuid: string): string => {
  return createUrl(`/ingest/${sipUuid}/upload/as/review/`)
}

// Preserve the legacy matcher contract: 201 creates a pairing, 409 means the
// file was already paired, and other failures surface as errors.
export const createArchivesSpacePair = async ({
  dipUuid,
  resourceId,
  fileUuid,
}: IngestAsMatcherPairRequest): Promise<IngestAsMatcherPairResult> => {
  const matchUrl = getIngestUploadAsMatchUrl(dipUuid)
  try {
    await client.requestText(matchUrl, {
      method: 'POST',
      json: {
        resource_id: resourceId,
        file_uuid: fileUuid,
      },
    })
    return 'created'
  } catch (error) {
    if (error instanceof HttpError && error.status === 409) {
      return 'duplicate'
    }
    throw error
  }
}

export const deleteArchivesSpacePair = async ({
  dipUuid,
  resourceId,
  fileUuid,
}: IngestAsMatcherPairRequest): Promise<void> => {
  const matchUrl = getIngestUploadAsMatchUrl(dipUuid)
  await client.requestText(matchUrl, {
    method: 'DELETE',
    json: {
      resource_id: resourceId,
      file_uuid: fileUuid,
    },
  })
}

export const getIngestPreviewUrl = (previewType: IngestPreviewType, jobUuid: string): string => {
  return createUrl(`/ingest/preview/${previewType}/${jobUuid}/`)
}

import { HttpError, createHttpClient } from './client'
import { getIngestUploadAsMatchUrl } from './ingest'

const client = createHttpClient()

export type AsMatcherPairRequest = {
  dipUuid: string
  resourceId: string
  fileUuid: string
}

export type AsMatcherPairResult = 'created' | 'duplicate'

// Preserve the legacy matcher contract: 201 creates a pairing, 409 means the
// file was already paired, and other failures surface as errors.
export const createArchivesSpacePair = async ({
  dipUuid,
  resourceId,
  fileUuid,
}: AsMatcherPairRequest): Promise<AsMatcherPairResult> => {
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
}: AsMatcherPairRequest): Promise<void> => {
  const matchUrl = getIngestUploadAsMatchUrl(dipUuid)
  await client.requestText(matchUrl, {
    method: 'DELETE',
    json: {
      resource_id: resourceId,
      file_uuid: fileUuid,
    },
  })
}

import { createHttpClient, openDownload } from './client'
import type { RequestOptions } from './client'
import type { Base64String } from '@/shared/encoding/base64'

export type DirectoryEntry = {
  name: Base64String
  parent?: Base64String
  children?: DirectoryEntry[]
}

export type FilesystemBrowseResponse = {
  entries: Base64String[]
  directories: Base64String[]
  properties?: Record<Base64String, Record<string, unknown>>
}

export type CopyMetadataFilesResponse = {
  error?: string | boolean
  message?: string
}

const http = createHttpClient()

export const getFilesystemContents = async (
  path: string,
  requestOptions: Omit<RequestOptions, 'query'> = {},
): Promise<DirectoryEntry> => {
  return http.getJson<DirectoryEntry>('/filesystem/contents/', {
    query: { path },
    ...requestOptions,
  })
}

export const getFilesystemChildren = async (
  locationUUID: string,
  path?: Base64String,
): Promise<FilesystemBrowseResponse> => {
  return http.getJson<FilesystemBrowseResponse>(`/filesystem/children/location/${locationUUID}/`, {
    query: path ? { path } : undefined,
  })
}

export const copyMetadataFiles = async (
  sipUUID: string,
  sourcePaths: Base64String[],
): Promise<CopyMetadataFilesResponse> => {
  const body = new URLSearchParams()
  body.set('sip_uuid', sipUUID)
  for (const sourcePath of sourcePaths) {
    body.append('source_paths[]', sourcePath)
  }

  return http.requestJson<CopyMetadataFilesResponse>('/filesystem/copy_metadata_files/', {
    method: 'POST',
    body: body.toString(),
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    },
  })
}

export const openFilesystemDownload = (filepath: Base64String): void => {
  openDownload('/filesystem/download_fs/', { query: { filepath } })
}

import { createHttpClient, openDownload } from './client'

export type ArchivalStorageSearchResponse = {
  iTotalRecords: number
  iTotalDisplayRecords: number
  sEcho: number
  aaData: Array<Record<string, unknown>>
}

export type ArchivalStorageTableState = {
  columns?: Array<{ visible?: boolean }>
}

const client = createHttpClient()

export const createArchivalStorageSearchUrl = (params?: URLSearchParams): string => {
  const query = params?.toString() ?? ''
  return query ? `/archival-storage/search/?${query}` : '/archival-storage/search/'
}

export const createArchivalStorageAipUrl = (uuid: string): string => {
  return `/archival-storage/${uuid}/`
}

export const createArchivalStorageAipFileDownloadUrl = (fileUuid: string): string => {
  return `/archival-storage/download/aip/file/${fileUuid}/`
}

export const createArchivalStorageThumbnailUrl = (fileUuid: string): string => {
  return `/archival-storage/thumbnail/${fileUuid}/`
}

export const createArchivalStorageRawFileUrl = (documentIdNoHyphens: string): string => {
  return `/archival-storage/search/json/file/${documentIdNoHyphens}/`
}

export const searchArchivalStorage = async (
  params: URLSearchParams,
): Promise<ArchivalStorageSearchResponse> => {
  return client.getJson<ArchivalStorageSearchResponse>(createArchivalStorageSearchUrl(params), {
    strictJson: true,
  })
}

export const loadArchivalStorageState = async (
  tableName: string,
): Promise<ArchivalStorageTableState> => {
  return client.getJson<ArchivalStorageTableState>(`/archival-storage/load_state/${tableName}/`, {
    strictJson: true,
  })
}

export const saveArchivalStorageState = async (
  tableName: string,
  payload: ArchivalStorageTableState,
): Promise<{ success?: boolean }> => {
  return client.requestJson<{ success?: boolean }>(`/archival-storage/save_state/${tableName}/`, {
    method: 'POST',
    json: payload,
    strictJson: true,
  })
}

export const openArchivalStorageCsv = (params: URLSearchParams): void => {
  openDownload(createArchivalStorageSearchUrl(params))
}

export const createArchivalStorageAicUrl = (params: URLSearchParams): string => {
  return `/archival-storage/search/create_aic/?${params.toString()}`
}

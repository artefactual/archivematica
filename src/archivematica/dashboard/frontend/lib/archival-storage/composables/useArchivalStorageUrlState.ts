import { useUrlSearchParams } from '@vueuse/core'
import type { SearchRow } from '../types'
import { parseRowsFromParams, rowsToUrlParams } from './useQueryRows'

const buildUrlFromParams = (params: URLSearchParams): string => {
  const query = params.toString()
  return query ? `${window.location.pathname}?${query}` : window.location.pathname
}

const replaceUrl = (params: URLSearchParams): void => {
  window.history.replaceState(null, '', buildUrlFromParams(params))
}

export const useArchivalStorageUrlState = () => {
  // `useUrlSearchParams` is used for scalar URL state while repeated filter
  // params remain custom-serialized for legacy compatibility.
  const scalarParams = useUrlSearchParams('history')

  const getInitialShowFiles = (): boolean => {
    const fileMode = scalarParams.file_mode
    const legacyFileMode = scalarParams.filemode
    return fileMode === 'true' || legacyFileMode === 'true'
  }

  const getInitialRows = (): SearchRow[] => {
    return parseRowsFromParams(new URLSearchParams(window.location.search))
  }

  const syncSearchUrl = (rows: SearchRow[], showFiles: boolean): void => {
    const params = rowsToUrlParams(rows)
    if (showFiles) {
      params.set('file_mode', 'true')
    }
    replaceUrl(params)
  }

  const syncResetUrl = (showFiles: boolean): void => {
    const params = new URLSearchParams()
    if (showFiles) {
      params.set('file_mode', 'true')
    }
    replaceUrl(params)
  }

  return {
    getInitialShowFiles,
    getInitialRows,
    syncSearchUrl,
    syncResetUrl,
  }
}

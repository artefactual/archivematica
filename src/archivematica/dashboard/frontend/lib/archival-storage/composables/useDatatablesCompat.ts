import type { ModeColumn, PaginationState, SearchRow, SortState } from '../types'
import { rowsToUrlParams } from './useQueryRows'

const getSortColumnIndex = (sorting: SortState, columns: ModeColumn[]): number => {
  if (!sorting) {
    return columns.find(column => column.sortable)?.serverIndex ?? 0
  }
  const column = columns.find(item => item.id === sorting.id)
  return column?.serverIndex ?? 0
}

type SearchParamArgs = {
  rows: SearchRow[]
  fileMode: boolean
  pagination: PaginationState
  sorting: SortState
  columns: ModeColumn[]
  sEcho: number
}

export const buildSearchParams = ({
  rows,
  fileMode,
  pagination,
  sorting,
  columns,
  sEcho,
}: SearchParamArgs): URLSearchParams => {
  const params = rowsToUrlParams(rows)
  params.set('file_mode', String(fileMode))
  params.set('iDisplayStart', String(pagination.pageIndex * pagination.pageSize))
  params.set('iDisplayLength', String(pagination.pageSize))
  params.set('iSortCol_0', String(getSortColumnIndex(sorting, columns)))
  params.set('sSortDir_0', sorting?.desc ? 'desc' : 'asc')
  params.set('sEcho', String(sEcho))
  return params
}

type CsvParamArgs = {
  rows: SearchRow[]
  fileMode: boolean
  fileName: string
}

export const buildCsvParams = ({ rows, fileMode, fileName }: CsvParamArgs): URLSearchParams => {
  const params = rowsToUrlParams(rows)
  params.set('requestFile', 'true')
  params.set('mimeType', 'text/csv')
  params.set('fileName', fileName)
  params.set('returnAll', 'true')
  params.set('file_mode', String(fileMode))
  return params
}

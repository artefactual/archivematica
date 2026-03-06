export type SearchMode = 'aips' | 'aipfiles'

export type QueryOperator = '' | 'or' | 'and' | 'not'

export type QueryType = 'term' | 'string' | 'range'

export type SearchRow = {
  id: string
  op: QueryOperator
  query: string
  field: string
  fieldName: string
  type: QueryType
}

export type SortState = {
  id: string
  desc: boolean
} | null

export type PaginationState = {
  pageIndex: number
  pageSize: number
}

export type SearchResultRow = Record<string, unknown>

export type SearchResponse = {
  iTotalRecords: number
  iTotalDisplayRecords: number
  sEcho: number
  aaData: SearchResultRow[]
}

export type ModeColumn = {
  id: string
  headerKey: string
  accessorKey: string
  serverIndex: number
  sortable: boolean
  defaultVisible: boolean
}

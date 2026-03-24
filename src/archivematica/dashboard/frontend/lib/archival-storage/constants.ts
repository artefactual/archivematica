import type { ModeColumn, SearchMode } from './types'

export const SEARCH_FIELDS = [
  { value: '', labelKey: 'archivalStorage.lookups.searchFields.any' },
  { value: 'FILEUUID', labelKey: 'archivalStorage.lookups.searchFields.fileUuid' },
  { value: 'filePath', labelKey: 'archivalStorage.lookups.searchFields.filePath' },
  { value: 'fileExtension', labelKey: 'archivalStorage.lookups.searchFields.fileExtension' },
  { value: 'AIPUUID', labelKey: 'archivalStorage.lookups.searchFields.aipUuid' },
  { value: 'sipName', labelKey: 'archivalStorage.lookups.searchFields.aipName' },
  { value: 'identifiers', labelKey: 'archivalStorage.lookups.searchFields.identifiers' },
  { value: 'isPartOf', labelKey: 'archivalStorage.lookups.searchFields.partOfAic' },
  { value: 'AICID', labelKey: 'archivalStorage.lookups.searchFields.aicIdentifier' },
  { value: 'transferMetadata', labelKey: 'archivalStorage.lookups.searchFields.transferMetadata' },
  { value: 'transferMetadataOther', labelKey: 'archivalStorage.lookups.searchFields.transferMetadataOther' },
] as const

export const QUERY_TYPES = [
  { value: 'term', labelKey: 'archivalStorage.lookups.queryTypes.keyword' },
  { value: 'string', labelKey: 'archivalStorage.lookups.queryTypes.phrase' },
  { value: 'range', labelKey: 'archivalStorage.lookups.queryTypes.dateRange' },
] as const

export const QUERY_OPERATORS = [
  { value: 'or', labelKey: 'archivalStorage.lookups.operators.or' },
  { value: 'and', labelKey: 'archivalStorage.lookups.operators.and' },
  { value: 'not', labelKey: 'archivalStorage.lookups.operators.not' },
] as const

const AIP_COLUMNS: ModeColumn[] = [
  { id: 'name', headerKey: 'archivalStorage.lookups.columns.name', accessorKey: 'name', serverIndex: 0, sortable: true, defaultVisible: true },
  { id: 'uuid', headerKey: 'archivalStorage.lookups.columns.uuid', accessorKey: 'uuid', serverIndex: 1, sortable: true, defaultVisible: true },
  { id: 'AICID', headerKey: 'archivalStorage.lookups.columns.aic', accessorKey: 'AICID', serverIndex: 2, sortable: true, defaultVisible: false },
  { id: 'size', headerKey: 'archivalStorage.lookups.columns.size', accessorKey: 'size', serverIndex: 3, sortable: true, defaultVisible: true },
  { id: 'file_count', headerKey: 'archivalStorage.lookups.columns.fileCount', accessorKey: 'file_count', serverIndex: 4, sortable: true, defaultVisible: false },
  { id: 'accessionids', headerKey: 'archivalStorage.lookups.columns.accessionNumbers', accessorKey: 'accessionids', serverIndex: 5, sortable: true, defaultVisible: false },
  { id: 'created', headerKey: 'archivalStorage.lookups.columns.created', accessorKey: 'created', serverIndex: 6, sortable: true, defaultVisible: true },
  { id: 'status', headerKey: 'archivalStorage.lookups.columns.status', accessorKey: 'status', serverIndex: 7, sortable: true, defaultVisible: true },
  { id: 'encrypted', headerKey: 'archivalStorage.lookups.columns.encrypted', accessorKey: 'encrypted', serverIndex: 8, sortable: true, defaultVisible: true },
  { id: 'location', headerKey: 'archivalStorage.lookups.columns.location', accessorKey: 'location', serverIndex: 9, sortable: true, defaultVisible: false },
  { id: 'actions', headerKey: 'archivalStorage.lookups.columns.actions', accessorKey: 'uuid', serverIndex: 10, sortable: false, defaultVisible: true },
]

const FILE_COLUMNS: ModeColumn[] = [
  { id: 'thumbnail', headerKey: 'archivalStorage.lookups.columns.thumbnail', accessorKey: 'FILEUUID', serverIndex: 0, sortable: false, defaultVisible: true },
  { id: 'filePath', headerKey: 'archivalStorage.lookups.columns.file', accessorKey: 'filePath', serverIndex: 1, sortable: true, defaultVisible: true },
  { id: 'FILEUUID', headerKey: 'archivalStorage.lookups.columns.fileUuid', accessorKey: 'FILEUUID', serverIndex: 2, sortable: true, defaultVisible: true },
  { id: 'sipname', headerKey: 'archivalStorage.lookups.columns.aip', accessorKey: 'sipname', serverIndex: 3, sortable: true, defaultVisible: true },
  { id: 'accessionid', headerKey: 'archivalStorage.lookups.columns.accessionNumber', accessorKey: 'accessionid', serverIndex: 4, sortable: true, defaultVisible: false },
  { id: 'status', headerKey: 'archivalStorage.lookups.columns.status', accessorKey: 'status', serverIndex: 5, sortable: true, defaultVisible: false },
  { id: 'actions', headerKey: 'archivalStorage.lookups.columns.actions', accessorKey: 'FILEUUID', serverIndex: 6, sortable: false, defaultVisible: true },
]

export const getModeColumns = (mode: SearchMode): ModeColumn[] => {
  return mode === 'aipfiles' ? FILE_COLUMNS : AIP_COLUMNS
}

export const getStateTableName = (mode: SearchMode): string => {
  return mode === 'aipfiles' ? 'aipfiles' : 'aips'
}

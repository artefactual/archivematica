import { ref } from 'vue'
import type { SearchRow } from '../types'

let nextSearchRowId = 0
const createSearchRowId = (): string => {
  const id = nextSearchRowId
  nextSearchRowId += 1
  return `search-row-${id}`
}

const createBlankRow = (op: SearchRow['op'] = ''): SearchRow => ({
  id: createSearchRowId(),
  op,
  query: '',
  field: '',
  fieldName: '',
  type: 'term',
})

export const parseRowsFromParams = (params: URLSearchParams): SearchRow[] => {
  const queries = params.getAll('query')
  const fields = params.getAll('field')
  const fieldNames = params.getAll('fieldName')
  const types = params.getAll('type')
  const operators = params.getAll('op')

  const rowCount = Math.max(queries.length, fields.length, fieldNames.length, types.length)
  if (rowCount === 0) {
    return [createBlankRow()]
  }

  const rows: SearchRow[] = []
  for (let index = 0; index < rowCount; index++) {
    rows.push({
      id: createSearchRowId(),
      op: index === 0 ? '' : (operators[index - 1] as SearchRow['op'] ?? 'or'),
      query: queries[index] ?? '',
      field: fields[index] ?? '',
      fieldName: fieldNames[index] ?? '',
      type: (types[index] as SearchRow['type'] | undefined) ?? 'term',
    })
  }

  return rows
}

export const rowsToUrlParams = (rows: SearchRow[]): URLSearchParams => {
  const params = new URLSearchParams()

  rows.forEach((row, index) => {
    if (index > 0) {
      params.append('op', row.op || 'or')
    }
    params.append('query', row.query)
    params.append('field', row.field)
    params.append('fieldName', row.fieldName)
    params.append('type', row.type)
  })

  return params
}

export const useQueryRows = (initialRows?: SearchRow[]) => {
  const rows = ref<SearchRow[]>(initialRows && initialRows.length > 0
    ? initialRows.map(row => ({
        ...row,
        // Preserve parsed row identity for stable list keys.
        id: row.id || createSearchRowId(),
      }))
    : [createBlankRow()])

  const addRow = () => {
    rows.value.push(createBlankRow('or'))
  }

  const removeRow = (index: number) => {
    rows.value = rows.value.filter((_, rowIndex) => rowIndex !== index)
    if (rows.value.length === 0) {
      rows.value = [createBlankRow()]
    }
    if (rows.value[0]) {
      rows.value[0].op = ''
    }
  }

  const isFieldNameVisible = (row: SearchRow) => row.field === 'transferMetadataOther'

  const resetRows = () => {
    rows.value = [createBlankRow()]
  }

  return {
    rows,
    addRow,
    removeRow,
    isFieldNameVisible,
    resetRows,
  }
}

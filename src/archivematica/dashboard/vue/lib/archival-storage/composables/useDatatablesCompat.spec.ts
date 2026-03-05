import { describe, expect, it } from 'vitest'
import { buildCsvParams, buildSearchParams } from './useDatatablesCompat'
import type { ModeColumn, SearchRow } from '../types'

const rows: SearchRow[] = [
  { id: 'search-row-1', op: '', query: 'foo', field: '', fieldName: '', type: 'term' },
  { id: 'search-row-2', op: 'and', query: 'bar', field: 'AIPUUID', fieldName: '', type: 'string' },
]

const columns: ModeColumn[] = [
  {
    id: 'name',
    headerKey: 'archivalStorage.lookups.columns.name',
    accessorKey: 'name',
    serverIndex: 0,
    sortable: true,
    defaultVisible: true,
  },
  {
    id: 'uuid',
    headerKey: 'archivalStorage.lookups.columns.uuid',
    accessorKey: 'uuid',
    serverIndex: 1,
    sortable: true,
    defaultVisible: true,
  },
]

describe('buildSearchParams', () => {
  it('maps table/query state to DataTables-compatible URL params', () => {
    const params = buildSearchParams({
      rows,
      fileMode: false,
      pagination: { pageIndex: 2, pageSize: 25 },
      sorting: { id: 'uuid', desc: true },
      columns,
      sEcho: 4,
    })

    expect(params.getAll('query')).toEqual(['foo', 'bar'])
    expect(params.getAll('op')).toEqual(['and'])
    expect(params.get('file_mode')).toBe('false')
    expect(params.get('iDisplayStart')).toBe('50')
    expect(params.get('iDisplayLength')).toBe('25')
    expect(params.get('iSortCol_0')).toBe('1')
    expect(params.get('sSortDir_0')).toBe('desc')
    expect(params.get('sEcho')).toBe('4')
  })
})

describe('buildCsvParams', () => {
  it('creates CSV download params including current filters', () => {
    const params = buildCsvParams({
      rows,
      fileMode: false,
      fileName: 'archival-storage-report.csv',
    })

    expect(params.get('requestFile')).toBe('true')
    expect(params.get('mimeType')).toBe('text/csv')
    expect(params.get('fileName')).toBe('archival-storage-report.csv')
    expect(params.get('returnAll')).toBe('true')
    expect(params.get('file_mode')).toBe('false')
    expect(params.getAll('query')).toEqual(['foo', 'bar'])
    expect(params.getAll('op')).toEqual(['and'])
  })
})

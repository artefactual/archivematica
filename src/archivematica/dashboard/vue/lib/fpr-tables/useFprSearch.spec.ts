import { computed, nextTick, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import type { FprRow, TableColumnMeta } from './types'
import { useFprSearch } from './useFprSearch'

const makeRows = () =>
  ref<FprRow[]>([
    {
      id: '1',
      description: 'JPEG',
      groupName: '1.02',
      enabled: true,
    },
    {
      id: '2',
      description: 'JPEG',
      groupName: '2.00',
      enabled: false,
    },
  ])

const columns = ref<TableColumnMeta[]>([
  { key: 'description' },
  { key: 'groupName' },
  { key: 'enabled' },
  { key: 'actions', sortable: false },
])

const displayValueForColumn = (row: FprRow, key: string) => {
  const value = row[key]
  if (typeof value === 'string') {
    return value
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  return ''
}

describe('useFprSearch', () => {
  it('applies a debounced global filter value', async () => {
    vi.useFakeTimers()
    try {
      const search = useFprSearch({
        rows: makeRows(),
        columns: computed(() => columns.value),
        displayValueForColumn,
      })

      search.searchFilterInput.value = 'jpeg 1'
      await nextTick()
      expect(search.globalFilter.value).toBe('')

      vi.advanceTimersByTime(100)
      await nextTick()
      expect(search.globalFilter.value).toBe('jpeg 1')
    } finally {
      vi.useRealTimers()
    }
  })

  it('uses tokenized AND matching across searchable columns', () => {
    const rows = makeRows()
    const search = useFprSearch({
      rows,
      columns: computed(() => columns.value),
      displayValueForColumn,
    })

    const firstRow = rows.value[0]
    const secondRow = rows.value[1]
    expect(firstRow).toBeDefined()
    expect(secondRow).toBeDefined()

    expect(search.tokenizedGlobalFilter(firstRow!, 'jpeg 1')).toBe(true)
    expect(search.tokenizedGlobalFilter(secondRow!, 'jpeg 1')).toBe(false)
    expect(search.tokenizedGlobalFilter(firstRow!, 'jpeg yes')).toBe(true)
    expect(search.tokenizedGlobalFilter(secondRow!, 'jpeg yes')).toBe(false)
  })

  it('supports DataTables-style quoted search terms', () => {
    const rows = makeRows()
    const search = useFprSearch({
      rows,
      columns: computed(() => columns.value),
      displayValueForColumn,
    })

    const firstRow = rows.value[0]
    const secondRow = rows.value[1]
    expect(firstRow).toBeDefined()
    expect(secondRow).toBeDefined()

    expect(search.tokenizedGlobalFilter(firstRow!, '"jpeg" "1.02"')).toBe(true)
    expect(search.tokenizedGlobalFilter(secondRow!, '"jpeg" "1.02"')).toBe(false)
  })

  it('clearSearch resets immediately and cancels stale debounced updates', async () => {
    vi.useFakeTimers()
    try {
      const search = useFprSearch({
        rows: makeRows(),
        columns: computed(() => columns.value),
        displayValueForColumn,
      })

      search.searchFilterInput.value = 'jpeg'
      await nextTick()
      search.clearSearch()
      expect(search.searchFilterInput.value).toBe('')
      expect(search.globalFilter.value).toBe('')

      vi.advanceTimersByTime(100)
      await nextTick()
      expect(search.globalFilter.value).toBe('')
    } finally {
      vi.useRealTimers()
    }
  })
})

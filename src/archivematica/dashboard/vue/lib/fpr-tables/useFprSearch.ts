import { computed, ref, watch, type Ref } from 'vue'
import { refDebounced } from '@vueuse/core'
import type { FprRow, TableColumnMeta } from './types'

const SEARCH_DEBOUNCE_MS = 100

type UseFprSearchOptions = {
  rows: Ref<FprRow[]>
  columns: Ref<TableColumnMeta[]>
  displayValueForColumn: (row: FprRow, key: string) => string
}

export const useFprSearch = ({
  rows,
  columns,
  displayValueForColumn,
}: UseFprSearchOptions) => {
  const searchFilterInput = ref('')
  const globalFilter = ref('')
  const debouncedSearchFilterInput = refDebounced(searchFilterInput, SEARCH_DEBOUNCE_MS)

  const searchableColumnKeys = computed(() =>
    columns.value.filter(column => column.key !== 'actions').map(column => column.key),
  )

  const searchableTextByRowId = computed(() => {
    const searchableKeys = searchableColumnKeys.value
    const index = new Map<string, string>()
    for (const row of rows.value) {
      const searchableText = searchableKeys
        .map(key => displayValueForColumn(row, key).toLowerCase())
        .join(' ')
      index.set(row.id, searchableText)
    }
    return index
  })

  let lastFilterValue = ''
  let lastFilterTokens: string[] = []
  const tokensForFilterValue = (filterValue: string): string[] => {
    if (filterValue === lastFilterValue) {
      return lastFilterTokens
    }
    lastFilterValue = filterValue
    lastFilterTokens = filterValue
      .toLowerCase()
      .trim()
      .split(/\s+/)
      .filter(Boolean)
    return lastFilterTokens
  }

  const tokenizedGlobalFilter = (row: FprRow, filterValue: string): boolean => {
    const tokens = tokensForFilterValue(filterValue)
    if (tokens.length === 0) {
      return true
    }

    const searchableText = searchableTextByRowId.value.get(row.id) ?? ''
    return tokens.every(token => searchableText.includes(token))
  }

  const clearSearch = () => {
    lastFilterValue = ''
    lastFilterTokens = []
    searchFilterInput.value = ''
    globalFilter.value = ''
  }

  watch(debouncedSearchFilterInput, (value) => {
    globalFilter.value = value
  })

  return {
    searchFilterInput,
    globalFilter,
    tokenizedGlobalFilter,
    clearSearch,
  }
}

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  createColumnHelper,
  FlexRender,
  functionalUpdate,
  getCoreRowModel,
  useVueTable,
  type ColumnDef,
  type PaginationState as TablePaginationState,
  type SortingState,
  type VisibilityState,
} from '@tanstack/vue-table'
import { useI18n } from 'vue-i18n'
import {
  createArchivalStorageAicUrl,
  createArchivalStorageAipFileDownloadUrl,
  createArchivalStorageAipUrl,
  createArchivalStorageRawFileUrl,
  createArchivalStorageThumbnailUrl,
  openArchivalStorageCsv,
} from '@/shared/http'
import { ResultsPagination } from '@/shared/components'
import { SEARCH_FIELDS, QUERY_OPERATORS, QUERY_TYPES, getModeColumns, getStateTableName } from './constants'
import ArchivalFilePathCell from './components/ArchivalFilePathCell.vue'
import { buildCsvParams, buildSearchParams } from './composables/useDatatablesCompat'
import { useArchivalStorageUrlState } from './composables/useArchivalStorageUrlState'
import { useArchivalStorageSearch } from './composables/useArchivalStorageSearch'
import { loadColumnVisibility, saveColumnVisibility } from './composables/useArchivalStorageState'
import { useQueryRows, rowsToUrlParams } from './composables/useQueryRows'
import type { ModeColumn, SearchResultRow, SearchMode, SortState } from './types'

const props = defineProps<{
  totalSize: string
  filesIndexedCount: number
}>()

const { t } = useI18n()

const {
  getInitialShowFiles,
  getInitialRows,
  syncSearchUrl,
  syncResetUrl,
} = useArchivalStorageUrlState()
const showFiles = ref(getInitialShowFiles())
const { rows, addRow, removeRow, isFieldNameVisible, resetRows } = useQueryRows(getInitialRows())
const columnsDropdownGroupRef = ref<HTMLElement | null>(null)
const columnsDropdownTriggerRef = ref<HTMLButtonElement | null>(null)
const isColumnsDropdownOpen = ref(false)

const mode = computed<SearchMode>(() => (showFiles.value ? 'aipfiles' : 'aips'))
const modeColumns = computed(() => getModeColumns(mode.value))

const tableData = ref<SearchResultRow[]>([])
const totalRecords = ref(0)
const sEchoCounter = ref(0)
const paginationPageSizeOptions = [10, 25, 50]
const DEFAULT_PAGE_SIZE = 10
const pagination = ref<TablePaginationState>({ pageIndex: 0, pageSize: DEFAULT_PAGE_SIZE })
const sorting = ref<SortingState>([])
const columnVisibility = ref<VisibilityState>({})
const loadingState = ref(true)
const isModeSwitching = ref(false)
const activeSearchRequestId = ref(0)
const hasSubmittedSearch = ref(false)
const thumbnailLoadFailures = ref<Record<string, true>>({})

const { loading, error, execute } = useArchivalStorageSearch()
const columnHelper = createColumnHelper<SearchResultRow>()

const formatDate = (value: unknown): string => {
  if (typeof value !== 'number') return ''
  return new Date(value * 1000).toLocaleString()
}

const getString = (row: SearchResultRow, key: string): string => {
  const value = row[key]
  return typeof value === 'string' ? value : ''
}

const getIdentifier = (value: unknown): string => {
  return typeof value === 'string' ? value : ''
}

const hasThumbnailLoadFailure = (fileUUID: string): boolean => {
  return thumbnailLoadFailures.value[fileUUID] === true
}

const markThumbnailLoadFailure = (fileUUID: string): void => {
  if (!fileUUID || hasThumbnailLoadFailure(fileUUID)) return
  thumbnailLoadFailures.value = {
    ...thumbnailLoadFailures.value,
    [fileUUID]: true,
  }
}

const getStableRowId = (row: SearchResultRow, index: number): string => {
  const fileUUID = getIdentifier(row.FILEUUID)
  if (fileUUID) return `file:${fileUUID}`
  const aipUUID = getIdentifier(row.uuid)
  if (aipUUID) return `aip:${aipUUID}`
  const parentAipUUID = getIdentifier(row.AIPUUID)
  if (parentAipUUID) {
    const filePath = getIdentifier(row.filePath)
    if (filePath) return `aip-file:${parentAipUUID}:${filePath}`
    return `aip-file:${parentAipUUID}:${index}`
  }
  return `row:${pagination.value.pageIndex}:${index}`
}

const renderBooleanStatusLabel = (value: unknown) => {
  if (typeof value === 'boolean') {
    return h(
      'span',
      {
        class: ['label', value ? 'label-success' : 'label-default'],
      },
      value ? t('misc.boolean.true') : t('misc.boolean.false'),
    )
  }
  return h('span', { class: ['label', 'label-default'] }, t('archivalStorage.na'))
}

const renderAipAic = (row: SearchResultRow) => {
  const type = getString(row, 'type')
  const aicId = getString(row, 'AICID')
  const isPartOf = getString(row, 'isPartOf')
  const count = row.countAIPsinAIC

  if (type === 'AIC' && typeof count === 'number') {
    const label = count > 1 ? t('archivalStorage.aipsInAic') : t('archivalStorage.aipInAic')
    return `${aicId} (${count} ${label})`
  }
  if (isPartOf) {
    return `${t('archivalStorage.partOf')} ${isPartOf}`
  }
  return t('archivalStorage.none')
}

const buildColumnDefs = (columns: ModeColumn[]): ColumnDef<SearchResultRow>[] => {
  return columns.map(column => columnHelper.accessor(
    row => row[column.accessorKey],
    {
      id: column.id,
      header: column.headerKey,
      enableSorting: column.sortable,
      cell: (context) => {
        const row = context.row.original

        if (column.id === 'thumbnail') {
          const fileUUID = getIdentifier(context.getValue())
          if (!fileUUID) return t('archivalStorage.na')
          if (hasThumbnailLoadFailure(fileUUID)) return t('archivalStorage.na')
          return h('img', {
            key: fileUUID,
            class: 'aip-thumbnail-img',
            src: createArchivalStorageThumbnailUrl(fileUUID),
            onError: () => {
              markThumbnailLoadFailure(fileUUID)
            },
          })
        }

        if (column.id === 'filePath') {
          const path = getIdentifier(context.getValue())
          const idNoHyphens = getString(row, 'document_id_no_hyphens')
          const rawUrl = createArchivalStorageRawFileUrl(idNoHyphens)
          const shownPath = path.startsWith('objects/') ? path.slice('objects/'.length) : path
          return h(ArchivalFilePathCell, { path: shownPath, rawUrl })
        }

        if (column.id === 'sipname') {
          const aipUUID = getString(row, 'AIPUUID')
          const aipName = getIdentifier(context.getValue())
          return h('span', [
            h('a', { href: createArchivalStorageAipUrl(aipUUID) }, aipName),
            h('br'),
            aipUUID,
          ])
        }

        if (column.id === 'actions' && mode.value === 'aipfiles') {
          const fileUUID = getIdentifier(context.getValue())
          return h('a', {
            class: 'btn btn-default btn-sm table-action-btn btn-with-icon',
            href: createArchivalStorageAipFileDownloadUrl(fileUUID),
            target: '_blank',
            rel: 'noopener noreferrer',
          }, [
            h('i', { 'class': 'fa fa-download', 'aria-hidden': 'true' }),
            h('span', { class: 'button-text-span' }, t('archivalStorage.download')),
          ])
        }

        if (column.id === 'name') {
          const uuid = getString(row, 'uuid')
          return h('a', { href: createArchivalStorageAipUrl(uuid) }, getIdentifier(context.getValue()))
        }

        if (column.id === 'AICID') {
          return renderAipAic(row)
        }

        if (column.id === 'accessionids') {
          const ids = row.accessionids
          return Array.isArray(ids) ? ids.join(', ') : ''
        }

        if (column.id === 'created') {
          return formatDate(context.getValue())
        }

        if (column.id === 'encrypted') {
          return renderBooleanStatusLabel(context.getValue())
        }

        if (column.id === 'actions' && mode.value === 'aips') {
          const uuid = getIdentifier(context.getValue())
          return h('a', { class: 'btn btn-default btn-sm table-action-btn', href: createArchivalStorageAipUrl(uuid) }, t('archivalStorage.view'))
        }

        const value = context.getValue()
        return typeof value === 'string' || typeof value === 'number' ? String(value) : ''
      },
    },
  ))
}

const columnDefs = computed(() => buildColumnDefs(modeColumns.value))

const pageCount = computed(() => {
  const count = Math.ceil(totalRecords.value / pagination.value.pageSize)
  return count > 0 ? count : 1
})

const table = useVueTable({
  get data() {
    return tableData.value
  },
  get columns() {
    return columnDefs.value
  },
  state: {
    get sorting() {
      return sorting.value
    },
    get pagination() {
      return pagination.value
    },
    get columnVisibility() {
      return columnVisibility.value
    },
  },
  manualPagination: true,
  manualSorting: true,
  get pageCount() {
    return pageCount.value
  },
  getRowId: (originalRow, index) => getStableRowId(originalRow, index),
  onSortingChange: (updater) => {
    sorting.value = functionalUpdate(updater, sorting.value)
  },
  onPaginationChange: (updater) => {
    pagination.value = functionalUpdate(updater, pagination.value)
  },
  onColumnVisibilityChange: (updater) => {
    columnVisibility.value = functionalUpdate(updater, columnVisibility.value)
  },
  getCoreRowModel: getCoreRowModel(),
})

const getCurrentSortState = (): SortState => {
  const firstSort = sorting.value[0]
  return firstSort ? { id: firstSort.id, desc: firstSort.desc } : null
}

const runSearch = async () => {
  const requestId = activeSearchRequestId.value + 1
  activeSearchRequestId.value = requestId
  const params = buildSearchParams({
    rows: rows.value,
    fileMode: showFiles.value,
    pagination: pagination.value,
    sorting: getCurrentSortState(),
    columns: modeColumns.value,
    sEcho: sEchoCounter.value,
  })

  sEchoCounter.value += 1

  try {
    const response = await execute(params)
    // Ignore stale responses from older in-flight requests.
    if (requestId !== activeSearchRequestId.value) {
      return
    }
    tableData.value = response.aaData
    totalRecords.value = response.iTotalRecords
  } catch {
    // Ignore stale failures; latest request keeps the visible error state.
    if (requestId !== activeSearchRequestId.value) {
      return
    }
  }
}

const hydrateVisibility = async () => {
  const visibility = await loadColumnVisibility(getStateTableName(mode.value), modeColumns.value)
  columnVisibility.value = visibility
}

const submitSearch = async () => {
  hasSubmittedSearch.value = true
  pagination.value = { ...pagination.value, pageIndex: 0 }
  syncSearchUrl(rows.value, showFiles.value)
  await runSearch()
}

const resetFilters = async () => {
  resetRows()
  pagination.value = { ...pagination.value, pageIndex: 0 }
  syncResetUrl(showFiles.value)
  await runSearch()
}

const toggleShowFiles = () => {
  showFiles.value = !showFiles.value
}

const toggleColumnVisibility = (columnId: string, value: boolean) => {
  table.getColumn(columnId)?.toggleVisibility(value)
}

const onColumnCheckboxChange = (columnId: string, event: Event) => {
  const target = event.target as HTMLInputElement | null
  toggleColumnVisibility(columnId, target?.checked === true)
}

const defaultSortForMode = () => {
  const firstSortable = modeColumns.value.find(column => column.sortable)
  sorting.value = firstSortable ? [{ id: firstSortable.id, desc: false }] : []
}

watch(mode, async () => {
  isModeSwitching.value = true
  loadingState.value = true
  thumbnailLoadFailures.value = {}
  tableData.value = []
  totalRecords.value = 0
  pagination.value = { pageIndex: 0, pageSize: DEFAULT_PAGE_SIZE }
  defaultSortForMode()
  try {
    await hydrateVisibility()
    await runSearch()
  } finally {
    syncSearchUrl(rows.value, showFiles.value)
    loadingState.value = false
    isModeSwitching.value = false
  }
}, { immediate: true })

watch(
  [sorting, pagination],
  async () => {
    if (loadingState.value) return
    await runSearch()
  },
  { deep: true },
)

watch(
  columnVisibility,
  (newVisibility) => {
    if (loadingState.value) return
    void saveColumnVisibility(getStateTableName(mode.value), modeColumns.value, newVisibility)
  },
  { deep: true },
)

const createAic = () => {
  const params = rowsToUrlParams(rows.value)
  window.location.assign(createArchivalStorageAicUrl(params))
}

const downloadCsv = () => {
  const params = buildCsvParams({
    rows: rows.value,
    fileMode: showFiles.value,
    fileName: 'archival-storage-report.csv',
  })
  openArchivalStorageCsv(params)
}

const goToFirstPage = () => {
  pagination.value = { ...pagination.value, pageIndex: 0 }
}

const goToLastPage = () => {
  pagination.value = { ...pagination.value, pageIndex: Math.max(pageCount.value - 1, 0) }
}

const onPageSizeChange = (nextPageSize: number) => {
  pagination.value = {
    pageIndex: 0,
    pageSize: nextPageSize,
  }
}

const canPrev = computed(() => pagination.value.pageIndex > 0)
const canNext = computed(() => pagination.value.pageIndex + 1 < pageCount.value)
const showCreateAic = computed(() => (
  hasSubmittedSearch.value
  && !showFiles.value
  && totalRecords.value > 0
))
const hasRows = computed(() => tableData.value.length > 0)
const displayStart = computed(() => (totalRecords.value === 0 ? 0 : (pagination.value.pageIndex * pagination.value.pageSize) + 1))
const displayEnd = computed(() => {
  if (totalRecords.value === 0) return 0
  return Math.min((pagination.value.pageIndex + 1) * pagination.value.pageSize, totalRecords.value)
})
const resultsSummaryLabel = computed(() => t('misc.pagination.infoTemplate', {
  start: displayStart.value,
  end: displayEnd.value,
  total: totalRecords.value,
}))

const getRowLabel = (index: number) => `${t('archivalStorage.filter')} ${index + 1}`
const getOpAriaLabel = (index: number) => `${t('archivalStorage.booleanOperator')} (${getRowLabel(index)})`
const getQueryAriaLabel = (index: number) => `${t('archivalStorage.query')} (${getRowLabel(index)})`
const getFieldAriaLabel = (index: number) => `${t('archivalStorage.field')} (${getRowLabel(index)})`
const getOtherFieldAriaLabel = (index: number) => `${t('archivalStorage.otherFieldName')} (${getRowLabel(index)})`
const getTypeAriaLabel = (index: number) => `${t('archivalStorage.queryType')} (${getRowLabel(index)})`
const getDeleteAriaLabel = (index: number) => `${t('archivalStorage.delete')} ${getRowLabel(index)}`

const getSortAriaValue = (sorted: false | 'asc' | 'desc'): 'none' | 'ascending' | 'descending' => {
  if (sorted === 'asc') return 'ascending'
  if (sorted === 'desc') return 'descending'
  return 'none'
}

const getSortButtonAriaLabel = (headerText: string, sorted: false | 'asc' | 'desc'): string => {
  if (sorted === 'asc') {
    return `${headerText}, ${t('archivalStorage.sortedAscending')}. ${t('archivalStorage.activateToSortDescending')}.`
  }
  if (sorted === 'desc') {
    return `${headerText}, ${t('archivalStorage.sortedDescending')}. ${t('archivalStorage.activateToRemoveSorting')}.`
  }
  return `${headerText}, ${t('archivalStorage.notSorted')}. ${t('archivalStorage.activateToSortAscending')}.`
}

const getColumnHeaderLabel = (columnId: string): string => {
  const column = modeColumns.value.find(item => item.id === columnId)
  return column ? t(column.headerKey) : columnId
}

const closeColumnsDropdown = () => {
  isColumnsDropdownOpen.value = false
}

const toggleColumnsDropdown = () => {
  isColumnsDropdownOpen.value = !isColumnsDropdownOpen.value
}

const onColumnsDropdownTriggerKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
    case ' ':
    case 'Spacebar':
      event.preventDefault()
      toggleColumnsDropdown()
      break
    case 'ArrowDown':
      event.preventDefault()
      isColumnsDropdownOpen.value = true
      break
    case 'Escape':
      if (!isColumnsDropdownOpen.value) return
      event.preventDefault()
      closeColumnsDropdown()
      break
  }
}

const onColumnsDropdownEscape = (event: KeyboardEvent) => {
  event.preventDefault()
  event.stopPropagation()
  closeColumnsDropdown()
  columnsDropdownTriggerRef.value?.focus()
}

const onColumnsDropdownDocumentClick = (event: MouseEvent) => {
  const group = columnsDropdownGroupRef.value
  const target = event.target
  if (!group || !(target instanceof Node)) return
  if (!group.contains(target)) {
    closeColumnsDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', onColumnsDropdownDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onColumnsDropdownDocumentClick)
})

const liveStatusMessage = computed(() => {
  if (loading.value) return t('archivalStorage.loadingResults')
  if (error.value) return `${t('archivalStorage.error')}: ${error.value}`
  if (totalRecords.value === 0) return t('archivalStorage.noResultsFound')
  return resultsSummaryLabel.value
})
</script>

<template>
  <section>
    <p
      class="sr-only"
      aria-live="polite"
      aria-atomic="true"
    >
      {{ liveStatusMessage }}
    </p>
    <form
      id="search_form"
      class="form-inline"
      @submit.prevent="submitSearch"
    >
      <div class="search-form-layout panel panel-default clearfix">
        <div class="search-panel-header panel-heading">
          <h3 class="search-panel-title">
            {{ t('archivalStorage.filters') }}
          </h3>
          <small
            v-if="props.totalSize && props.filesIndexedCount > 0"
            class="search-panel-meta"
          >
            <span class="search-stat-chip">
              <span class="search-stat-label">{{ t('archivalStorage.archiveSize') }}</span>
              <span class="search-stat-value">{{ props.totalSize }}</span>
            </span>
            <span class="search-stat-chip">
              <span class="search-stat-label">{{ t('archivalStorage.filesIndexed') }}</span>
              <span class="search-stat-value">{{ props.filesIndexedCount }}</span>
            </span>
          </small>
        </div>
        <div class="search-panel-body panel-body">
          <div class="search-form-rows">
            <div
              v-for="(row, index) in rows"
              :key="row.id"
              class="archival-row"
            >
              <div class="search-op-slot">
                <select
                  v-if="index > 0"
                  v-model="row.op"
                  class="form-control"
                  :aria-label="getOpAriaLabel(index)"
                >
                  <option
                    v-for="op in QUERY_OPERATORS"
                    :key="op.value"
                    :value="op.value"
                  >
                    {{ t(op.labelKey) }}
                  </option>
                </select>
                <span
                  v-else
                  class="search-op-placeholder"
                />
              </div>

              <input
                v-model="row.query"
                class="form-control aip-search-query-input search-query-input"
                :aria-label="getQueryAriaLabel(index)"
                @keydown.enter.prevent="submitSearch"
              >

              <select
                v-model="row.field"
                class="form-control search-field-select"
                :aria-label="getFieldAriaLabel(index)"
              >
                <option
                  v-for="field in SEARCH_FIELDS"
                  :key="field.value"
                  :value="field.value"
                >
                  {{ t(field.labelKey) }}
                </option>
              </select>

              <input
                v-if="isFieldNameVisible(row)"
                v-model="row.fieldName"
                class="form-control search-other-field"
                :placeholder="t('archivalStorage.otherFieldName')"
                :aria-label="getOtherFieldAriaLabel(index)"
              >

              <select
                v-model="row.type"
                class="form-control search-type-select"
                :aria-label="getTypeAriaLabel(index)"
              >
                <option
                  v-for="queryType in QUERY_TYPES"
                  :key="queryType.value"
                  :value="queryType.value"
                >
                  {{ t(queryType.labelKey) }}
                </option>
              </select>

              <button
                v-if="rows.length > 1"
                type="button"
                class="search-delete-row"
                :aria-label="getDeleteAriaLabel(index)"
                @click="removeRow(index)"
              >
                <i
                  class="fa fa-trash"
                  aria-hidden="true"
                />
              </button>
            </div>
          </div>
        </div>

        <div class="search-submit-container panel-footer">
          <div class="submit-actions-left">
            <div class="show-files-toggle-wrap">
              <span
                id="show-files-toggle-label"
                class="show-files-toggle-label"
              >{{ t('archivalStorage.showFiles') }}</span>
              <button
                type="button"
                class="show-files-toggle"
                :class="{ 'is-active': showFiles }"
                role="switch"
                :aria-pressed="showFiles"
                :aria-checked="showFiles"
                aria-labelledby="show-files-toggle-label"
                @click="toggleShowFiles"
              >
                <span class="show-files-toggle-track">
                  <span class="show-files-toggle-thumb" />
                </span>
              </button>
            </div>
            <button
              type="button"
              class="btn btn-default"
              @click="addRow"
            >
              {{ t('archivalStorage.addFilter') }}
            </button>
            <button
              type="button"
              class="btn btn-default"
              @click="resetFilters"
            >
              {{ t('archivalStorage.reset') }}
            </button>
            <button
              class="btn btn-primary"
              type="submit"
            >
              {{ t('archivalStorage.search') }}
            </button>
          </div>

          <div class="submit-actions-right">
            <button
              v-if="showCreateAic"
              id="create-aic-btn"
              class="btn btn-primary"
              type="button"
              @click="createAic"
            >
              {{ t('archivalStorage.createAnAic') }}
            </button>
            <button
              v-if="!showFiles"
              id="download-csv-btn"
              class="btn btn-default btn-with-icon"
              type="button"
              @click="downloadCsv"
            >
              <i
                class="fa fa-download"
                aria-hidden="true"
              />
              <span class="button-text-span">{{ t('archivalStorage.downloadCsv') }}</span>
            </button>
            <div
              ref="columnsDropdownGroupRef"
              class="btn-group table-column-toggle dropdown"
              :class="{ open: isColumnsDropdownOpen }"
              @click.stop
              @keydown.stop
            >
              <button
                id="select-columns-dropdown"
                ref="columnsDropdownTriggerRef"
                class="btn columns-toggle-btn dropdown-toggle"
                type="button"
                aria-haspopup="true"
                :aria-expanded="isColumnsDropdownOpen"
                @click="toggleColumnsDropdown"
                @keydown="onColumnsDropdownTriggerKeydown"
              >
                <i
                  class="fa fa-cog"
                  aria-hidden="true"
                />
                {{ t('archivalStorage.selectColumns') }}
                <span class="caret" />
              </button>
              <ul
                v-show="isColumnsDropdownOpen"
                :key="mode"
                class="dropdown-menu dropdown-menu-right archival-columns-menu"
                aria-labelledby="select-columns-dropdown"
                @click.stop
                @keydown.esc="onColumnsDropdownEscape"
              >
                <li
                  v-for="column in modeColumns"
                  :key="column.id"
                  class="column-menu-item"
                  @click.stop
                >
                  <label class="column-menu-label">
                    <input
                      class="column-menu-checkbox"
                      type="checkbox"
                      :checked="table.getColumn(column.id)?.getIsVisible()"
                      @click.stop
                      @change="onColumnCheckboxChange(column.id, $event)"
                    >
                    <span>{{ t(column.headerKey) }}</span>
                  </label>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </form>

    <div
      v-if="!isModeSwitching && (loading || hasRows)"
      class="table-responsive"
    >
      <table
        id="archival-storage-entries"
        class="table table-striped"
      >
        <thead>
          <tr
            v-for="headerGroup in table.getHeaderGroups()"
            :key="headerGroup.id"
          >
            <th
              v-for="header in headerGroup.headers"
              :key="header.id"
              :aria-sort="header.column.getCanSort() ? getSortAriaValue(header.column.getIsSorted()) : undefined"
            >
              <button
                v-if="!header.isPlaceholder && header.column.getCanSort()"
                class="header-sort-btn"
                type="button"
                :aria-label="getSortButtonAriaLabel(getColumnHeaderLabel(String(header.column.id)), header.column.getIsSorted())"
                @click="header.column.toggleSorting()"
              >
                {{ getColumnHeaderLabel(String(header.column.id)) }}
                <span class="sort-icon-slot">
                  <i
                    class="fa"
                    :class="{
                      'fa-sort-up': header.column.getIsSorted() === 'asc',
                      'fa-sort-down': header.column.getIsSorted() === 'desc',
                      'fa-sort sort-icon-placeholder': header.column.getIsSorted() !== 'asc' && header.column.getIsSorted() !== 'desc',
                    }"
                    aria-hidden="true"
                  />
                </span>
              </button>
              <span v-else>
                {{ getColumnHeaderLabel(String(header.column.id)) }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="rowData in table.getRowModel().rows"
            :key="rowData.id"
          >
            <td
              v-for="cell in rowData.getVisibleCells()"
              :key="cell.id"
            >
              <FlexRender
                :render="cell.column.columnDef.cell"
                :props="cell.getContext()"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p
      v-if="error"
      class="alert alert-danger table-error"
      role="alert"
    >
      {{ error }}
    </p>

    <ResultsPagination
      v-if="totalRecords > 0"
      :page-index="pagination.pageIndex"
      :page-count="pageCount"
      :page-size="pagination.pageSize"
      :page-size-options="paginationPageSizeOptions"
      :can-previous-page="canPrev"
      :can-next-page="canNext"
      :start-row="displayStart"
      :end-row="displayEnd"
      :total-count="totalRecords"
      :filtered-count="totalRecords"
      control-mode="edges"
      info-style="chip"
      page-size-label-mode="show"
      @first-page="goToFirstPage"
      @previous-page="table.previousPage()"
      @next-page="table.nextPage()"
      @last-page="goToLastPage"
      @set-page-size="onPageSizeChange"
    />
  </section>
</template>

<style scoped>
.archival-row {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.search-form-layout {
  display: block;
  width: 100%;
  max-width: none;
  margin-bottom: 0;
}

.search-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-bottom: 1px solid #e4e4e4;
  background: #f8f8f8;
}

.search-panel-body {
  padding: 0;
}

.search-panel-title {
  margin: 0;
  font-size: 17px;
  font-weight: 400;
  color: #444;
}

.search-panel-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #555;
  font-size: 13px;
  font-weight: 400;
}

.search-stat-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 2px 8px;
  border: 1px solid #d7d7d7;
  border-radius: 999px;
  background: #fff;
}

.search-stat-label {
  color: #666;
}

.search-stat-value {
  color: #222;
  font-weight: 400;
}

.search-form-rows {
  flex: 1;
  min-width: 0;
  padding: 10px;
}

.search-op-slot {
  width: 74px;
}

.search-op-placeholder {
  display: block;
  width: 74px;
}

.search-query-input {
  width: 320px;
  min-width: 240px;
  max-width: 520px;
  flex: 1 1 320px;
}

.search-field-select {
  width: 170px;
  min-width: 140px;
  max-width: 170px;
  flex: 0 0 170px;
}

.search-type-select {
  width: 130px;
  min-width: 120px;
  flex: 0 1 130px;
}

.search-other-field {
  width: 180px;
  min-width: 160px;
  flex: 1 1 180px;
}

.search-delete-row {
  padding: 4px 6px;
  border: 1px solid transparent;
  border-radius: 3px;
  background: none;
  margin-left: 5px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
}

.search-delete-row:hover {
  background-color: #f5f5f5;
}

.search-delete-row:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}

.search-delete-row:hover,
.search-delete-row:focus {
  color: #d9534f;
  border-color: #d9534f;
}

.search-submit-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border-top: 1px solid #ddd;
  background: #f2f2f2;
  position: relative;
  overflow: visible;
}

.submit-actions-left,
.submit-actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.submit-actions-right {
  margin-left: auto;
}

.show-files-toggle-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding-right: 12px;
  margin-right: 4px;
  border-right: 1px solid #d0d0d0;
}

.show-files-toggle-label {
  margin: 0;
  font-weight: 600;
  color: #555;
}

.show-files-toggle {
  border: none;
  background: transparent;
  padding: 0;
}

.show-files-toggle-track {
  width: 42px;
  height: 22px;
  border-radius: 999px;
  border: 1px solid #aaa;
  background: #ddd;
  display: inline-flex;
  align-items: center;
  padding: 2px;
  transition: background-color 0.15s ease;
}

.show-files-toggle-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease;
}

.show-files-toggle.is-active .show-files-toggle-track {
  background: #7a7a7a;
  border-color: #666;
}

.show-files-toggle.is-active .show-files-toggle-thumb {
  transform: translateX(20px);
}

.button-text-span {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px;
}

.btn-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-with-icon .button-text-span {
  margin-left: 0;
}

#create-aic-btn {
  margin: 0;
}

#download-csv-btn {
  margin: 0;
}

.aip-thumbnail-img {
  max-width: 120px;
}

.table-column-toggle {
  margin-left: 2px;
  position: relative;
}

.columns-toggle-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #555;
}

.columns-toggle-btn:hover,
.columns-toggle-btn:focus {
  background: #e9e9e9;
  border-color: #ccc;
}

.columns-toggle-btn .fa {
  margin-right: 6px;
}

.archival-columns-menu {
  right: 0;
  left: auto;
  z-index: 3000;
  position: absolute;
  top: calc(100% + 2px);
}

.archival-columns-menu {
  min-width: 220px;
  max-height: 280px;
  overflow-y: auto;
  margin-top: 2px;
  padding: 4px 0;
}

.column-menu-item {
  width: 100%;
  padding: 0;
}

.column-menu-label {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin: 0;
  padding: 6px 12px;
  font-size: 13px;
  line-height: 1.4;
  font-weight: 400;
  cursor: pointer;
}

.column-menu-label:hover {
  background: #f5f5f5;
}

.column-menu-checkbox {
  margin: 0;
  flex: 0 0 auto;
}

.header-sort-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  border: none;
  background: none;
  padding: 0;
  font-weight: 600;
  text-align: left;
}

.header-sort-btn .fa {
  flex: 0 0 auto;
}

.sort-icon-slot {
  display: inline-flex;
  justify-content: center;
  flex: 0 0 auto;
}

.sort-icon-placeholder {
  visibility: hidden;
}

#archival-storage-entries th,
#archival-storage-entries td {
  vertical-align: middle;
}

.table-action-btn {
  line-height: 1.2;
}

.table-action-btn .button-text-span {
  margin-left: 4px;
  font-size: 13px;
}

.table-error {
  margin-top: 12px;
}

.table-responsive {
  margin-top: 20px;
}

@media (max-width: 991px) {
  .search-op-slot,
  .search-op-placeholder {
    width: 64px;
  }

  .search-query-input {
    min-width: 180px;
    flex: 1 1 220px;
  }
}

@media (max-width: 767px) {
  .archival-row {
    gap: 8px;
    margin-bottom: 0;
  }

  .archival-row + .archival-row {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #e5e5e5;
  }

  .search-op-slot {
    width: 100%;
  }

  .search-op-placeholder {
    display: none;
  }

  .search-query-input,
  .search-field-select,
  .search-type-select,
  .search-other-field {
    width: 100%;
    min-width: 0;
    max-width: none;
    flex: 1 1 100%;
  }

  .search-delete-row {
    margin-left: 0;
  }

  .search-submit-container {
    gap: 12px;
  }

  .submit-actions-left,
  .submit-actions-right {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>

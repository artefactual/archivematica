<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  FlexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type Cell,
  type ColumnDef,
  type PaginationState,
  type Row,
  type SortingState,
  type Updater,
  useVueTable,
} from '@tanstack/vue-table'
import { ResultsPagination } from '@/shared/components'
import * as fprRoutes from '@/shared/http/fpr'
import type { FprRow, FprTableKind, FprTablePayload, TableAction, TableActionStyle } from './types'
import { useFprSearch } from './useFprSearch'

const { t } = useI18n()

const props = defineProps<{
  payload: FprTablePayload
}>()

const EMPTY_TEXT_KEY_BY_KIND: Record<FprTableKind, string> = {
  'format-list': 'fpr.empty.formats',
  'idcommand-list': 'fpr.empty.idCommands',
  'fpcommand-list': 'fpr.empty.fpCommands',
  'idtool-list': 'fpr.empty.idTools',
  'fptool-list': 'fpr.empty.tools',
  'formatgroup-list': 'fpr.empty.formatGroups',
  'idrule-list': 'fpr.empty.idRules',
  'fprule-list': 'fpr.empty.fpRules',
  'format-detail-versions': 'fpr.empty.versions',
  'idtool-detail-commands': 'fpr.empty.commands',
  'fptool-detail-commands': 'fpr.empty.commands',
  'formatgroup-form-formats': 'fpr.empty.formats',
}

const CREATE_LABEL_KEY_BY_KIND: Record<FprTableKind, string> = {
  'format-list': 'fpr.create.format',
  'idcommand-list': 'fpr.create.command',
  'fpcommand-list': 'fpr.create.command',
  'idtool-list': 'fpr.create.tool',
  'fptool-list': 'fpr.create.tool',
  'formatgroup-list': 'fpr.create.formatGroup',
  'idrule-list': 'fpr.create.rule',
  'fprule-list': 'fpr.create.rule',
  'format-detail-versions': 'fpr.create.formatVersion',
  'idtool-detail-commands': 'fpr.create.command',
  'fptool-detail-commands': 'fpr.create.toolCommand',
  'formatgroup-form-formats': 'fpr.create.format',
}

type KindColumnDefinition = {
  id: string
  fallbackLabelKey: string
}

const COLUMN_DEFINITIONS_BY_KIND: Record<FprTableKind, KindColumnDefinition[]> = {
  'format-list': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'groupName', fallbackLabelKey: 'fpr.columns.group' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'idcommand-list': [
    { id: 'command', fallbackLabelKey: 'fpr.columns.command' },
    { id: 'type', fallbackLabelKey: 'fpr.columns.type' },
    { id: 'tool', fallbackLabelKey: 'fpr.columns.tool' },
    { id: 'mode', fallbackLabelKey: 'fpr.columns.mode' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'fpcommand-list': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'usage', fallbackLabelKey: 'fpr.columns.usage' },
    { id: 'tool', fallbackLabelKey: 'fpr.columns.tool' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'idtool-list': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'version', fallbackLabelKey: 'fpr.columns.version' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'fptool-list': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'formatgroup-list': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'idrule-list': [
    { id: 'format', fallbackLabelKey: 'fpr.columns.format' },
    { id: 'command', fallbackLabelKey: 'fpr.columns.command' },
    { id: 'output', fallbackLabelKey: 'fpr.columns.output' },
    { id: 'tool', fallbackLabelKey: 'fpr.columns.tools' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'fprule-list': [
    { id: 'purpose', fallbackLabelKey: 'fpr.columns.purpose' },
    { id: 'format', fallbackLabelKey: 'fpr.columns.format' },
    { id: 'command', fallbackLabelKey: 'fpr.columns.command' },
    { id: 'success', fallbackLabelKey: 'fpr.columns.success' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'format-detail-versions': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'version', fallbackLabelKey: 'fpr.columns.version' },
    { id: 'pronomId', fallbackLabelKey: 'fpr.columns.pronomId' },
    { id: 'accessFormat', fallbackLabelKey: 'fpr.columns.accessFormat' },
    { id: 'preservationFormat', fallbackLabelKey: 'fpr.columns.preservationFormat' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'idtool-detail-commands': [
    { id: 'configuration', fallbackLabelKey: 'fpr.columns.configuration' },
    { id: 'identifier', fallbackLabelKey: 'fpr.columns.identifier' },
    { id: 'commandScript', fallbackLabelKey: 'fpr.columns.command' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'fptool-detail-commands': [
    { id: 'command', fallbackLabelKey: 'fpr.columns.command' },
    { id: 'uuid', fallbackLabelKey: 'fpr.columns.uuid' },
    { id: 'enabled', fallbackLabelKey: 'fpr.columns.enabled' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
  'formatgroup-form-formats': [
    { id: 'description', fallbackLabelKey: 'fpr.columns.description' },
    { id: 'actions', fallbackLabelKey: 'fpr.columns.actions' },
  ],
}

// Client-side page size options.
const PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const

// Some row fields are code values from Django and are translated in Vue.
const VALUE_KEY_PREFIX_BY_COLUMN: Partial<Record<string, string>> = {
  type: 'fpr.values.scriptType',
  usage: 'fpr.values.commandUsage',
  purpose: 'fpr.values.purpose',
  mode: 'fpr.values.configuration',
  configuration: 'fpr.values.configuration',
}

// Preferred fill-column order for CSS width hints.
// First matching column expands.
const FILL_COLUMN_PREFERENCE = ['description', 'format', 'command'] as const

// TanStack sort state is controlled from Vue so we can reset pagination on sort
// changes.
const sorting = ref<SortingState>([])

// Used for autofocus after the Vue table mounts.
const searchInputRef = ref<HTMLInputElement | null>(null)

// Client-side page state (first iteration: full dataset in memory).
const pagination = ref<PaginationState>({
  pageIndex: 0,
  pageSize: 10,
})
const pageSizeOptions = [...PAGE_SIZE_OPTIONS]

// Scroll target when the pager changes pages.
const tableTopRef = ref<HTMLElement | null>(null)

// Guards page-change scroll behavior so it does not run on initial render.
const hasMounted = ref(false)

// TanStack callbacks pass either a concrete value or an updater function;
// normalize both into a Vue ref.
const updateRef = <T>(updater: Updater<T>, target: { value: T }) => {
  if (typeof updater === 'function') {
    target.value = (updater as (old: T) => T)(target.value)
    return
  }
  target.value = updater
}

// Django can override labels/sortability per page via payload metadata, so look
// up column metadata by key first.
const columnMetaByKey = computed(() => new Map(props.payload.columns.map(column => [column.key, column])))
const columnMeta = (key: string) => columnMetaByKey.value.get(key)
// Column labels/sortability can be overridden per page.
// Django sends those overrides in payload metadata.
const columnLabel = (key: string, fallback: string) => columnMeta(key)?.label ?? fallback
const columnIsSortable = (key: string, fallback = true) => columnMeta(key)?.sortable ?? fallback

const numericField = (row: FprRow, key: string): number | null => {
  const value = row[key]
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

const formatFieldLabel = (row: FprRow): string | null => {
  const description = row.format
  if (typeof description !== 'string') {
    return null
  }

  const details: string[] = []
  const version = row.formatVersion
  const pronomId = row.formatPronomId
  if (typeof version === 'string' && version.length > 0) {
    details.push(
      t('fpr.values.formatVersionTemplate', {
        version,
      }),
    )
  }
  if (typeof pronomId === 'string' && pronomId.length > 0) {
    details.push(pronomId)
  }
  if (details.length === 0) {
    return description
  }
  return `${description} (${details.join(', ')})`
}

const displayValueForColumn = (row: FprRow, key: string): string => {
  if (key === 'success') {
    const okay = numericField(row, 'successOkay')
    const attempts = numericField(row, 'successAttempts')
    if (okay !== null && attempts !== null) {
      return t('fpr.values.successTemplate', { okay, attempts })
    }
  }

  if (key === 'format') {
    const formatted = formatFieldLabel(row)
    if (formatted !== null) {
      return formatted
    }
  }

  const value = row[key]
  if (typeof value === 'string') {
    const prefix = VALUE_KEY_PREFIX_BY_COLUMN[key]
    if (prefix) {
      return t(`${prefix}.${value}`)
    }
    return value
  }
  if (typeof value === 'number') {
    return String(value)
  }
  if (typeof value === 'boolean') {
    return value ? t('misc.boolean.true') : t('misc.boolean.false')
  }
  return ''
}

const {
  searchFilterInput,
  globalFilter,
  tokenizedGlobalFilter,
  clearSearch,
} = useFprSearch({
  rows: computed(() => props.payload.rows),
  columns: computed(() => props.payload.columns),
  displayValueForColumn,
})

// Normalize mixed row values into stable strings.
// This keeps TanStack sort/filter behavior consistent across types.
const fieldColumn = (id: string, fallbackLabelKey: string): ColumnDef<FprRow> => ({
  id,
  accessorFn: (row) => {
    if (id === 'enabled' && typeof row.enabled === 'boolean') {
      return row.enabled ? '1' : '0'
    }
    return displayValueForColumn(row, id)
  },
  header: columnLabel(id, t(fallbackLabelKey)),
  enableSorting: columnIsSortable(id),
})

// The "actions" has the same definition across all tables.
const actionsColumn = (): ColumnDef<FprRow> => ({
  id: 'actions',
  accessorFn: () => '',
  header: columnLabel('actions', t('fpr.columns.actions')),
  enableSorting: false,
  enableGlobalFilter: false,
})

// Rebuild TanStack columns from the payload.
// This supports payload-driven table kinds in the shared renderer.
const columns = computed<ColumnDef<FprRow>[]>(() => {
  const availableColumnKeys = new Set(props.payload.columns.map(column => column.key))
  return COLUMN_DEFINITIONS_BY_KIND[props.payload.kind]
    .filter(({ id }) => availableColumnKeys.has(id))
    .map(({ id, fallbackLabelKey }) =>
      id === 'actions' ? actionsColumn() : fieldColumn(id, fallbackLabelKey),
    )
})

const table = useVueTable({
  get data() {
    return props.payload.rows
  },
  get columns() {
    return columns.value
  },
  state: {
    get sorting() {
      return sorting.value
    },
    get globalFilter() {
      return globalFilter.value
    },
    get pagination() {
      return pagination.value
    },
  },
  onSortingChange: updater => updateRef(updater, sorting),
  onGlobalFilterChange: updater => updateRef(updater, globalFilter),
  onPaginationChange: updater => updateRef(updater, pagination),
  globalFilterFn: (row, _columnId, filterValue) =>
    tokenizedGlobalFilter(row.original, String(filterValue ?? '')),
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getRowId: row => row.id,
})

// Use pre-pagination rows for totals/info.
// This reflects filter+sort results before page slicing.
const filteredRows = computed(() => table.getPrePaginationRowModel().rows)
// These are the rows currently rendered in the table body (after pagination).
const rows = computed(() => table.getRowModel().rows)
const actionButtonClass = (style: TableActionStyle, size: 'xs' | 'sm' = 'xs') => {
  const classes = ['btn', size === 'sm' ? 'btn-sm' : 'btn-xs']
  if (style === 'primary') {
    classes.push('btn-primary')
  } else if (style === 'warning') {
    classes.push('btn-warning')
  } else {
    classes.push('btn-default')
  }
  return classes.join(' ')
}

const createButtonClass = computed(() => {
  // Let Django choose the create-action button style, with a safe default.
  const createStyle = props.payload.ui.create?.style ?? 'primary'
  return actionButtonClass(createStyle, 'sm')
})

const stringField = (row: FprRow, key: string): string | null => {
  const value = row[key]
  return typeof value === 'string' && value.length > 0 ? value : null
}

const createUrl = computed(() => {
  const create = props.payload.ui.create
  if (!create) {
    return null
  }

  switch (props.payload.kind) {
    case 'format-list':
    case 'formatgroup-form-formats':
      return fprRoutes.getFprFormatCreateUrl()
    case 'idcommand-list':
      return fprRoutes.getFprIdCommandCreateUrl()
    case 'fpcommand-list':
      return fprRoutes.getFprFpCommandCreateUrl()
    case 'idtool-list':
      return fprRoutes.getFprIdToolCreateUrl()
    case 'fptool-list':
      return fprRoutes.getFprFpToolCreateUrl()
    case 'formatgroup-list':
      return fprRoutes.getFprFormatGroupCreateUrl()
    case 'idrule-list':
      return fprRoutes.getFprIdRuleCreateUrl()
    case 'fprule-list':
      return fprRoutes.getFprFpRuleCreateUrl()
    case 'format-detail-versions':
      return create.formatSlug ? fprRoutes.getFprFormatVersionCreateUrl(create.formatSlug) : null
    case 'idtool-detail-commands':
      return fprRoutes.getFprIdCommandCreateUrl(create.parentUuid)
    case 'fptool-detail-commands':
      return fprRoutes.getFprFpCommandCreateUrl(create.parentUuid)
    default:
      return null
  }
})

const createLabel = computed(() => t(CREATE_LABEL_KEY_BY_KIND[props.payload.kind]))
const emptyText = computed(() => t(EMPTY_TEXT_KEY_BY_KIND[props.payload.kind]))
const emptyAlertText = computed(() => (
  props.payload.rows.length > 0 ? t('fpr.search.noMatches') : emptyText.value
))

// Centralize display normalization for mixed row cell values.
const getString = (row: FprRow, key: string): string => displayValueForColumn(row, key)

const getBool = (row: FprRow, key: string): boolean => row[key] === true

const getActions = (row: FprRow): TableAction[] => row.actions ?? []
const actionLabel = (action: TableAction) => t(`fpr.actions.${action.key}`)

const actionsWithUrl = (row: FprRow): Array<{ action: TableAction, url: string }> =>
  getActions(row)
    .map(action => ({ action, url: actionUrlForRow(row, action) }))
    .filter((item): item is { action: TableAction, url: string } => item.url !== null)

const actionUrlForRow = (row: FprRow, action: TableAction): string | null => {
  const rowId = row.id
  const formatSlug = stringField(row, 'formatSlug')
  const versionSlug = stringField(row, 'versionSlug')
  const toolSlug = stringField(row, 'toolSlug')
  const groupSlug = stringField(row, 'groupSlug')

  switch (props.payload.kind) {
    case 'format-list':
    case 'formatgroup-form-formats':
      if (!formatSlug) return null
      if (action.key === 'view') return fprRoutes.getFprFormatDetailUrl(formatSlug)
      if (action.key === 'edit') return fprRoutes.getFprFormatEditUrl(formatSlug)
      return null
    case 'idcommand-list':
    case 'idtool-detail-commands':
      if (action.key === 'view') return fprRoutes.getFprIdCommandDetailUrl(rowId)
      if (action.key === 'replace') return fprRoutes.getFprIdCommandEditUrl(rowId)
      if (action.key === 'disable' || action.key === 'enable') return fprRoutes.getFprIdCommandDeleteUrl(rowId)
      return null
    case 'fpcommand-list':
    case 'fptool-detail-commands':
      if (action.key === 'view') return fprRoutes.getFprFpCommandDetailUrl(rowId)
      if (action.key === 'replace') return fprRoutes.getFprFpCommandEditUrl(rowId)
      if (action.key === 'disable' || action.key === 'enable') return fprRoutes.getFprFpCommandDeleteUrl(rowId)
      return null
    case 'idtool-list':
      if (!toolSlug) return null
      if (action.key === 'view') return fprRoutes.getFprIdToolDetailUrl(toolSlug)
      if (action.key === 'edit') return fprRoutes.getFprIdToolEditUrl(toolSlug)
      return null
    case 'fptool-list':
      if (!toolSlug) return null
      if (action.key === 'view') return fprRoutes.getFprFpToolDetailUrl(toolSlug)
      if (action.key === 'edit') return fprRoutes.getFprFpToolEditUrl(toolSlug)
      return null
    case 'formatgroup-list':
      if (!groupSlug) return null
      if (action.key === 'edit') return fprRoutes.getFprFormatGroupEditUrl(groupSlug)
      if (action.key === 'delete') return fprRoutes.getFprFormatGroupDeleteUrl(groupSlug)
      return null
    case 'idrule-list':
      if (action.key === 'view') return fprRoutes.getFprIdRuleDetailUrl(rowId)
      if (action.key === 'replace') return fprRoutes.getFprIdRuleEditUrl(rowId)
      if (action.key === 'disable' || action.key === 'enable') return fprRoutes.getFprIdRuleDeleteUrl(rowId)
      return null
    case 'fprule-list':
      if (action.key === 'view') return fprRoutes.getFprFpRuleDetailUrl(rowId)
      if (action.key === 'replace') return fprRoutes.getFprFpRuleEditUrl(rowId)
      if (action.key === 'disable' || action.key === 'enable') return fprRoutes.getFprFpRuleDeleteUrl(rowId)
      return null
    case 'format-detail-versions':
      if (!formatSlug || !versionSlug) return null
      if (action.key === 'view') return fprRoutes.getFprFormatVersionDetailUrl(formatSlug, versionSlug)
      if (action.key === 'replace') return fprRoutes.getFprFormatVersionEditUrl(formatSlug, versionSlug)
      if (action.key === 'disable' || action.key === 'enable') {
        return fprRoutes.getFprFormatVersionDeleteUrl(formatSlug, versionSlug)
      }
      return null
  }
}

const linkUrlForCell = (row: FprRow, columnId: string): string | null => {
  const rowId = row.id
  const formatSlug = stringField(row, 'formatSlug')
  const versionSlug = stringField(row, 'versionSlug')
  const groupSlug = stringField(row, 'groupSlug')
  const toolSlug = stringField(row, 'toolSlug')
  const commandUuid = stringField(row, 'commandUuid')

  switch (props.payload.kind) {
    case 'format-list':
      if (columnId === 'description' && formatSlug) return fprRoutes.getFprFormatDetailUrl(formatSlug)
      if (columnId === 'groupName' && groupSlug) return fprRoutes.getFprFormatGroupEditUrl(groupSlug)
      return null
    case 'idcommand-list':
      if (columnId === 'command') return fprRoutes.getFprIdCommandDetailUrl(rowId)
      if (columnId === 'tool' && toolSlug) return fprRoutes.getFprIdToolDetailUrl(toolSlug)
      return null
    case 'fpcommand-list':
      return columnId === 'description' ? fprRoutes.getFprFpCommandDetailUrl(rowId) : null
    case 'idtool-list':
      if ((columnId === 'description' || columnId === 'version') && toolSlug) {
        return fprRoutes.getFprIdToolDetailUrl(toolSlug)
      }
      return null
    case 'fptool-list':
      return columnId === 'description' && toolSlug ? fprRoutes.getFprFpToolDetailUrl(toolSlug) : null
    case 'formatgroup-list':
      return columnId === 'description' && groupSlug ? fprRoutes.getFprFormatGroupEditUrl(groupSlug) : null
    case 'idrule-list':
      if (columnId === 'format' && formatSlug) return fprRoutes.getFprFormatDetailUrl(formatSlug)
      if (columnId === 'command' && commandUuid) return fprRoutes.getFprIdCommandDetailUrl(commandUuid)
      if (columnId === 'output') return fprRoutes.getFprIdRuleDetailUrl(rowId)
      if (columnId === 'tool' && toolSlug) return fprRoutes.getFprIdToolDetailUrl(toolSlug)
      return null
    case 'fprule-list':
      return columnId === 'format' && formatSlug ? fprRoutes.getFprFormatDetailUrl(formatSlug) : null
    case 'format-detail-versions':
      if (columnId === 'description' && formatSlug && versionSlug) {
        return fprRoutes.getFprFormatVersionDetailUrl(formatSlug, versionSlug)
      }
      if (columnId === 'pronomId') {
        const pronomId = stringField(row, 'pronomId')
        return pronomId ? `https://www.nationalarchives.gov.uk/PRONOM/${pronomId}` : null
      }
      return null
    case 'idtool-detail-commands':
      return null
    case 'fptool-detail-commands':
      return (columnId === 'command' || columnId === 'uuid') ? fprRoutes.getFprFpCommandDetailUrl(rowId) : null
    case 'formatgroup-form-formats':
      return columnId === 'description' && formatSlug ? fprRoutes.getFprFormatDetailUrl(formatSlug) : null
  }
}

const isExternalLinkCell = (columnId: string) => columnId === 'pronomId'

const isEnabledColumn = (columnId: string) => columnId === 'enabled'

onMounted(() => {
  hasMounted.value = true
  searchFilterInput.value = globalFilter.value
  searchInputRef.value?.focus()
})

const fillColumnId = computed(() => {
  // Prefer one "main" text column to absorb extra width.
  // This avoids enabling TanStack column sizing.
  for (const key of FILL_COLUMN_PREFERENCE) {
    if (props.payload.columns.some(column => column.key === key)) {
      return key
    }
  }
  return null
})

const isFillColumn = (columnId: string) => columnId === fillColumnId.value

const headerCellClass = (columnId: string) => [
  { 'fpr-sortable': table.getColumn(columnId)?.getCanSort() ?? false },
  isFillColumn(columnId) ? 'fpr-col-fill' : null,
  columnId === 'actions' ? 'fpr-col-actions' : null,
]

const bodyCellClass = (columnId: string) => [
  isFillColumn(columnId) ? 'fpr-col-fill' : null,
  columnId === 'actions' ? 'fpr-col-actions' : null,
]

const cellsForRow = (row: Row<FprRow>): Array<{ cell: Cell<FprRow, unknown>, linkUrl: string | null }> =>
  row.getVisibleCells().map(cell => ({
    cell: cell as Cell<FprRow, unknown>,
    linkUrl: linkUrlForCell(row.original, cell.column.id),
  }))

const pageIndex = computed(() => table.getState().pagination.pageIndex)
const pageSize = computed(() => table.getState().pagination.pageSize)
const pageCount = computed(() => table.getPageCount())
const canPreviousPage = computed(() => table.getCanPreviousPage())
const canNextPage = computed(() => table.getCanNextPage())
const pageStartRow = computed(() => {
  // Pager info should show 0..0 when no rows remain after filtering.
  if (filteredRows.value.length === 0 || rows.value.length === 0) {
    return 0
  }
  return pageIndex.value * pageSize.value + 1
})
const pageEndRow = computed(() => {
  // End row is based on the current rendered page, not the filtered total.
  if (filteredRows.value.length === 0 || rows.value.length === 0) {
    return 0
  }
  return pageStartRow.value + rows.value.length - 1
})

// Reset to page 1 after filter/sort changes.
// This avoids landing on an empty later page.
watch(globalFilter, () => table.setPageIndex(0))
watch(sorting, () => table.setPageIndex(0), { deep: true })

// Pager navigation should return the user to the top of the table.
// Otherwise repeated paging forces extra scrolling.
watch(pageIndex, async (nextPageIndex, previousPageIndex) => {
  if (!hasMounted.value || nextPageIndex === previousPageIndex) {
    return
  }
  await nextTick()
  tableTopRef.value?.scrollIntoView({ block: 'start', behavior: 'smooth' })
})
</script>

<template>
  <div
    ref="tableTopRef"
    class="fpr-table-app"
  >
    <div class="fpr-toolbar">
      <div class="fpr-toolbar-main">
        <div class="fpr-toolbar-search">
          <label class="control-label sr-only">
            {{ t('fpr.search.label') }}
          </label>
          <div class="input-group">
            <input
              ref="searchInputRef"
              v-model="searchFilterInput"
              class="form-control"
              type="search"
              :placeholder="t('fpr.search.placeholder')"
            >
            <span class="input-group-btn">
              <button
                class="btn btn-default"
                type="button"
                :disabled="!searchFilterInput"
                @click="clearSearch"
              >
                {{ t('fpr.search.clear') }}
              </button>
            </span>
          </div>
        </div>

        <div class="fpr-toolbar-left">
          <a
            v-if="payload.ui.create && createUrl"
            :href="createUrl || undefined"
            :class="createButtonClass"
          >
            {{ createLabel }}
          </a>
        </div>
      </div>
    </div>

    <template v-if="filteredRows.length">
      <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover table-condensed">
          <thead>
            <tr
              v-for="headerGroup in table.getHeaderGroups()"
              :key="headerGroup.id"
            >
              <th
                v-for="header in headerGroup.headers"
                :key="header.id"
                :class="headerCellClass(header.column.id)"
              >
                <template v-if="!header.isPlaceholder">
                  <button
                    v-if="header.column.getCanSort()"
                    class="fpr-header-sort-btn"
                    type="button"
                    @click="header.column.toggleSorting()"
                  >
                    <span class="fpr-header-label">
                      <FlexRender
                        :render="header.column.columnDef.header"
                        :props="header.getContext()"
                      />
                    </span>
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
                  <span
                    v-else
                    class="fpr-header-label"
                  >
                    <FlexRender
                      :render="header.column.columnDef.header"
                      :props="header.getContext()"
                    />
                  </span>
                </template>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.id"
            >
              <td
                v-for="cellItem in cellsForRow(row)"
                :key="cellItem.cell.id"
                :class="bodyCellClass(cellItem.cell.column.id)"
              >
                <template v-if="cellItem.cell.column.id === 'actions'">
                  <div class="fpr-actions">
                    <a
                      v-for="item in actionsWithUrl(cellItem.cell.row.original)"
                      :key="`${cellItem.cell.row.id}-${item.action.key}`"
                      :href="item.url"
                      :class="actionButtonClass(item.action.style)"
                    >
                      {{ actionLabel(item.action) }}
                    </a>
                  </div>
                </template>

                <template v-else-if="isEnabledColumn(cellItem.cell.column.id)">
                  <span
                    class="label"
                    :class="getBool(cellItem.cell.row.original, 'enabled') ? 'label-success' : 'label-default'"
                  >
                    {{ getString(cellItem.cell.row.original, 'enabled') }}
                  </span>
                </template>

                <template v-else-if="cellItem.linkUrl">
                  <a
                    :href="cellItem.linkUrl || undefined"
                    :target="isExternalLinkCell(cellItem.cell.column.id) ? '_blank' : undefined"
                    :rel="isExternalLinkCell(cellItem.cell.column.id) ? 'noopener noreferrer' : undefined"
                  >
                    {{ getString(cellItem.cell.row.original, cellItem.cell.column.id) }}
                  </a>
                </template>

                <template v-else>
                  {{ getString(cellItem.cell.row.original, cellItem.cell.column.id) }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <ResultsPagination
        :page-index="pageIndex"
        :page-count="pageCount"
        :page-size="pageSize"
        :page-size-options="pageSizeOptions"
        :can-previous-page="canPreviousPage"
        :can-next-page="canNextPage"
        :start-row="pageStartRow"
        :end-row="pageEndRow"
        :filtered-count="filteredRows.length"
        :total-count="payload.rows.length"
        control-mode="pages"
        info-style="plain"
        page-size-label-mode="template"
        @set-page-index="(nextPageIndex) => table.setPageIndex(nextPageIndex)"
        @previous-page="() => table.previousPage()"
        @next-page="() => table.nextPage()"
        @set-page-size="(nextPageSize) => table.setPageSize(nextPageSize)"
      />
    </template>

    <div
      v-else
      class="alert alert-info"
      role="status"
    >
      {{ emptyAlertText }}
    </div>
  </div>
</template>

<style scoped>
.fpr-toolbar {
  margin-bottom: 10px;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fafafa;
}

.fpr-toolbar-main {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
}

.fpr-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  margin-left: auto;
}

.fpr-toolbar-search {
  max-width: 380px;
  width: 100%;
  margin-left: 0;
}

.fpr-toolbar-left .btn {
  white-space: nowrap;
}

.fpr-sortable {
  white-space: nowrap;
}

.fpr-header-label {
  display: inline-block;
  white-space: nowrap;
}

.fpr-header-sort-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: none;
  padding: 0;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  user-select: none;
}

.fpr-header-sort-btn:focus {
  outline: 1px dotted #333;
  outline-offset: 2px;
}

.fpr-header-sort-btn .fa {
  flex: 0 0 auto;
}

.sort-icon-slot {
  display: inline-flex;
  justify-content: center;
  flex: 0 0 auto;
  min-width: 1em;
  color: #777;
  white-space: nowrap;
}

.sort-icon-placeholder {
  visibility: hidden;
}

.fpr-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
  white-space: nowrap;
}

.fpr-col-fill {
  width: 99%;
}

.fpr-col-actions {
  width: 1%;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .fpr-toolbar-main {
    flex-direction: column;
    align-items: stretch;
  }

  .fpr-toolbar-left {
    flex-wrap: wrap;
    margin-left: 0;
  }

  .fpr-toolbar-search {
    max-width: none;
    margin-left: 0;
  }
}
</style>

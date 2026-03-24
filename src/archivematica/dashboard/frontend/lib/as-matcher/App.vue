<script setup lang="ts">
import {
  functionalUpdate,
  getCoreRowModel,
  getSortedRowModel,
  useVueTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/vue-table'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  createArchivesSpacePair,
  deleteArchivesSpacePair,
  getIngestUploadAsResetUrl,
  getIngestUploadAsReviewMatchesUrl,
} from '@/shared/http'
import MatcherAlerts from './components/MatcherAlerts.vue'
import MatcherObjectPane from './components/MatcherObjectPane.vue'
import MatcherPairsPane from './components/MatcherPairsPane.vue'
import MatcherResourcePane from './components/MatcherResourcePane.vue'
import MatcherToolbar from './components/MatcherToolbar.vue'
import type {
  AlertMessage,
  AlertType,
  MatchRow,
  MatcherBootstrapData,
  MatcherInitialMatch,
  ObjectSelectionRow,
  MatcherObjectPath,
  MatcherResourceNode,
  ResourceRow,
  ResourceSortKey,
} from './types'

const props = defineProps<MatcherBootstrapData>()
const { t } = useI18n()

// Why: keep component code on the standard `t('namespace.key')` path while
// tolerating older server payloads during rollout if a locale key is missing.
const translateMatcherLabel = (key: keyof MatcherBootstrapData['labels']): string => {
  const i18nKey = `asMatcher.${key}`
  const translated = String(t(i18nKey))
  if (translated !== i18nKey) {
    return translated
  }
  return props.labels[key]
}

const matcherLabels = computed<MatcherBootstrapData['labels']>(() => ({
  filterObjects: translateMatcherLabel('filterObjects'),
  filterResources: translateMatcherLabel('filterResources'),
  pair: translateMatcherLabel('pair'),
  pairSelectedObjects: translateMatcherLabel('pairSelectedObjects'),
  restartMatching: translateMatcherLabel('restartMatching'),
  reviewMatches: translateMatcherLabel('reviewMatches'),
  objects: translateMatcherLabel('objects'),
  resources: translateMatcherLabel('resources'),
  pairs: translateMatcherLabel('pairs'),
  selectAll: translateMatcherLabel('selectAll'),
  file: translateMatcherLabel('file'),
  level: translateMatcherLabel('level'),
  title: translateMatcherLabel('title'),
  identifier: translateMatcherLabel('identifier'),
  dates: translateMatcherLabel('dates'),
  selectedResource: translateMatcherLabel('selectedResource'),
  targetResource: translateMatcherLabel('targetResource'),
  noneSelected: translateMatcherLabel('noneSelected'),
  selectedObjects: translateMatcherLabel('selectedObjects'),
  deleteMatch: translateMatcherLabel('deleteMatch'),
  noResourceSelected: translateMatcherLabel('noResourceSelected'),
  noObjectsSelected: translateMatcherLabel('noObjectsSelected'),
  duplicateMatch: translateMatcherLabel('duplicateMatch'),
  pairRequestFailed: translateMatcherLabel('pairRequestFailed'),
  deleteRequestFailed: translateMatcherLabel('deleteRequestFailed'),
  noPairsYet: translateMatcherLabel('noPairsYet'),
}))

const reviewUrl = getIngestUploadAsReviewMatchesUrl(props.dipUuid)
const resetUrl = getIngestUploadAsResetUrl(props.dipUuid)
const resetAvailable = Boolean(props.resetAvailable)

const normalizeText = (value: unknown): string => {
  if (typeof value === 'string') {
    return value
  }
  if (value == null) {
    return ''
  }
  return String(value)
}

// Flatten the ArchivesSpace hierarchy once so the UI can sort/filter rows locally
// without asking the server for another representation of the same tree.
const flattenResourceTree = (root: MatcherResourceNode): ResourceRow[] => {
  const rows: ResourceRow[] = []
  let sortPosition = 0

  const visit = (node: MatcherResourceNode, depth: number) => {
    rows.push({
      id: `resource-${rows.length + 1}`,
      resourceId: normalizeText(node.id),
      depth,
      sortPosition,
      levelOfDescription: normalizeText(node.levelOfDescription),
      title: normalizeText(node.title),
      identifier: normalizeText(node.identifier),
      dates: normalizeText(node.dates),
    })

    sortPosition += 1

    const children = Array.isArray(node.children) ? node.children : []
    for (const child of children) {
      visit(child, depth + 1)
    }
  }

  visit(root, 0)
  return rows
}

const objectFilter = ref('')
const resourceFilter = ref('')
const selectedResourceId = ref<string | null>(null)
const resourceSorting = ref<SortingState>([{ id: 'level', desc: false }])
const pairsSorting = ref<SortingState>([
  { id: 'resourceOrder', desc: false },
  { id: 'createdOrder', desc: false },
])
const selectedObjectUuids = ref(new Set<string>())
const lastCheckedVisibleIndex = ref<number | null>(null)
const alerts = ref<AlertMessage[]>([])
const pairs = ref<MatchRow[]>([])
const deletingPairIds = ref(new Set<number>())

let nextAlertId = 1
let nextPairLocalId = 1
let nextPairCreatedOrder = 1

const resourceRows = flattenResourceTree(props.resourceData)
const resourceRowsById = new Map(resourceRows.map(row => [row.resourceId, row]))
const objectRows = [...props.objectPaths].sort((a, b) => a.path.localeCompare(b.path, undefined, { sensitivity: 'base' }))
const objectPathByUuid = new Map(objectRows.map(item => [item.uuid, item.path]))

const resourceColumns: ColumnDef<ResourceRow>[] = [
  {
    id: 'level',
    accessorFn: row => row.levelOfDescription,
    sortingFn: (left, right) => left.original.sortPosition - right.original.sortPosition,
  },
  { id: 'title', accessorKey: 'title' },
  { id: 'identifier', accessorKey: 'identifier' },
  { id: 'dates', accessorKey: 'dates' },
]

const pairColumns: ColumnDef<MatchRow>[] = [
  {
    id: 'resourceOrder',
    accessorFn: row => row.resourceSortPosition ?? Number.MAX_SAFE_INTEGER,
    sortingFn: (left, right) => {
      const leftPosition = left.original.resourceSortPosition ?? Number.MAX_SAFE_INTEGER
      const rightPosition = right.original.resourceSortPosition ?? Number.MAX_SAFE_INTEGER
      if (leftPosition !== rightPosition) {
        return leftPosition - rightPosition
      }
      return left.original.createdOrder - right.original.createdOrder
    },
  },
  { id: 'createdOrder', accessorKey: 'createdOrder' },
  { id: 'file', accessorKey: 'objectPath' },
  { id: 'title', accessorKey: 'title' },
  { id: 'identifier', accessorKey: 'identifier' },
  { id: 'dates', accessorKey: 'dates' },
]

const addAlert = (type: AlertType, message: string) => {
  alerts.value = [...alerts.value, { id: nextAlertId, type, message }]
  nextAlertId += 1
}

const dismissAlert = (id: number) => {
  alerts.value = alerts.value.filter(alert => alert.id !== id)
}

const pairedObjectUuidSet = computed(() => {
  return new Set(pairs.value.map(pair => pair.objectUuid))
})

const pairedResourceIdSet = computed(() => {
  return new Set(pairs.value.map(pair => pair.resourceId))
})

const selectedResource = computed(() => {
  if (!selectedResourceId.value) {
    return null
  }
  return resourceRowsById.get(selectedResourceId.value) ?? null
})

const objectSelectionRows = computed<ObjectSelectionRow[]>(() => {
  const filterTerm = objectFilter.value.trim().toLowerCase()
  const pairedSet = pairedObjectUuidSet.value
  const checkedSet = selectedObjectUuids.value

  return objectRows
    .filter(item => filterTerm === '' || item.path.toLowerCase().includes(filterTerm))
    .map(item => ({
      ...item,
      isPaired: pairedSet.has(item.uuid),
      isChecked: checkedSet.has(item.uuid),
    }))
})

const totalSelectedObjectCount = computed(() => {
  let count = 0
  const pairedSet = pairedObjectUuidSet.value
  for (const uuid of selectedObjectUuids.value) {
    if (!pairedSet.has(uuid)) {
      count += 1
    }
  }
  return count
})

const visibleSelectableObjectUuids = computed(() => {
  return objectSelectionRows.value.filter(item => !item.isPaired).map(item => item.uuid)
})

const allVisibleObjectsSelected = computed(() => {
  const visibleUuids = visibleSelectableObjectUuids.value
  if (visibleUuids.length === 0) {
    return false
  }

  for (const uuid of visibleUuids) {
    if (!selectedObjectUuids.value.has(uuid)) {
      return false
    }
  }

  return true
})

const someVisibleObjectsSelected = computed(() => {
  const visibleUuids = visibleSelectableObjectUuids.value
  if (visibleUuids.length === 0) {
    return false
  }

  let selectedCount = 0
  for (const uuid of visibleUuids) {
    if (selectedObjectUuids.value.has(uuid)) {
      selectedCount += 1
    }
  }

  return selectedCount > 0 && selectedCount < visibleUuids.length
})

const filteredResourceSourceRows = computed(() => {
  const filterTerm = resourceFilter.value.trim().toLowerCase()
  const rows = filterTerm === ''
    ? resourceRows
    : resourceRows.filter((row) => {
        return [row.levelOfDescription, row.title, row.identifier, row.dates]
          .join(' ')
          .toLowerCase()
          .includes(filterTerm)
      })

  return rows
})

const resourceTable = useVueTable({
  get data() {
    return filteredResourceSourceRows.value
  },
  columns: resourceColumns,
  enableSortingRemoval: false,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  state: {
    get sorting() {
      return resourceSorting.value
    },
  },
  onSortingChange: (updater) => {
    resourceSorting.value = functionalUpdate(updater, resourceSorting.value)
  },
})

const pairsTable = useVueTable({
  get data() {
    return pairs.value
  },
  columns: pairColumns,
  enableSortingRemoval: false,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  state: {
    get sorting() {
      return pairsSorting.value
    },
  },
  onSortingChange: (updater) => {
    pairsSorting.value = functionalUpdate(updater, pairsSorting.value)
  },
})

const filteredResourceRows = computed(() => {
  return resourceTable.getRowModel().rows.map(row => row.original)
})

const sortedPairs = computed(() => {
  return pairsTable.getRowModel().rows.map(row => row.original)
})

const pairButtonDisabled = computed(() => {
  return !selectedResource.value || totalSelectedObjectCount.value === 0
})

const sortIconClass = (key: ResourceSortKey): string => {
  const column = resourceTable.getColumn(key === 'sortPosition' ? 'level' : key)
  const state = column?.getIsSorted()
  if (!state) {
    return 'fa fa-sort text-muted'
  }

  return state === 'asc' ? 'fa fa-sort-asc' : 'fa fa-sort-desc'
}

const setResourceSort = (key: ResourceSortKey) => {
  const column = resourceTable.getColumn(key === 'sortPosition' ? 'level' : key)
  column?.toggleSorting()
}

const toggleResourceSelection = (resourceId: string) => {
  selectedResourceId.value = selectedResourceId.value === resourceId ? null : resourceId
}

// Keep multi-select range behavior in the object pane so users can pair batches
// quickly without leaving the current matcher page.
const toggleObjectSelection = (uuid: string, checked: boolean, visibleIndex: number, shiftPressed: boolean) => {
  const updated = new Set(selectedObjectUuids.value)

  if (checked) {
    updated.add(uuid)

    if (shiftPressed && lastCheckedVisibleIndex.value !== null) {
      const start = Math.min(lastCheckedVisibleIndex.value, visibleIndex)
      const end = Math.max(lastCheckedVisibleIndex.value, visibleIndex)
      const range = objectSelectionRows.value.slice(start, end + 1)
      for (const item of range) {
        if (!item.isPaired) {
          updated.add(item.uuid)
        }
      }
    }

    lastCheckedVisibleIndex.value = visibleIndex
  } else {
    updated.delete(uuid)
  }

  selectedObjectUuids.value = updated
}

const onObjectCheckboxChange = (event: Event, uuid: string, visibleIndex: number) => {
  const target = event.target
  if (!(target instanceof HTMLInputElement)) {
    return
  }

  const shiftPressed = event instanceof MouseEvent && event.shiftKey
  toggleObjectSelection(uuid, target.checked, visibleIndex, shiftPressed)
}

const setVisibleObjectSelection = (checked: boolean) => {
  const updated = new Set(selectedObjectUuids.value)

  for (const uuid of visibleSelectableObjectUuids.value) {
    if (checked) {
      updated.add(uuid)
    } else {
      updated.delete(uuid)
    }
  }

  selectedObjectUuids.value = updated
}

const onSelectAllVisibleChange = (event: Event) => {
  const target = event.target
  if (!(target instanceof HTMLInputElement)) {
    return
  }
  setVisibleObjectSelection(target.checked)
}

const buildMatchRow = (fileUuid: string, resourceNode: MatcherResourceNode): MatchRow | null => {
  const objectPath = objectPathByUuid.get(fileUuid)
  if (!objectPath) {
    return null
  }

  const resourceId = normalizeText(resourceNode.id)
  const visibleResource = resourceRowsById.get(resourceId)

  const row: MatchRow = {
    localId: nextPairLocalId,
    createdOrder: nextPairCreatedOrder,
    objectUuid: fileUuid,
    objectPath,
    resourceId,
    resourceSortPosition: visibleResource?.sortPosition ?? null,
    levelOfDescription: visibleResource?.levelOfDescription ?? normalizeText(resourceNode.levelOfDescription),
    title: visibleResource?.title ?? normalizeText(resourceNode.title),
    identifier: visibleResource?.identifier ?? normalizeText(resourceNode.identifier),
    dates: visibleResource?.dates ?? normalizeText(resourceNode.dates),
  }

  nextPairLocalId += 1
  nextPairCreatedOrder += 1
  return row
}

const addPairFromCurrentSelection = (objectItem: MatcherObjectPath, resource: ResourceRow) => {
  const row: MatchRow = {
    localId: nextPairLocalId,
    createdOrder: nextPairCreatedOrder,
    objectUuid: objectItem.uuid,
    objectPath: objectItem.path,
    resourceId: resource.resourceId,
    resourceSortPosition: resource.sortPosition,
    levelOfDescription: resource.levelOfDescription,
    title: resource.title,
    identifier: resource.identifier,
    dates: resource.dates,
  }

  nextPairLocalId += 1
  nextPairCreatedOrder += 1
  pairs.value = [...pairs.value, row]
}

const initializePairs = (initialMatches: MatcherInitialMatch[]) => {
  const initialRows: MatchRow[] = []
  for (const match of initialMatches) {
    const row = buildMatchRow(match.file_uuid, match.resource)
    if (row) {
      initialRows.push(row)
    }
  }
  pairs.value = initialRows
}

const pairSelectedObjects = async () => {
  dismissAllAlerts()

  const resource = selectedResource.value
  if (!resource) {
    addAlert('warning', matcherLabels.value.noResourceSelected)
    return
  }

  const selectedObjects = objectRows.filter((item) => {
    return selectedObjectUuids.value.has(item.uuid) && !pairedObjectUuidSet.value.has(item.uuid)
  })

  if (selectedObjects.length === 0) {
    addAlert('warning', matcherLabels.value.noObjectsSelected)
    return
  }

  const succeededObjectUuids = new Set<string>()

  for (const objectItem of selectedObjects) {
    try {
      const result = await createArchivesSpacePair({
        dipUuid: props.dipUuid,
        resourceId: resource.resourceId,
        fileUuid: objectItem.uuid,
      })

      if (result === 'created') {
        addPairFromCurrentSelection(objectItem, resource)
        succeededObjectUuids.add(objectItem.uuid)
        continue
      }

      if (result === 'duplicate') {
        addAlert('warning', `${matcherLabels.value.duplicateMatch} (${objectItem.path})`)
        continue
      }
    } catch {
      addAlert('danger', `${matcherLabels.value.pairRequestFailed} (${objectItem.path})`)
    }
  }

  if (succeededObjectUuids.size > 0) {
    const updated = new Set(selectedObjectUuids.value)
    for (const uuid of succeededObjectUuids) {
      updated.delete(uuid)
    }
    selectedObjectUuids.value = updated
    selectedResourceId.value = null
  }
}

const dismissAllAlerts = () => {
  alerts.value = []
}

const removePair = async (pair: MatchRow) => {
  const deleting = new Set(deletingPairIds.value)
  deleting.add(pair.localId)
  deletingPairIds.value = deleting

  try {
    await deleteArchivesSpacePair({
      dipUuid: props.dipUuid,
      resourceId: pair.resourceId,
      fileUuid: pair.objectUuid,
    })
    pairs.value = pairs.value.filter(item => item.localId !== pair.localId)
  } catch {
    addAlert('danger', `${matcherLabels.value.deleteRequestFailed} (${pair.objectPath})`)
  } finally {
    const updatedDeleting = new Set(deletingPairIds.value)
    updatedDeleting.delete(pair.localId)
    deletingPairIds.value = updatedDeleting
  }
}

initializePairs(props.initialMatches)
</script>

<template>
  <div class="as-matcher">
    <MatcherAlerts
      :alerts="alerts"
      @dismiss="dismissAlert"
    />

    <MatcherToolbar
      :labels="matcherLabels"
      :review-url="reviewUrl"
      :reset-url="resetUrl"
      :reset-available="resetAvailable"
      :pair-disabled="pairButtonDisabled"
      @pair="pairSelectedObjects"
    />

    <div class="as-matcher-grid">
      <MatcherObjectPane
        :labels="matcherLabels"
        :object-filter="objectFilter"
        :rows="objectSelectionRows"
        :selected-objects-count="totalSelectedObjectCount"
        :all-visible-objects-selected="allVisibleObjectsSelected"
        :some-visible-objects-selected="someVisibleObjectsSelected"
        @update:object-filter="objectFilter = $event"
        @select-all-change="onSelectAllVisibleChange"
        @object-change="onObjectCheckboxChange"
      />

      <MatcherResourcePane
        :labels="matcherLabels"
        :resource-filter="resourceFilter"
        :rows="filteredResourceRows"
        :selected-resource-id="selectedResourceId"
        :paired-resource-ids="pairedResourceIdSet"
        :sort-icon-class="sortIconClass"
        @update:resource-filter="resourceFilter = $event"
        @sort="setResourceSort"
        @select-resource="toggleResourceSelection"
      />

      <MatcherPairsPane
        :labels="matcherLabels"
        :pairs="sortedPairs"
        :deleting-pair-ids="deletingPairIds"
        @remove-pair="removePair"
      />
    </div>
  </div>
</template>

<style>
/* Why: keep matcher-specific layout and interaction styles with the matcher app
 * so the Django template no longer needs a dedicated legacy stylesheet.
 */

.as-matcher {
  margin-top: 15px;
}

.as-matcher-alerts {
  margin-bottom: 10px;
}

.as-matcher-alerts .alert {
  margin-bottom: 8px;
}

.as-matcher-toolbar {
  position: sticky;
  top: 57px;
  z-index: 20;
  margin-bottom: 12px;
}

.as-matcher-toolbar.well {
  padding: 10px 12px;
}

.as-matcher-toolbar-body {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}

.as-matcher-toolbar-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.as-matcher-toolbar-actions {
  justify-content: flex-start;
}

.as-matcher-context-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: normal;
  text-align: left;
}

.as-matcher-input-group {
  width: 220px;
}

.as-matcher-grid {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(380px, 1.6fr) minmax(360px, 1.6fr);
  gap: 12px;
  align-items: start;
  justify-content: start;
}

.as-matcher-pane {
  margin-bottom: 0;
}

.as-matcher-pane-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.as-matcher-pane-heading-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.as-matcher-pane-heading .label {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border: 1px solid #d9e0e6;
  border-radius: 999px;
  background: #f3f6f9;
  color: #4f5b66;
  font-weight: 600;
  line-height: 1.2;
  text-shadow: none;
}

.as-matcher-pane-heading .label {
  font-size: 11px;
}

.as-matcher-pane-body {
  padding-top: 10px;
}

.as-matcher-pane-body-tight {
  padding-bottom: 0;
}

.as-matcher-pane-filter {
  margin: -10px -15px 0;
  padding: 10px 15px;
  border-bottom: 1px solid #e5e5e5;
  background: #fafafa;
}

.as-matcher-pane-filter .input-group {
  width: 100%;
}

.as-matcher-select-all {
  margin: 0 -15px;
  padding: 8px 15px;
  border-bottom: 1px solid #e5e5e5;
  background: #fbfcfd;
}

.as-matcher-select-all label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding-left: 0;
  font-weight: 600;
  color: #4f5b66;
}

.as-matcher-select-all input[type='checkbox'] {
  position: static;
  margin: 0;
}

.as-matcher-object-list {
  max-height: 520px;
  overflow: auto;
  margin: 0 -15px -15px;
  background: #fff;
}

.as-matcher-object-row {
  border-bottom: 1px solid #f2f2f2;
}

.as-matcher-object-row:last-child {
  border-bottom: 0;
}

.as-matcher-object-row:hover {
  background-color: #f4faf5;
}

.as-matcher-object-row.is-disabled {
  background-color: #fafafa;
}

.as-matcher-object-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0;
  padding: 7px 10px;
  font-weight: normal;
  cursor: pointer;
}

.as-matcher-object-row.is-disabled .as-matcher-object-label {
  cursor: not-allowed;
  color: #888;
}

.as-matcher-object-label input {
  margin-top: 2px;
}

.as-matcher-object-label span {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.as-matcher-table-wrap {
  max-height: 560px;
  overflow: auto;
  padding: 0;
}

.as-matcher-table {
  margin-bottom: 0;
}

.as-matcher-table > thead > tr > th {
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
  white-space: nowrap;
}

.as-matcher-sort-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 600;
  line-height: inherit;
  text-align: left;
}

.as-matcher-sort-btn:hover,
.as-matcher-sort-btn:focus {
  color: inherit;
  text-decoration: none;
}

.as-matcher-sort-btn:focus {
  outline: 2px solid #337ab7;
  outline-offset: 2px;
}

.as-matcher-resource-row {
  cursor: pointer;
}

.as-matcher-resource-row:focus {
  outline: 2px solid #337ab7;
  outline-offset: -2px;
}

.as-matcher-resource-row.is-selected > td {
  background-color: #ffe08a;
}

.as-matcher-resource-row.is-paired > td {
  box-shadow: inset 0 0 0 9999px rgba(92, 184, 92, 0.12);
}

.as-matcher-resource-row.is-selected.is-paired > td {
  background-color: #ffe08a;
  box-shadow: inset 0 0 0 9999px rgba(255, 224, 138, 0.25);
}

.as-matcher-resource-title {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 5px;
}

.as-matcher-resource-branch {
  color: #777;
  font-size: 11px;
}

.as-matcher-actions-col {
  width: 44px;
  text-align: center;
}

.delete-btn {
  padding: 4px 6px;
  background: none;
  border: 1px solid transparent;
  border-radius: 3px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  line-height: 1;
}

.delete-btn:hover,
.delete-btn:focus {
  background-color: #f5f5f5;
}

.delete-btn:focus {
  outline: 2px solid #337ab7;
  outline-offset: 2px;
}

.delete-btn:hover,
.delete-btn:focus {
  color: #d9534f;
  border-color: #d9534f;
}

.delete-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.atk-matcher-match-item:hover {
  background-color: #f4faf5;
}

@media (max-width: 1399px) {
  .as-matcher-grid {
    grid-template-columns: minmax(240px, 1fr) minmax(340px, 1.4fr);
  }

  .as-matcher-grid > :last-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 991px) {
  .as-matcher-toolbar {
    position: static;
  }

  .as-matcher-input-group {
    width: 100%;
    max-width: 340px;
  }

  .as-matcher-grid {
    grid-template-columns: 1fr;
  }

  .as-matcher-object-list,
  .as-matcher-table-wrap {
    max-height: none;
  }
}
</style>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ref } from 'vue'
import TreeView from '@/shared/components/TreeView.vue'
import type { FileNode } from '@/browser/types'
import type { SourceLocation } from '@/shared/http/transfer'
import type { TreeFocusOptions, TreeNode, TreeNodeContext } from '@/shared/components/TreeView.vue'

const { t } = useI18n()

const treeViewRef = ref<InstanceType<typeof TreeView>>()
const selectedNode = ref<FileNode | undefined>()

// Expose method to focus the tree view for external callers.
const focusTreeView = (options?: TreeFocusOptions) => {
  if (treeViewRef.value) {
    treeViewRef.value.focusTree(options)
  }
}

defineExpose({
  focusTreeView,
})

const props = defineProps<{
  currentLocation: string
  enabledLocations: SourceLocation[]
  loading: boolean
  apiError: string | null
  fileNodes: FileNode[]
  transferType: string
  expandedPaths: string[]
}>()

const emit = defineEmits<{
  'update:currentLocation': [value: string]
  'expand': [node: FileNode]
  'toggle': [path: string]
  'add': [node: FileNode]
  'escape': []
}>()

const toFileNode = (node: TreeNode): FileNode => node as FileNode

const COMPRESSED_EXTENSIONS = [
  '.zip',
  '.tgz',
  '.tar.gz',
] as const

const isCompressedFile = (node: TreeNode): boolean => {
  const name = toFileNode(node).name.toLowerCase()
  return COMPRESSED_EXTENSIONS.some(ext => name.endsWith(ext))
}

const isNodeAddable = (node: TreeNode, transferType: string): boolean => {
  const fileNode = toFileNode(node)
  const isDir = fileNode.type === 'directory'

  switch (transferType) {
    case 'zipped bag':
    case 'zipfile':
      return !isDir && isCompressedFile(fileNode)
    case 'dspace':
      return isDir || (!isDir && isCompressedFile(fileNode))
    case 'standard':
    case 'unzipped bag':
    case 'disk image':
    case 'dataverse':
    default:
      return isDir
  }
}

// In transfer browsing, directories should remain navigable even when they
// cannot be added for a given transfer type.
const isNodeDisabled = (node: TreeNode, transferType: string): boolean => {
  const fileNode = toFileNode(node)
  return !isNodeAddable(fileNode, transferType) && fileNode.type !== 'directory'
}

const isNodeExpandable = (node: TreeNode): boolean => {
  const fileNode = toFileNode(node)
  return fileNode.type === 'directory' && fileNode.children !== undefined
}

const isDirectoryLike = (node: TreeNode, hasChildren: boolean): boolean => {
  const fileNode = toFileNode(node)
  return fileNode.type === 'directory' || hasChildren
}

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} bytes`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${Math.round(bytes / (1024 * 1024))} MB`
  return `${Math.round(bytes / (1024 * 1024 * 1024))} GB`
}

const buildAriaLabel = (node: TreeNode, context: TreeNodeContext, transferType: string): string => {
  const fileNode = toFileNode(node)
  let label = fileNode.name

  if (!isNodeAddable(fileNode, transferType)) {
    label += ` (${t('fileBrowser.notSelectableFor', { type: transferType })})`
  }

  if (fileNode.display_string) {
    label += ` (${fileNode.display_string})`
  } else if (fileNode.size != null && fileNode.type !== 'directory') {
    label += ` (${formatSize(fileNode.size)})`
  }

  if (fileNode.type === 'directory') {
    label += context.isExpanded ? ` (${t('fileBrowser.expanded')})` : ` (${t('fileBrowser.collapsed')})`
    if (fileNode.children && fileNode.children_fetched) {
      label += fileNode.children.length === 1
        ? ` (${t('fileBrowser.containsOneItem')})`
        : ` (${t('fileBrowser.containsManyItems', { count: fileNode.children.length })})`
    }
  }

  return label
}

const handleLocationSelect = (event: Event) => {
  const target = event.target as HTMLSelectElement | null
  if (target) {
    emit('update:currentLocation', target.value)
  }
}

const handleToggle = (node: TreeNode) => {
  const fileNode = toFileNode(node)
  emit('toggle', fileNode.path)
  if (fileNode.type === 'directory' && !fileNode.children_fetched) {
    emit('expand', fileNode)
  }
}

const handleSelectionChange = (node: TreeNode | undefined) => {
  selectedNode.value = node ? toFileNode(node) : undefined
}

const addSelectedNode = () => {
  if (!selectedNode.value || !isNodeAddable(selectedNode.value, props.transferType)) {
    return
  }
  emit('add', selectedNode.value)
}
</script>

<template>
  <div id="transfer-browse-tree">
    <!-- Source Location Selector -->
    <label
      for="source-location-select"
      class="sr-only"
    >{{ t('fileBrowser.sourceLocation') }}</label>
    <select
      id="source-location-select"
      class="form-control"
      :value="currentLocation"
      aria-describedby="location-help"
      @change="handleLocationSelect"
    >
      <option
        v-for="location in enabledLocations"
        :key="location.uuid"
        :value="location.uuid"
      >
        {{ location.description }}
      </option>
    </select>
    <span
      id="location-help"
      class="sr-only"
    >{{ t('fileBrowser.locationHelp') }}</span>

    <!-- Tree Container -->
    <div
      v-if="currentLocation"
      class="transfer-tree-container"
      role="region"
      :aria-label="t('fileBrowser.browser')"
      :aria-busy="loading"
    >
      <div
        v-if="apiError"
        class="alert alert-danger"
        role="alert"
        aria-live="assertive"
      >
        {{ apiError }}
      </div>
      <TreeView
        v-else
        ref="treeViewRef"
        :items="props.fileNodes"
        :model-value="selectedNode"
        :frame-style="'well'"
        :variant="'compact'"
        :auto-focus-on-mount="true"
        :auto-focus-target="'selected'"
        :get-key="(node) => toFileNode(node).path"
        :get-children="(node) => toFileNode(node).children"
        :expanded="props.expandedPaths"
        :get-disabled="(node) => isNodeDisabled(node, transferType)"
        :get-aria-label="(node, ctx) => buildAriaLabel(node, ctx, transferType)"
        :get-content-class="(node) => {
          const fileNode = toFileNode(node)
          const isAddable = isNodeAddable(node, transferType)
          const isDir = fileNode.type === 'directory'
          const isExpandable = isNodeExpandable(fileNode)
          return {
            'tree-node-selectable': isAddable,
            'tree-node-expandable': isExpandable,
            'tree-node-not-addable': !isAddable,
            'tree-node-not-addable-file': !isAddable && !isDir,
            'tree-node-not-addable-dir': !isAddable && isDir,
          }
        }"
        :scroll-container-selector="'.transfer-tree-container'"
        :scroll-on-select="true"
        :enter-toggles="false"
        :right-toggles="true"
        :on-enter="(node) => {
          if (isNodeAddable(node, transferType)) {
            $emit('add', toFileNode(node))
          }
        }"
        @update:model-value="handleSelectionChange($event as TreeNode | undefined)"
        @toggle="handleToggle($event)"
        @escape="emit('escape')"
      >
        <template #label="{ node, isExpanded, hasChildren }">
          <span class="transfer-node-name">{{ toFileNode(node).name }}</span>
          <span
            v-if="toFileNode(node).display_string"
            class="tree-node-display"
          >({{ toFileNode(node).display_string }})</span>
          <span
            v-else-if="toFileNode(node).size != null && !isDirectoryLike(node, hasChildren)"
            class="tree-node-size"
          >({{ formatSize(toFileNode(node).size ?? 0) }})</span>
          <span
            v-if="!isNodeAddable(node, transferType)"
            class="sr-only"
          >({{ t('fileBrowser.notSelectableFor', { type: transferType }) }})</span>
          <span
            v-if="isDirectoryLike(node, hasChildren)"
            class="sr-only"
          >
            {{ isExpanded ? `(${t('fileBrowser.expanded')})` : `(${t('fileBrowser.collapsed')})` }}
          </span>
        </template>
        <template #children="{ node, hasChildren }">
          <div
            v-if="isDirectoryLike(node, hasChildren) && toFileNode(node).loading"
            class="tree-node-loading"
            role="status"
            aria-live="polite"
          >
            {{ t('transfer.loading') }}
          </div>
          <div
            v-else-if="isDirectoryLike(node, hasChildren) && toFileNode(node).children_fetched && (toFileNode(node).children?.length ?? 0) === 0"
            class="tree-node-empty"
            role="status"
          >
            {{ t('fileBrowser.emptyFolder') }}
          </div>
        </template>
      </TreeView>
    </div>
    <button
      v-if="currentLocation"
      type="button"
      class="btn btn-primary pull-right transfer-tree-add-btn"
      :disabled="!selectedNode || !isNodeAddable(selectedNode, transferType)"
      :aria-label="selectedNode ? t('fileBrowser.addToTransfer', { path: selectedNode.path }) : t('fileBrowser.selectFileOrFolder')"
      @click="addSelectedNode"
    >
      {{ t('transfer.add') }}
    </button>
  </div>
</template>

<style scoped>
#transfer-browse-tree {
  width: 950px;
  margin-bottom: 60px;
  margin-top: 10px;
}

.transfer-tree-container {
  margin-top: 10px;
  margin-bottom: 10px;
  overflow: auto;
  max-height: 30em;
}

.transfer-tree-action {
  border: 0;
  background: none;
  color: #337ab7;
  font-size: 12px;
  padding: 0;
  cursor: pointer;
}

.transfer-tree-action:hover,
.transfer-tree-action:focus {
  color: #23527c;
  text-decoration: underline;
}

:deep(.transfer-tree-container .tree-node-actions) {
  margin-left: 6px !important;
  display: inline-flex;
}

:deep(.transfer-tree-container .tree-node-content > .tree-node-label) {
  flex: 0 1 auto;
}

:deep(.transfer-tree-container .tree) {
  --tree-focus-outline: none;
  --tree-focus-outline-offset: 0;
  --tree-focus-bg: #dfe3e8;
  --tree-compact-focus-bg: #dfe3e8;
  --tree-selected-label-bg: #aaddff;
  --tree-selected-label-weight: bold;
}

:deep(.transfer-tree-container .tree-node-display) {
  color: #666;
}

/* Screen reader only content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Ensure focus indicators are visible */
select:focus,
button:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}
</style>

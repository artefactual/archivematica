<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FileNode } from '@/shared/models'
import { createTreeNodeId } from '@/browser/components/treeNodeId'

const { t } = useI18n()

interface Props {
  node: FileNode
  selectedPath: string
  transferType: string
  expandedPaths?: string[]
  level?: number
  nodeIndex?: number
  totalNodes?: number
}

interface Emits {
  (e: 'select', path: string): void
  (e: 'expand', node: FileNode): void
  (e: 'toggle', path: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Generate unique ID for the node to ensure proper ARIA relationships.
const nodeId = computed(() => createTreeNodeId(props.node.path))

const isDirectory = computed(() => props.node.type === 'directory')
const isSelected = computed(() => props.selectedPath === props.node.path)
const isExpanded = computed(() => (props.expandedPaths ?? []).includes(props.node.path))

// Check if a file can be added based on transfer type.
const canBeAdded = computed(() => {
  const node = props.node
  const transferType = props.transferType
  const isDir = node.type === 'directory'
  const isCompressedFile = !isDir && zipFilter(node)

  switch (transferType) {
    case 'zipped bag':
    case 'zipfile':
      // Only compressed files allowed, no directories.
      return isCompressedFile
    case 'dspace':
      // Both directories and compressed files allowed.
      return isDir || isCompressedFile
    case 'standard':
    case 'unzipped bag':
    case 'disk image':
    case 'dataverse':
    default:
      // Only directories allowed.
      return isDir
  }
})

// Check if file is a compressed file by examining extension.
const zipFilter = (node: FileNode): boolean => {
  const name = node.name.toLowerCase()
  return name.endsWith('.zip') || name.endsWith('.tgz') || name.endsWith('.tar.gz')
}

const handleClick = () => {
  emit('select', props.node.path)
}

// Keyboard event handler is handled by parent TreeView component for better key management.

// Generate accessible label for screen readers to provide full context.
const getNodeLabel = () => {
  let label = props.node.name

  if (!canBeAdded.value) {
    label += ` (${t('fileBrowser.notSelectableFor', { type: props.transferType })})`
  }

  if (props.node.display_string) {
    label += ` (${props.node.display_string})`
  } else if (props.node.size && !isDirectory.value) {
    label += ` (${formatSize(props.node.size)})`
  }

  if (isDirectory.value) {
    label += isExpanded.value ? ` (${t('fileBrowser.expanded')})` : ` (${t('fileBrowser.collapsed')})`
    if (props.node.children && props.node.children_fetched) {
      label += ` containing ${props.node.children.length} items`
    }
  }

  return label
}

const handleToggle = () => {
  if (isDirectory.value) {
    const wasExpanded = isExpanded.value
    emit('toggle', props.node.path)

    // If we're expanding and haven't fetched children yet, trigger child loading.
    if (!wasExpanded && !props.node.children_fetched) {
      // Emit expand event to load children.
      emit('expand', props.node)
    }
  }
}

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} bytes`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${Math.round(bytes / (1024 * 1024))} MB`
  return `${Math.round(bytes / (1024 * 1024 * 1024))} GB`
}
</script>

<template>
  <div
    :id="nodeId"
    class="tree-node"
    role="treeitem"
    :aria-level="String(props.level ?? 1)"
    :aria-selected="isSelected"
    :aria-expanded="isDirectory ? isExpanded : undefined"
    :aria-disabled="!canBeAdded"
  >
    <div
      class="tree-node-content"
      :class="{
        selected: isSelected,
        disabled: !canBeAdded,
        selectable: canBeAdded,
      }"
      :aria-label="getNodeLabel()"
      @click="handleClick"
    >
      <span
        v-if="isDirectory"
        class="tree-node-toggle"
        role="button"
        :aria-label="isExpanded ? t('fileBrowser.collapseFolder') : t('fileBrowser.expandFolder')"
        :tabindex="-1"
        @click.stop="handleToggle"
      >
        <i
          class="fa tree-icon"
          :class="isExpanded ? 'fa-folder-open tree-icon-expanded' : 'fa-folder tree-icon-collapsed'"
        />
      </span>
      <span
        v-else
        class="tree-node-icon"
        aria-hidden="true"
      >
        <i class="fa fa-file tree-icon tree-icon-file" />
      </span>

      <span class="tree-node-label">{{ node.name }}</span>
      <span
        v-if="node.display_string"
        class="tree-node-display"
      >({{ node.display_string }})</span>
      <span
        v-else-if="node.size && !isDirectory"
        class="tree-node-size"
      >({{ formatSize(node.size) }})</span>

      <!-- Screen reader only status information -->
      <span
        v-if="!canBeAdded"
        class="sr-only"
      >({{ t('fileBrowser.notSelectableFor', { type: transferType }) }})</span>
      <span
        v-if="isDirectory"
        class="sr-only"
      >
        {{ isExpanded ? `(${t('fileBrowser.expanded')})` : `(${t('fileBrowser.collapsed')})` }}
      </span>
    </div>

    <div
      v-if="isDirectory && isExpanded"
      class="tree-node-children"
      role="group"
    >
      <div
        v-if="node.loading"
        class="tree-node-loading"
        role="status"
        aria-live="polite"
      >
        {{ t('transfer.loading') }}
      </div>
      <div
        v-else-if="(!node.children || node.children.length === 0) && node.children_fetched"
        class="tree-node-empty"
        role="status"
      >
        {{ t('fileBrowser.emptyFolder') }}
      </div>
      <TreeViewNode
        v-for="child in node.children || []"
        :key="child.path"
        :node="child"
        :selected-path="selectedPath"
        :transfer-type="transferType"
        :expanded-paths="expandedPaths"
        :level="(props.level ?? 1) + 1"
        :node-index="0"
        :total-nodes="(node.children || []).length"
        @select="$emit('select', $event)"
        @expand="$emit('expand', $event)"
        @toggle="$emit('toggle', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.tree-node {
  user-select: none;
}

.tree-node:focus {
  outline: none;
}

.tree-node-content {
  display: flex;
  align-items: center;
  padding: 2px 4px;
  min-height: 20px;
  line-height: 1.4;
  cursor: default;
}

.tree-node-content.selectable {
  cursor: pointer;
}

.tree-node-content.selectable:hover {
  background-color: #f5f5f5;
}

.tree-node-content.selected {
  background-color: #0073aa !important;
  color: #fff;
  position: relative;
}

/* Add visual indicator for keyboard focus within selected node */
.tree-node-content.selected::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid #fff;
  border-radius: 2px;
  pointer-events: none;
}

.tree-node-content.selected .tree-node-size,
.tree-node-content.selected .tree-node-display {
  color: #fff;
}

/* Fix contrast for disabled items when selected */
.tree-node-content.selected.disabled {
  background-color: #0073aa !important;
  color: #fff !important;
  opacity: 1;
}

.tree-node-content.selected.disabled .tree-node-size,
.tree-node-content.selected.disabled .tree-node-display {
  color: #fff !important;
}

.tree-node-content.disabled {
  opacity: 0.8;
  text-decoration: line-through;
  color: #767676;
  cursor: not-allowed;
}

.tree-node-toggle {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  margin-right: 4px;
}

.tree-node-toggle:focus {
  outline: 2px solid #007cba;
  outline-offset: 1px;
}

.tree-node-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 4px;
}

.tree-icon {
  width: 16px;
  height: 16px;
  display: block;
  line-height: 16px;
  text-align: center;
  font-size: 14px;
}

.tree-icon-expanded {
  color: #d4af37; /* Golden yellow for open folders */
}

.tree-icon-collapsed {
  color: #f1c40f; /* Bright yellow for closed folders */
}

.tree-icon-file {
  color: #95a5a6; /* Light gray for files */
}

.tree-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node-size {
  color: #595959;
  margin-left: 4px;
}

.tree-node-display {
  color: #595959;
  margin-left: 4px;
}

.tree-node-children {
  margin-left: 20px;
}

/* Ensure disabled files can't be hovered */
.tree-node-content.disabled:hover {
  background-color: transparent !important;
}

.tree-node-loading {
  padding: 2px 4px;
  color: #595959;
  font-style: italic;
  font-size: 12px;
}

.tree-node-empty {
  padding: 2px 4px;
  color: #767676;
  font-style: italic;
  font-size: 12px;
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

/* High contrast mode support */
@media (prefers-contrast: high) {
  .tree-node-content.selected {
    background-color: #000 !important;
    color: #fff;
    border: 2px solid #fff;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .tree-node-content {
    transition: none;
  }
}
</style>

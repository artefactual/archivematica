<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import TreeViewNode from '@/browser/components/TreeViewNode.vue'
import type { FileNode, TreeSelection } from '@/shared/models'
import { createTreeNodeId } from '@/browser/components/treeNodeId'

const { t } = useI18n()

interface Props {
  nodes: FileNode[]
  selectedPath: string
  transferType: string
  expandedPaths: string[]
}

interface Emits {
  (e: 'select', selection: TreeSelection): void
  (e: 'expand', node: FileNode): void
  (e: 'toggle', path: string): void
  (e: 'add'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const treeViewRef = ref<HTMLElement>()

// Create a flat list of all visible nodes for efficient keyboard navigation.
const flatNodeList = computed(() => {
  const result: { node: FileNode, level: number }[] = []

  const addNode = (node: FileNode, level: number) => {
    result.push({ node, level })
    if (
      node.type === 'directory'
      && props.expandedPaths.includes(node.path)
      && node.children
    ) {
      node.children.forEach(child => addNode(child, level + 1))
    }
  }

  props.nodes.forEach(node => addNode(node, 1))
  return result
})

const getFlatNode = (index: number) => flatNodeList.value[index] ?? null

const isCompressedFile = (node: FileNode): boolean => {
  const name = node.name.toLowerCase()
  return (
    name.endsWith('.zip')
    || name.endsWith('.tgz')
    || name.endsWith('.tar.gz')
  )
}

const isNodeAddable = (node: FileNode): boolean => {
  const isDir = node.type === 'directory'

  switch (props.transferType) {
    case 'zipped bag':
    case 'zipfile':
      return !isDir && isCompressedFile(node)
    case 'dspace':
      return isDir || (!isDir && isCompressedFile(node))
    case 'standard':
    case 'unzipped bag':
    case 'disk image':
    case 'dataverse':
    default:
      return isDir
  }
}

const emitSelection = (node: FileNode) => {
  emit('select', {
    path: node.path,
    canAdd: isNodeAddable(node),
  })
}

// Handle focus to ensure keyboard navigation works when tree receives focus.
const handleFocus = () => {
  const nodes = flatNodeList.value
  if (!props.selectedPath && nodes.length > 0) {
    const firstIndex = nodes.findIndex(item => isNodeAddable(item.node))
    const targetIndex = firstIndex !== -1 ? firstIndex : 0
    const target = getFlatNode(targetIndex)
    if (!target) return
    emitSelection(target.node)
    currentFocusIndex.value = targetIndex
    // Scroll to the first node to make it visible.
    nextTick(() => {
      scrollToFocusedNode(target.node.path)
    })
  } else {
    // Ensure currentFocusIndex matches the selected path for consistency.
    updateFocusIndex()
    // Scroll to the selected node to ensure visibility.
    if (props.selectedPath) {
      nextTick(() => {
        scrollToFocusedNode(props.selectedPath)
      })
    }
  }
}

const currentFocusIndex = ref(0)

// Find current focused node index in the flat list.
const updateFocusIndex = () => {
  const index = flatNodeList.value.findIndex(
    item => item.node.path === props.selectedPath,
  )
  if (index !== -1) {
    currentFocusIndex.value = index
  }
}

// Update focus index when selection changes to keep state synchronized.
const handleSelect = (path: string) => {
  const index = flatNodeList.value.findIndex(item => item.node.path === path)
  if (index === -1) return
  const target = getFlatNode(index)
  if (!target) return
  emitSelection(target.node)
  currentFocusIndex.value = index
  // Ensure the tree view has focus for keyboard navigation
  if (treeViewRef.value) {
    treeViewRef.value.focus()
  }
  // Delay focus index update so flatNodeList is current after DOM changes.
  nextTick(() => {
    updateFocusIndex()
  })
}

const handleToggle = (path: string) => {
  emit('toggle', path)
  // Update flat list after toggle and ensure focus is maintained.
  nextTick(() => {
    updateFocusIndex()
    // After expanding, focus the tree view to ensure keyboard navigation works.
    if (treeViewRef.value) {
      treeViewRef.value.focus()
    }
  })
}

// Handle keyboard navigation for accessibility and user experience.
const handleKeyDown = (event: KeyboardEvent) => {
  const flatNodes = flatNodeList.value
  if (flatNodes.length === 0) return

  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      if (currentFocusIndex.value > 0) {
        const previousIndex = currentFocusIndex.value - 1
        const previousNode = getFlatNode(previousIndex)
        if (!previousNode) return
        currentFocusIndex.value = previousIndex
        emitSelection(previousNode.node)
        nextTick(() => {
          scrollToFocusedNode(previousNode.node.path)
        })
      }
      break

    case 'ArrowDown':
      event.preventDefault()
      // Check if current node is loading to prevent navigation during load.
      const currentEntryDown = getFlatNode(currentFocusIndex.value)
      if (currentEntryDown?.node.loading) {
        return // Don't navigate while loading.
      }

      if (currentFocusIndex.value < flatNodes.length - 1) {
        const nextIndex = currentFocusIndex.value + 1
        const nextNode = getFlatNode(nextIndex)
        if (!nextNode) return
        currentFocusIndex.value = nextIndex
        emitSelection(nextNode.node)
        nextTick(() => {
          scrollToFocusedNode(nextNode.node.path)
        })
      }
      break

    case 'ArrowLeft':
      event.preventDefault()
      const currentEntryLeft = getFlatNode(currentFocusIndex.value)
      const currentNodeLeft = currentEntryLeft?.node
      if (
        currentNodeLeft
        && currentNodeLeft.type === 'directory'
        && props.expandedPaths.includes(currentNodeLeft.path)
      ) {
        // Collapse directory if expanded.
        emit('toggle', currentNodeLeft.path)
      } else {
        // Move to parent by finding node at lower level.
        const currentLevel = currentEntryLeft?.level
        if (currentLevel === undefined) return
        for (let i = currentFocusIndex.value - 1; i >= 0; i--) {
          const candidate = getFlatNode(i)
          if (candidate && candidate.level < currentLevel) {
            currentFocusIndex.value = i
            emitSelection(candidate.node)
            break
          }
        }
      }
      break

    case 'ArrowRight':
      event.preventDefault()
      const currentEntryRight = getFlatNode(currentFocusIndex.value)
      const currentNodeRight = currentEntryRight?.node
      if (currentNodeRight && currentNodeRight.type === 'directory') {
        // Don't expand if already loading to prevent duplicate requests.
        if (currentNodeRight.loading) return

        if (!props.expandedPaths.includes(currentNodeRight.path)) {
          // Expand if collapsed - emit toggle to update visual state.
          emit('toggle', currentNodeRight.path)
          // Also emit expand to load children if not yet loaded.
          if (!currentNodeRight.children_fetched) {
            emit('expand', currentNodeRight)
          }
        } else if (
          currentNodeRight.children
          && currentNodeRight.children.length > 0
        ) {
          // Move to first child if expanded and has children.
          const nextIndex = currentFocusIndex.value + 1
          const nextNode = getFlatNode(nextIndex)
          if (nextNode) {
            currentFocusIndex.value = nextIndex
            emitSelection(nextNode.node)
            nextTick(() => {
              scrollToFocusedNode(nextNode.node.path)
            })
          }
        }
      }
      break

    case 'Enter':
    case ' ':
      event.preventDefault()
      const currentEntry = getFlatNode(currentFocusIndex.value)
      const currentNode = currentEntry?.node
      if (currentNode) {
        if (currentNode.type === 'directory') {
          // For directories, toggle expansion with Enter/Space.
          emit('toggle', currentNode.path)
          // If expanding and children not loaded, emit expand to load them.
          if (
            !props.expandedPaths.includes(currentNode.path)
            && !currentNode.children_fetched
          ) {
            emit('expand', currentNode)
          }
        } else {
          // For files, emit selection to update button state.
          emitSelection(currentNode)
        }
      }
      break

    case 'Home':
      event.preventDefault()
      if (flatNodes.length > 0) {
        const firstNode = getFlatNode(0)
        if (!firstNode) return
        currentFocusIndex.value = 0
        emitSelection(firstNode.node)
        nextTick(() => {
          scrollToFocusedNode(firstNode.node.path)
        })
      }
      break

    case 'End':
      event.preventDefault()
      if (flatNodes.length > 0) {
        const lastIndex = flatNodes.length - 1
        const lastNode = getFlatNode(lastIndex)
        if (!lastNode) return
        currentFocusIndex.value = lastIndex
        emitSelection(lastNode.node)
        nextTick(() => {
          scrollToFocusedNode(lastNode.node.path)
        })
      }
      break

    case 'a':
    case 'A':
      event.preventDefault()
      const currentSelectedNode = getFlatNode(currentFocusIndex.value)?.node
      if (
        currentSelectedNode
        && isNodeAddable(currentSelectedNode)
        && props.selectedPath
      ) {
        emit('add')
      }
      break
  }
}

// Expose method to focus the tree view for external callers.
const focusTree = () => {
  if (treeViewRef.value) {
    treeViewRef.value.focus()
  }
}

// Scroll the focused node into view if it's outside the visible area.
const scrollToFocusedNode = (path: string) => {
  // Find the node element by its path-based ID.
  const nodeId = createTreeNodeId(path)
  const nodeElement = document.getElementById(nodeId)

  if (nodeElement) {
    // Find the scroll container for proper scrolling context.
    const scrollContainer = nodeElement.closest('.transfer-tree-container')
    if (scrollContainer) {
      // Calculate if element is visible in scroll container.
      const containerRect = scrollContainer.getBoundingClientRect()
      const elementRect = nodeElement.getBoundingClientRect()

      // Only scroll if element is outside visible area.
      if (
        elementRect.top < containerRect.top
        || elementRect.bottom > containerRect.bottom
      ) {
        nodeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        })
      }
    }
  }
}

defineExpose({
  focusTree,
})
</script>

<template>
  <div
    ref="treeViewRef"
    class="file-tree-view"
    role="tree"
    :aria-label="t('fileBrowser.fileBrowserFor', { type: transferType })"
    tabindex="0"
    @keydown="handleKeyDown"
    @focus="handleFocus"
  >
    <!-- Instructions for screen readers -->
    <div
      class="sr-only"
      role="status"
      aria-live="polite"
    >
      {{ t('fileBrowser.keyboardInstructions') }}
    </div>

    <TreeViewNode
      v-for="(node, index) in nodes"
      :key="node.path"
      :node="node"
      :selected-path="selectedPath"
      :transfer-type="transferType"
      :expanded-paths="props.expandedPaths"
      :node-index="index"
      :total-nodes="nodes.length"
      :level="1"
      @select="handleSelect"
      @expand="$emit('expand', $event)"
      @toggle="handleToggle"
    />

    <div
      v-if="nodes.length === 0"
      class="tree-empty"
      role="status"
    >
      {{ t('fileBrowser.emptyFolder') }}
    </div>
  </div>
</template>

<style scoped>
.file-tree-view {
  position: relative;
}

.file-tree-view:focus {
  outline: none;
}

.tree-empty {
  padding: 12px;
  color: #595959;
  font-style: italic;
  text-align: center;
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
</style>

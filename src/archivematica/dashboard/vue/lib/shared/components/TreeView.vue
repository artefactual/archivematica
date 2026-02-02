<!--
TreeView.vue provides a minimal tree wrapper built on Reka UI. It is intended as a
simple, reusable foundation for the Archivematica Dashboard’s three browsing
contexts such as:
- Ingest browser. Implemented in `lib/aip-browser` and accessed from the Ingest
  tab when previewing packages.
- Metadata editor. Implemented in `lib/md-editor` for the add-metadata-files
  view in the Ingest workflow.
- Transfer browser: implemented in `lib/browser` for the Transfer tab widget
  used to choose contents and start new transfers.

Goals:
- Provide a small, stable tree surface (items + select/toggle events).
- Stay focused on presentation and interaction.
- Support gradual growth as the three use cases converge.

Non-goals:
- Owning data loading (fetching, decoding, lazy loading).
- Encoding Archivematica-specific rules (selection policy, download behavior).
- Acting as a full-featured file browser on its own.

Keyboard Interaction Contract:
- Arrow navigation:
  - Up/Down: move through visible tree items (handled by Reka roving focus).
  - Right: expand a node when `rightToggles` is enabled and node has children.
  - Left: collapse expanded node; otherwise move focus to parent node.
- Activation keys:
  - Enter/Space are handled in `TreeNode` and may toggle or call `onEnter`
    depending on props (`enterToggles`, `onEnter`).
  - App-level meaning of activation remains app-specific (for example add,
    download, or expand-only behavior).
- Escape handoff:
  - `TreeView` emits `escape` on `Esc`.
  - Consumers should route focus to a deterministic control outside the tree
    (for example the Browse button that opened it).
- Autofocus:
  - `autoFocusOnMount` and `autoFocusOnItemsChange` control when focus enters
    the tree.
  - `autoFocusTarget` (`selected` or `first`) controls which node is focused.
-->
<script lang="ts">
export type TreeFrameStyle = 'none' | 'framed' | 'well'
export type TreeVariant = 'default' | 'compact'
export type TreeFocusTarget = 'selected' | 'first'
export type TreeFocusOptions = {
  target?: TreeFocusTarget
}

export type TreeNode = {
  id?: string
  label?: string
  path?: string
  children?: TreeNode[]
}

export type TreeNodeContext = {
  node: TreeNode
  isExpanded: boolean
  isSelected: boolean
  isDisabled: boolean
}
</script>

<script setup lang="ts">
import { TreeRoot } from 'reka-ui'
import TreeNode from '@/shared/components/TreeNode.vue'
import { createTreeNodeKeyHelpers } from '@/shared/components/treeNodeKeys'
import { provideTreeNodeConfig } from '@/shared/components/treeNodeConfig'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  // The array of tree nodes to display in the tree.
  items: TreeNode[]

  // The currently selected tree node. Supports v-model for two-way binding.
  modelValue?: TreeNode

  // Array of node keys that should be expanded by default.
  // Keys are determined by the getKey function or node.id.
  expanded?: string[]

  // Whether multiple nodes can be selected simultaneously.
  // When true, modelValue can be an array (handled by Reka UI).
  multiple?: boolean

  // Function to extract a unique key from a tree node. Defaults to using
  // node.id if available.
  getKey?: (node: TreeNode) => string

  // Function to get the children of a tree node. Defaults to using
  // node.children if available.
  getChildren?: (node: TreeNode) => TreeNode[] | undefined

  // Function to generate a unique DOM ID for a tree node. Used for
  // accessibility and scrolling. Defaults to sanitizing getKey result.
  getNodeId?: (node: TreeNode) => string

  // Function to generate an ARIA label for a tree node. Receives the node and
  // its context (expanded, selected, disabled state).
  getAriaLabel?: (node: TreeNode, context: TreeNodeContext) => string

  // Function to determine if a tree node should be disabled. Disabled nodes
  // cannot be selected or toggled.
  getDisabled?: (node: TreeNode) => boolean

  // Function to get CSS classes for the tree node's content. Can return a
  // string, array of strings, or object of class mappings.
  getContentClass?: (node: TreeNode, context: TreeNodeContext) => string | string[] | Record<string, boolean>

  // CSS selector for the scrollable container. Used for auto-scrolling when
  // nodes are selected.
  scrollContainerSelector?: string

  // Whether to automatically scroll the selected node into view.
  scrollOnSelect?: boolean

  // Presentation variant for density and spacing.
  variant?: TreeVariant

  // Whether pressing Enter key toggles node expansion.
  enterToggles?: boolean

  // Callback function when Enter is pressed on a node.
  onEnter?: (node: TreeNode) => void

  // Whether pressing the right arrow key toggles node expansion.
  rightToggles?: boolean

  // When actions (buttons/icons) in tree nodes should be visible.
  actionsVisibility?: 'always' | 'hover' | 'focus' | 'hover+focus'

  // Whether actions in tree nodes are focusable via keyboard.
  actionsFocusable?: boolean

  // Shared frame style for the tree root.
  frameStyle?: TreeFrameStyle

  // Automatically focus the tree when it mounts.
  autoFocusOnMount?: boolean

  // Automatically focus the tree when root items become available.
  autoFocusOnItemsChange?: boolean

  // Target used by auto focus behavior.
  autoFocusTarget?: TreeFocusTarget
}>(), {
  actionsVisibility: 'always',
  actionsFocusable: true,
  frameStyle: 'none',
  variant: 'default',
  modelValue: undefined,
  expanded: undefined,
  getKey: undefined,
  getChildren: undefined,
  getNodeId: undefined,
  getAriaLabel: undefined,
  getDisabled: undefined,
  getContentClass: undefined,
  scrollContainerSelector: undefined,
  onEnter: undefined,
  autoFocusOnMount: false,
  autoFocusOnItemsChange: false,
  autoFocusTarget: 'selected',
})

const emit = defineEmits<{
  // Emitted when a tree node is selected.
  'select': [node: TreeNode, originalEvent?: Event]
  // Emitted when a tree node is toggled (expanded/collapsed).
  'toggle': [node: TreeNode]
  // Emitted to update the selected node for v-model binding.
  'update:modelValue': [node: TreeNode | undefined]
  // Emitted to update the expanded nodes for v-model binding.
  'update:expanded': [expanded: string[]]
  // Emitted when Escape is pressed while focus is within the tree.
  'escape': []
}>()

// Reference to the root Tree component for focus management.
const treeRootRef = ref<{ $el?: HTMLElement } | null>(null)

// Compute CSS class for actions visibility based on prop.
const actionsVisibilityClass = computed(() => {
  switch (props.actionsVisibility) {
    case 'hover':
      return 'tree-actions-hover'
    case 'focus':
      return 'tree-actions-focus'
    case 'hover+focus':
      return 'tree-actions-hover-focus'
    default:
      return undefined
  }
})

const frameStyleClass = computed(() => {
  switch (props.frameStyle) {
    case 'framed':
      return 'tree-frame-framed'
    case 'well':
      return 'tree-frame-well'
    default:
      return undefined
  }
})

const variantClass = computed(() => (
  props.variant === 'compact' ? 'tree-variant-compact' : undefined
))

const {
  getKey,
  getNodeId,
} = createTreeNodeKeyHelpers<TreeNode>({
  resolveGetKey: () => props.getKey,
  resolveGetNodeId: () => props.getNodeId,
})

// Get children for a tree node.
const getChildren = (node: TreeNode | Record<string, unknown>) => {
  if (props.getChildren) {
    return props.getChildren(node as TreeNode)
  }
  return (node as TreeNode | undefined)?.children
}

const treeNodeConfig = computed(() => ({
  getChildren,
  getNodeId,
  getAriaLabel: props.getAriaLabel,
  getDisabled: props.getDisabled,
  getContentClass: props.getContentClass,
  enterToggles: props.enterToggles,
  onEnter: props.onEnter,
  rightToggles: props.rightToggles,
  actionsFocusable: props.actionsFocusable,
}))

provideTreeNodeConfig(treeNodeConfig)

// Scroll the specified node into view within the scroll container.
const scrollToNode = (node: TreeNode) => {
  const nodeId = getNodeId(node)
  const element = nodeId ? document.getElementById(nodeId) : null
  if (!element) return
  const container = props.scrollContainerSelector
    ? element.closest(props.scrollContainerSelector)
    : element.parentElement
  if (!container) return
  const containerRect = container.getBoundingClientRect()
  const elementRect = element.getBoundingClientRect()
  if (elementRect.top < containerRect.top || elementRect.bottom > containerRect.bottom) {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    element.scrollIntoView({
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
      block: 'nearest',
    })
  }
}

// Handle selection of a tree node.
const handleSelect = (node: TreeNode, originalEvent?: Event) => {
  emit('select', node, originalEvent)
  if (props.scrollOnSelect) {
    nextTick(() => {
      scrollToNode(node)
    })
  }
}

// Watch for changes to the selected node and scroll into view if needed.
watch(
  () => props.modelValue,
  (node) => {
    if (!props.scrollOnSelect || !node) return
    nextTick(() => {
      scrollToNode(node)
    })
  },
)

// Expose a method to focus the tree component.
const focusTree = (options?: TreeFocusOptions) => {
  const rootEl = treeRootRef.value?.$el
  if (!rootEl) return
  const targetOption = options?.target ?? 'selected'
  const selectedItem = targetOption === 'selected'
    ? rootEl.querySelector<HTMLElement>('[role="treeitem"][data-selected]')
    : null
  const firstItem = rootEl.querySelector<HTMLElement>('[role="treeitem"]')
  const target = selectedItem ?? firstItem
  target?.focus()
}

const hasItems = (nodes: TreeNode[]) => nodes.length > 0

onMounted(() => {
  if (!props.autoFocusOnMount || !hasItems(props.items)) return
  nextTick(() => {
    focusTree({ target: props.autoFocusTarget })
  })
})

watch(
  () => props.items,
  (items) => {
    if (!props.autoFocusOnItemsChange) return
    const nowHasItems = hasItems(items)
    if (!nowHasItems) return
    nextTick(() => {
      focusTree({ target: props.autoFocusTarget })
    })
  },
)

defineExpose({
  focusTree,
})
</script>

<template>
  <TreeRoot
    ref="treeRootRef"
    :items="props.items"
    :get-key="getKey"
    :get-children="getChildren"
    :model-value="props.modelValue"
    :expanded="props.expanded"
    :multiple="props.multiple"
    class="tree"
    :class="[actionsVisibilityClass, frameStyleClass, variantClass]"
    @update:model-value="emit('update:modelValue', $event as TreeNode | undefined)"
    @update:expanded="emit('update:expanded', $event)"
    @keydown.esc.stop.prevent="emit('escape')"
  >
    <TreeNode
      v-for="(item, index) in props.items"
      :key="getKey(item)"
      :node="item"
      :level="1"
      :position="index + 1"
      :total-siblings="props.items.length"
      @select="handleSelect"
      @toggle="emit('toggle', $event)"
    >
      <template #icon="slotProps">
        <slot
          name="icon"
          v-bind="slotProps"
        />
      </template>
      <template #label="slotProps">
        <slot
          name="label"
          v-bind="slotProps"
        >
          {{ slotProps.node.label }}
        </slot>
      </template>
      <template #actions="slotProps">
        <slot
          name="actions"
          v-bind="slotProps"
        />
      </template>
      <template #children="slotProps">
        <slot
          name="children"
          v-bind="slotProps"
        />
      </template>
    </TreeNode>
  </TreeRoot>
</template>

<style>
.tree {
  list-style: none;
  margin: 0;
  padding-left: 0;
  --tree-focus-outline: 2px solid #2a7ae2;
  --tree-focus-outline-offset: 2px;
  --tree-focus-bg: #fff2cc;
  --tree-hover-bg: #fff2cc;
  --tree-compact-hover-bg: #f5f5f5;
  --tree-compact-focus-bg: #f5f5f5;
  --tree-selected-label-bg: transparent;
  --tree-selected-label-weight: inherit;
}

.tree.tree-frame-framed {
  border: 1px solid #eee;
  padding: 5px;
}

.tree.tree-frame-well {
  min-height: 20px;
  padding: 9px;
  background-color: #f5f5f5;
  border: 1px solid #e3e3e3;
  border-radius: 3px;
  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.05);
}

.tree-actions-hover .tree-node-actions,
.tree-actions-focus .tree-node-actions,
.tree-actions-hover-focus .tree-node-actions {
  opacity: 0;
  transition: opacity 120ms ease;
}

.tree-actions-hover .tree-node-content:hover .tree-node-actions,
.tree-actions-hover-focus .tree-node-content:hover .tree-node-actions {
  opacity: 1;
}

.tree-actions-focus .tree-node:focus > .tree-node-content .tree-node-actions,
.tree-actions-hover-focus .tree-node:focus > .tree-node-content .tree-node-actions {
  opacity: 1;
}

.tree-node-content {
  display: flex;
  align-items: center;
  padding: 6px;
  background-color: transparent;
  cursor: pointer;
  user-select: none;
  gap: 6px;
}

.tree-node {
  background-color: #fff;
}

.tree-node:focus {
  outline: none;
}

.tree-node:focus > .tree-node-content {
  outline: var(--tree-focus-outline);
  outline-offset: var(--tree-focus-outline-offset);
  background-color: var(--tree-focus-bg);
}

.tree-node-content:hover {
  background-color: var(--tree-hover-bg);
}

.tree-node-icon {
  display: block;
  width: 28px;
  height: 16px;
  text-align: center;
  flex-shrink: 0;
}

.tree-node-icon .fa-folder,
.tree-node-icon .fa-folder-open {
  color: #f1c40f;
}

.tree-node-icon .fa-file {
  color: #95a5a6;
}

.tree-node-label {
  cursor: inherit;
  flex: 1;
}

.tree-node-content.tree-node-selected .tree-node-label,
.tree-node-content.tree-node-selected .tree-node-display {
  background-color: var(--tree-selected-label-bg);
  font-weight: var(--tree-selected-label-weight);
}

.tree-node-actions {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tree-children {
  list-style: none;
  margin: 0;
  padding-left: 10px;
}

.tree-variant-compact .tree-node {
  user-select: none;
  background-color: transparent;
}

.tree-variant-compact .tree-node-content {
  padding: 2px 4px;
  min-height: 20px;
  line-height: 1.4;
  cursor: default;
}

.tree-variant-compact .tree-node-content.tree-node-selectable {
  cursor: pointer;
}

.tree-variant-compact .tree-node-content.tree-node-expandable {
  cursor: pointer;
}

.tree-variant-compact .tree-node-content.tree-node-selectable:hover {
  background-color: var(--tree-compact-hover-bg);
}

.tree-variant-compact .tree-node:focus > .tree-node-content.tree-node-selectable {
  background-color: var(--tree-compact-focus-bg);
}

.tree-variant-compact .tree-node[data-disabled] > .tree-node-content {
  opacity: 0.8;
  cursor: not-allowed;
}

.tree-variant-compact .tree-node-content.tree-node-not-addable .tree-node-label,
.tree-variant-compact .tree-node-content.tree-node-not-addable .tree-node-display,
.tree-variant-compact .tree-node-content.tree-node-not-addable .tree-node-size {
  text-decoration: line-through;
  color: #767676;
}

.tree-variant-compact .tree-node[data-disabled] > .tree-node-content:hover {
  background-color: transparent;
}

.tree-variant-compact .tree-node-content.tree-node-not-addable-file {
  cursor: not-allowed;
}

.tree-variant-compact .tree-node-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 4px;
}

.tree-variant-compact .tree-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-variant-compact .tree-node-size,
.tree-variant-compact .tree-node-display {
  color: #595959;
  margin-left: 4px;
}

.tree-variant-compact .tree-node-children {
  margin-left: 20px;
}

.tree-variant-compact .tree-node-loading {
  padding: 2px 4px;
  color: #595959;
  font-style: italic;
  font-size: 12px;
}

.tree-variant-compact .tree-node-empty {
  padding: 2px 4px;
  color: #767676;
  font-style: italic;
  font-size: 12px;
}

@media (prefers-reduced-motion: reduce) {
  .tree-variant-compact .tree-node-content {
    transition: none;
  }
}
</style>

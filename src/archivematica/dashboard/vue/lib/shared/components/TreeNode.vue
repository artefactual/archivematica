<script setup lang="ts">
import { TreeItem, injectTreeRootContext } from 'reka-ui'
import { computed, nextTick, ref } from 'vue'
import type { TreeItemSelectEvent } from 'reka-ui'
import type { TreeNode, TreeNodeContext } from '@/shared/components/TreeView.vue'
import { useTreeNodeConfig } from '@/shared/components/treeNodeConfig'

defineOptions({ name: 'TreeNode' })

type TreeNodeProps = {
  node: TreeNode
  level: number
  getChildren?: (node: TreeNode) => TreeNode[] | undefined
  getNodeId?: (node: TreeNode) => string
  getAriaLabel?: (node: TreeNode, context: TreeNodeContext) => string
  getDisabled?: (node: TreeNode) => boolean
  getContentClass?: (node: TreeNode, context: TreeNodeContext) => string | string[] | Record<string, boolean>
  enterToggles?: boolean
  onEnter?: (node: TreeNode) => void
  rightToggles?: boolean
  actionsFocusable?: boolean
  position?: number
  totalSiblings?: number
}

const props = withDefaults(defineProps<TreeNodeProps>(), {
  getChildren: undefined,
  getNodeId: undefined,
  getAriaLabel: undefined,
  getDisabled: undefined,
  getContentClass: undefined,
  onEnter: undefined,
  position: undefined,
  totalSiblings: undefined,
})

const emit = defineEmits<{
  select: [node: TreeNode, originalEvent?: Event]
  toggle: [node: TreeNode]
}>()

type TreeNodeSlotProps = {
  node: TreeNode
  level: number
  hasChildren: boolean
  isExpanded: boolean
  isSelected: boolean
  isDisabled: boolean
  isFocused: boolean
  actionProps?: {
    tabindex?: number
  }
}

defineSlots<{
  icon?: (props: TreeNodeSlotProps) => unknown
  label?: (props: TreeNodeSlotProps) => unknown
  actions?: (props: TreeNodeSlotProps) => unknown
  children?: (props: TreeNodeSlotProps) => unknown
}>()

const injectedConfig = useTreeNodeConfig()
const resolvedGetChildren = computed(() => props.getChildren ?? injectedConfig?.value.getChildren)
const resolvedGetNodeId = computed(() => props.getNodeId ?? injectedConfig?.value.getNodeId)
const resolvedGetAriaLabel = computed(() => props.getAriaLabel ?? injectedConfig?.value.getAriaLabel)
const resolvedGetDisabled = computed(() => props.getDisabled ?? injectedConfig?.value.getDisabled)
const resolvedGetContentClass = computed(() => props.getContentClass ?? injectedConfig?.value.getContentClass)
const resolvedEnterToggles = computed(() => props.enterToggles ?? injectedConfig?.value.enterToggles ?? true)
const resolvedOnEnter = computed(() => props.onEnter ?? injectedConfig?.value.onEnter)
const resolvedRightToggles = computed(() => props.rightToggles ?? injectedConfig?.value.rightToggles ?? false)
const resolvedActionsFocusable = computed(() => props.actionsFocusable ?? injectedConfig?.value.actionsFocusable ?? true)

const children = computed(() => (resolvedGetChildren.value ? resolvedGetChildren.value(props.node) : props.node.children))
const hasChildren = computed(() => children.value !== undefined)
const nodeId = computed(() => (resolvedGetNodeId.value ? resolvedGetNodeId.value(props.node) : undefined))
const isDisabled = computed(() => (resolvedGetDisabled.value ? resolvedGetDisabled.value(props.node) : false))
const isFocused = ref(false)
const treeContext = injectTreeRootContext()
const actionProps = computed(() => (resolvedActionsFocusable.value ? {} : { tabindex: -1 }))

const getContext = (isExpanded: boolean, isSelected: boolean): TreeNodeContext => ({
  node: props.node,
  isExpanded,
  isSelected,
  isDisabled: isDisabled.value,
})

const resolveAriaLabel = (isExpanded: boolean, isSelected: boolean) => (
  resolvedGetAriaLabel.value ? resolvedGetAriaLabel.value(props.node, getContext(isExpanded, isSelected)) : undefined
)

const resolveContentClass = (isExpanded: boolean, isSelected: boolean) => (
  resolvedGetContentClass.value ? resolvedGetContentClass.value(props.node, getContext(isExpanded, isSelected)) : undefined
)

const handleSelect = (event: TreeItemSelectEvent<TreeNode>) => {
  if (isDisabled.value) {
    return
  }
  const originalEvent = event?.detail?.originalEvent
  emit('select', props.node, originalEvent)

  if (originalEvent instanceof KeyboardEvent && resolvedEnterToggles.value) {
    const key = originalEvent.key
    if ((key === 'Enter' || key === ' ') && children.value !== undefined) {
      emit('toggle', props.node)
    }
  }
}

const handleToggleEvent = () => {
  if (isDisabled.value || !children.value) {
    return
  }
  emit('toggle', props.node)
}

const handleRightKey = (event: KeyboardEvent) => {
  if (isDisabled.value || !children.value) {
    return
  }
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  emit('toggle', props.node)
  treeContext?.onToggle(props.node)
}

const focusParentNode = (currentEl: HTMLElement) => {
  const root = currentEl.closest('[role="tree"]') ?? currentEl.parentElement
  if (!root || props.level <= 1) {
    currentEl.focus()
    return
  }
  const items = Array.from(root.querySelectorAll<HTMLElement>('[role="treeitem"]'))
  const index = items.indexOf(currentEl)
  if (index <= 0) {
    currentEl.focus()
    return
  }
  const targetIndent = String(props.level - 1)
  for (let i = index - 1; i >= 0; i -= 1) {
    if (items[i]?.getAttribute('data-indent') === targetIndent) {
      items[i]?.focus()
      return
    }
  }
  currentEl.focus()
}

const isNodeExpanded = () => {
  if (!treeContext?.expanded?.value || !treeContext?.getKey) return false
  const key = treeContext.getKey(props.node)
  return treeContext.expanded.value.includes(key)
}

const handleLeftKey = (event: KeyboardEvent) => {
  const currentEl = event.currentTarget as HTMLElement | null
  if (!currentEl) return
  event.stopImmediatePropagation()
  if (isDisabled.value) {
    focusParentNode(currentEl)
    return
  }
  if (children.value && isNodeExpanded()) {
    emit('toggle', props.node)
    treeContext?.onToggle(props.node)
    nextTick(() => {
      currentEl.focus()
    })
    return
  }
  focusParentNode(currentEl)
}

const handleEnterKey = (event: KeyboardEvent) => {
  if (isDisabled.value) {
    return
  }
  emit('select', props.node, event)
  if (resolvedOnEnter.value) {
    resolvedOnEnter.value(props.node)
    return
  }
  if (resolvedEnterToggles.value && children.value !== undefined) {
    treeContext?.onToggle(props.node)
  }
}

const handleFocusIn = () => {
  isFocused.value = true
}

const handleFocusOut = (event: FocusEvent) => {
  const currentTarget = event.currentTarget as HTMLElement | null
  const relatedTarget = event.relatedTarget as HTMLElement | null
  if (currentTarget && relatedTarget && currentTarget.contains(relatedTarget)) {
    return
  }
  isFocused.value = false
}
</script>

<template>
  <TreeItem
    :id="nodeId"
    v-slot="{ isExpanded, isSelected }"
    :value="props.node"
    :level="props.level"
    class="tree-node"
    :data-disabled="isDisabled ? '' : undefined"
    :aria-disabled="isDisabled ? 'true' : undefined"
    :aria-setsize="props.totalSiblings"
    :aria-posinset="props.position"
    @select="handleSelect"
    @toggle="handleToggleEvent"
    @keydown.right="resolvedRightToggles ? handleRightKey($event) : undefined"
    @keydown.left.stop.prevent="handleLeftKey($event)"
    @keydown.enter.stop.prevent="handleEnterKey"
    @keydown.space.stop.prevent="handleEnterKey"
    @focusin="handleFocusIn"
    @focusout="handleFocusOut"
  >
    <div
      class="tree-node-content"
      :class="[
        { 'tree-node-file': !children },
        { 'tree-node-selected': isSelected },
        resolveContentClass(isExpanded, isSelected),
      ]"
      :aria-label="resolveAriaLabel(isExpanded, isSelected)"
    >
      <span
        class="tree-node-icon"
        aria-hidden="true"
      >
        <slot
          name="icon"
          :node="props.node"
          :level="props.level"
          :has-children="hasChildren"
          :is-expanded="isExpanded"
          :is-selected="isSelected"
          :is-focused="isFocused"
          :is-disabled="isDisabled"
        >
          <i
            v-if="children"
            class="fa"
            :class="isExpanded ? 'fa-folder-open' : 'fa-folder'"
          />
          <span
            v-else
            class="tree-node-icon-file"
          >
            <i class="fa fa-file tree-node-icon-default" />
          </span>
        </slot>
      </span>
      <span class="tree-node-label">
        <slot
          name="label"
          :node="props.node"
          :level="props.level"
          :has-children="hasChildren"
          :is-expanded="isExpanded"
          :is-selected="isSelected"
          :is-focused="isFocused"
          :is-disabled="isDisabled"
        >
          {{ props.node.label }}
        </slot>
      </span>
      <span class="tree-node-actions">
        <slot
          name="actions"
          :node="props.node"
          :level="props.level"
          :has-children="hasChildren"
          :is-expanded="isExpanded"
          :is-selected="isSelected"
          :is-focused="isFocused"
          :is-disabled="isDisabled"
          :action-props="actionProps"
        />
      </span>
    </div>
    <ul
      v-if="children && isExpanded"
      class="tree-children"
      role="group"
    >
      <slot
        name="children"
        :node="props.node"
        :level="props.level"
        :has-children="hasChildren"
        :is-expanded="isExpanded"
        :is-selected="isSelected"
        :is-focused="isFocused"
        :is-disabled="isDisabled"
      />
      <TreeNode
        v-for="(child, index) in children"
        :key="resolvedGetNodeId ? resolvedGetNodeId(child) : (child.id ?? child.path ?? String(index))"
        :node="child"
        :level="props.level + 1"
        :position="index + 1"
        :total-siblings="children.length"
        @select="(node, originalEvent) => emit('select', node, originalEvent)"
        @toggle="emit('toggle', $event)"
      >
        <template #icon="slotContext">
          <slot
            name="icon"
            v-bind="slotContext"
          />
        </template>
        <template #label="slotContext">
          <slot
            name="label"
            v-bind="slotContext"
          >
            {{ slotContext.node.label ?? '' }}
          </slot>
        </template>
        <template #actions="slotContext">
          <slot
            name="actions"
            v-bind="slotContext"
          />
        </template>
      </TreeNode>
    </ul>
  </TreeItem>
</template>

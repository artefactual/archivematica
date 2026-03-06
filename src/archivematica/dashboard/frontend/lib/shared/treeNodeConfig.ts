import { inject, provide, type ComputedRef, type InjectionKey } from 'vue'
import type { TreeNode, TreeNodeContext } from '@/shared/components/TreeView.vue'

// Internal TreeView -> TreeNode configuration channel.
//
// Why:
// - Recursive TreeNode rendering previously forwarded many behavior props
//    (`getChildren`, `getDisabled`, keyboard flags, etc.) through every level.
// - That prop drilling is easy to break when adding/updating behavior.
//
// Purpose:
// - Provide one shared behavior/config object at TreeView root.
// - Let each TreeNode (root + descendants) consume the same config via inject.
//
// Scope:
// - Internal shared-tree plumbing only. This is not a public app API.
export type TreeNodeConfig = {
  getChildren?: (node: TreeNode) => TreeNode[] | undefined
  getNodeId?: (node: TreeNode) => string
  getAriaLabel?: (node: TreeNode, context: TreeNodeContext) => string
  getDisabled?: (node: TreeNode) => boolean
  getContentClass?: (node: TreeNode, context: TreeNodeContext) => string | string[] | Record<string, boolean>
  enterToggles: boolean
  onEnter?: (node: TreeNode) => void
  rightToggles: boolean
  actionsFocusable: boolean
}

const TREE_NODE_CONFIG_KEY: InjectionKey<ComputedRef<TreeNodeConfig>> = Symbol('TreeNodeConfig')

export const provideTreeNodeConfig = (config: ComputedRef<TreeNodeConfig>) => {
  provide(TREE_NODE_CONFIG_KEY, config)
}

export const useTreeNodeConfig = () => inject(TREE_NODE_CONFIG_KEY, undefined)

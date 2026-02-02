// Shared key/id helpers for TreeView/TreeNode internals.
//
// Why this module exists:
// - Tree rendering needs stable per-node keys even when callers do not provide
//    `id`/`path` or return empty strings from `getKey`.
// - DOM ids used for aria wiring and scroll targeting must remain unique and
//    deterministic for a mounted tree instance.
// - Keeping this logic outside `TreeView.vue` reduces component size and makes
//    edge-case behavior directly unit-testable.
//
// Scope:
// - This is intentionally tree-component-scoped infrastructure, not a generic
//    app-wide utility.
type TreeNodeLike = {
  id?: string
  path?: string
}

type TreeNodeRecord = TreeNodeLike | Record<string, unknown>

export type TreeNodeKeyOptions<TNode extends TreeNodeLike = TreeNodeLike> = {
  resolveGetKey?: () => ((node: TNode) => string) | undefined
  resolveGetNodeId?: () => ((node: TNode) => string) | undefined
}

export const sanitizeNodeId = (value: string) => value
  .replace(/[^A-Za-z0-9_-]/g, '-')
  .replace(/-+/g, '-')
  .replace(/^-|-$/g, '')

export const fallbackHash = (value: string) => {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash).toString(16)
}

export const createTreeNodeKeyHelpers = <TNode extends TreeNodeLike = TreeNodeLike>(
  options: TreeNodeKeyOptions<TNode> = {},
) => {
  const resolveGetKey = options.resolveGetKey ?? (() => undefined)
  const resolveGetNodeId = options.resolveGetNodeId ?? (() => undefined)

  let anonymousNodeCounter = 0
  const anonymousNodeKeys = new WeakMap<object, string>()

  const getAnonymousNodeKey = (node: TreeNodeRecord) => {
    if (typeof node !== 'object' || node === null) {
      anonymousNodeCounter += 1
      return `anon-${anonymousNodeCounter}`
    }
    const existing = anonymousNodeKeys.get(node)
    if (existing) {
      return existing
    }
    anonymousNodeCounter += 1
    const generated = `anon-${anonymousNodeCounter}`
    anonymousNodeKeys.set(node, generated)
    return generated
  }

  const getKey = (node: TNode | Record<string, unknown>) => {
    const customGetKey = resolveGetKey()
    if (customGetKey) {
      return customGetKey(node as TNode) || getAnonymousNodeKey(node)
    }
    const treeNode = node as TNode | undefined
    return treeNode?.id ?? treeNode?.path ?? getAnonymousNodeKey(node)
  }

  const getNodeId = (node: TNode) => {
    const customGetNodeId = resolveGetNodeId()
    if (customGetNodeId) {
      return customGetNodeId(node)
    }
    const key = getKey(node)
    const sanitized = sanitizeNodeId(key)
    return sanitized ? `tree-node-${sanitized}` : `tree-node-${fallbackHash(key)}`
  }

  return {
    getKey,
    getNodeId,
  }
}

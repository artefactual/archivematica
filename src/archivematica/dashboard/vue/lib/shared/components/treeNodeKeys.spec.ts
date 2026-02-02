import { describe, it, expect } from 'vitest'
import { createTreeNodeKeyHelpers, fallbackHash, sanitizeNodeId } from './treeNodeKeys'

describe('treeNodeKeys', () => {
  it('sanitizes DOM id fragments', () => {
    expect(sanitizeNodeId('a/b c')).toBe('a-b-c')
    expect(sanitizeNodeId('--x__y--')).toBe('x__y')
  })

  it('returns stable fallback hash for same input', () => {
    expect(fallbackHash('abc')).toBe(fallbackHash('abc'))
    expect(fallbackHash('abc')).not.toBe(fallbackHash('def'))
  })

  it('uses id, then path, then anonymous key fallback', () => {
    const { getKey } = createTreeNodeKeyHelpers()
    expect(getKey({ id: 'n1', path: '/a' })).toBe('n1')
    expect(getKey({ path: '/a' })).toBe('/a')

    const nodeA = { label: 'A' }
    const nodeB = { label: 'B' }
    const keyA = getKey(nodeA)
    const keyB = getKey(nodeB)
    expect(keyA).not.toBe(keyB)
    expect(getKey(nodeA)).toBe(keyA)
  })

  it('falls back to anonymous key when custom getKey returns empty', () => {
    const { getKey } = createTreeNodeKeyHelpers({
      resolveGetKey: () => () => '',
    })

    const nodeA = { label: 'A' }
    const nodeB = { label: 'B' }
    const keyA = getKey(nodeA)
    const keyB = getKey(nodeB)
    expect(keyA).not.toBe('')
    expect(keyB).not.toBe('')
    expect(keyA).not.toBe(keyB)
  })

  it('creates unique node ids for nodes without id/path', () => {
    const { getNodeId } = createTreeNodeKeyHelpers()
    const idA = getNodeId({ label: 'A' } as { id?: string, path?: string })
    const idB = getNodeId({ label: 'B' } as { id?: string, path?: string })
    expect(idA).not.toBe(idB)
    expect(idA.startsWith('tree-node-')).toBe(true)
    expect(idB.startsWith('tree-node-')).toBe(true)
  })

  it('uses custom getNodeId when provided', () => {
    const { getNodeId } = createTreeNodeKeyHelpers({
      resolveGetNodeId: () => node => `custom-${node.id ?? 'x'}`,
    })
    expect(getNodeId({ id: 'abc' })).toBe('custom-abc')
  })
})

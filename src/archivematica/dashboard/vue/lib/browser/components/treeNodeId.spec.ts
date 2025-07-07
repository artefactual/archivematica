import { describe, it, expect } from 'vitest'
import { createTreeNodeId } from '@/browser/components/treeNodeId'

describe('createTreeNodeId', () => {
  it('normalizes basic paths', () => {
    expect(createTreeNodeId('folder/sub')).toBe('node-folder-sub')
  })

  it('handles paths with literal percent characters', () => {
    expect(() => createTreeNodeId('folder/100% ready')).not.toThrow()
    expect(createTreeNodeId('folder/100% ready')).toMatch(/^node-/)
  })

  it('falls back to a hash when sanitizing empties the name', () => {
    const result = createTreeNodeId('%%%')
    expect(result).toMatch(/^node-/)
    expect(result).not.toBe('node-')
  })
})

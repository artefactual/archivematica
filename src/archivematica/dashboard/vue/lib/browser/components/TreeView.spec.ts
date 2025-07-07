import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import TreeView from '@/browser/components/TreeView.vue'
import TreeViewNode from '@/browser/components/TreeViewNode.vue'
import type { FileNode } from '@/shared/models'

const i18n = createI18nMock()

describe('TreeView', () => {
  const mockNodes: FileNode[] = [
    {
      name: 'folder1',
      path: '/folder1',
      type: 'directory',
      children: [],
      children_fetched: false,
    },
    {
      name: 'file1.txt',
      path: '/file1.txt',
      type: 'file',
      size: 1024,
      children_fetched: false,
    },
  ]

  const defaultProps = {
    nodes: mockNodes,
    selectedPath: '',
    transferType: 'standard',
    expandedPaths: [],
  }

  it('renders tree nodes for each provided node', () => {
    const wrapper = mount(TreeView, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const treeNodes = wrapper.findAllComponents(TreeViewNode)
    expect(treeNodes).toHaveLength(2)

    const firstNode = treeNodes[0]
    const secondNode = treeNodes[1]
    if (!firstNode || !secondNode) {
      throw new Error('Expected two tree view nodes')
    }

    // Check that each node receives correct props
    expect(firstNode.props()).toEqual({
      node: mockNodes[0],
      selectedPath: '',
      transferType: 'standard',
      expandedPaths: [],
      nodeIndex: 0,
      totalNodes: 2,
      level: 1,
    })

    expect(secondNode.props()).toEqual({
      node: mockNodes[1],
      selectedPath: '',
      transferType: 'standard',
      expandedPaths: [],
      nodeIndex: 1,
      totalNodes: 2,
      level: 1,
    })
  })

  it('passes expanded paths to tree nodes', () => {
    const expandedPaths = ['/folder1']
    const wrapper = mount(TreeView, {
      props: {
        ...defaultProps,
        expandedPaths,
      },
      global: {
        plugins: [i18n],
      },
    })

    const treeNodes = wrapper.findAllComponents(TreeViewNode)
    const firstNode = treeNodes[0]
    if (!firstNode) {
      throw new Error('Expected at least one tree view node')
    }
    expect(firstNode.props().expandedPaths).toEqual(expandedPaths)
  })

  it('passes selected path to tree nodes', () => {
    const selectedPath = '/folder1'
    const wrapper = mount(TreeView, {
      props: {
        ...defaultProps,
        selectedPath,
      },
      global: {
        plugins: [i18n],
      },
    })

    const treeNodes = wrapper.findAllComponents(TreeViewNode)
    const firstNode = treeNodes[0]
    if (!firstNode) {
      throw new Error('Expected at least one tree view node')
    }
    expect(firstNode.props().selectedPath).toBe(selectedPath)
  })

  it('emits select event when tree node emits select', async () => {
    const wrapper = mount(TreeView, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const treeNode = wrapper.findComponent(TreeViewNode)
    await treeNode.vm.$emit('select', '/folder1')

    expect(wrapper.emitted('select')).toEqual([
      [{ path: '/folder1', canAdd: true }],
    ])
  })

  it('emits expand event when tree node emits expand', async () => {
    const wrapper = mount(TreeView, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const testNode = mockNodes[0]
    const treeNode = wrapper.findComponent(TreeViewNode)
    await treeNode.vm.$emit('expand', testNode)

    expect(wrapper.emitted('expand')).toEqual([[testNode]])
  })

  it('emits toggle event when tree node emits toggle', async () => {
    const wrapper = mount(TreeView, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const treeNode = wrapper.findComponent(TreeViewNode)
    await treeNode.vm.$emit('toggle', '/folder1')

    expect(wrapper.emitted('toggle')).toEqual([['/folder1']])
  })

  it('renders empty when no nodes provided', () => {
    const wrapper = mount(TreeView, {
      props: {
        ...defaultProps,
        nodes: [],
      },
      global: {
        plugins: [i18n],
      },
    })

    const treeNodes = wrapper.findAllComponents(TreeViewNode)
    expect(treeNodes).toHaveLength(0)
  })

  it('applies correct CSS classes', () => {
    const wrapper = mount(TreeView, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const container = wrapper.find('.file-tree-view')
    expect(container.exists()).toBe(true)
    expect(container.element.tagName).toBe('DIV')
  })

  it('uses proper key for each tree node', () => {
    const wrapper = mount(TreeView, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const treeNodes = wrapper.findAllComponents(TreeViewNode)
    // Vue Test Utils doesn't directly expose keys, but we can check that nodes are properly rendered
    const firstNode = treeNodes[0]
    const secondNode = treeNodes[1]
    if (!firstNode || !secondNode) {
      throw new Error('Expected two tree view nodes')
    }
    expect(firstNode.props().node.path).toBe('/folder1')
    expect(secondNode.props().node.path).toBe('/file1.txt')
  })

  describe('WCAG Compliance', () => {
    it('should have proper tree role and attributes', () => {
      const wrapper = mount(TreeView, {
        props: defaultProps,
        global: {
          plugins: [i18n],
        },
      })

      const treeView = wrapper.find('.file-tree-view')
      expect(treeView.attributes('role')).toBe('tree')
      expect(treeView.attributes('aria-label')).toBe('File browser for standard transfer')
      expect(treeView.attributes('tabindex')).toBe('0')
    })

    it('should show screen reader instructions', () => {
      const wrapper = mount(TreeView, {
        props: defaultProps,
        global: {
          plugins: [i18n],
        },
      })

      const instructions = wrapper.find('.sr-only[role="status"]')
      expect(instructions.exists()).toBe(true)
      expect(instructions.attributes('aria-live')).toBe('polite')
      expect(instructions.text()).toContain('Use arrow keys to navigate')
    })

    it('should show empty state when no nodes', () => {
      const wrapper = mount(TreeView, {
        props: {
          ...defaultProps,
          nodes: [],
        },
        global: {
          plugins: [i18n],
        },
      })

      const emptyState = wrapper.find('.tree-empty')
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.attributes('role')).toBe('status')
      expect(emptyState.text()).toBe('No files or folders to display')
    })

    it('should render tree nodes with proper ARIA level', () => {
      const wrapper = mount(TreeView, {
        props: defaultProps,
        global: {
          plugins: [i18n],
        },
      })

      const treeNodes = wrapper.findAll('[role="treeitem"]')
      const firstNode = treeNodes[0]
      const secondNode = treeNodes[1]
      if (!firstNode || !secondNode) {
        throw new Error('Expected two tree items')
      }
      expect(firstNode.attributes('aria-level')).toBe('1')
      expect(secondNode.attributes('aria-level')).toBe('1')
    })

    it('should render tree nodes with proper structure', () => {
      const wrapper = mount(TreeView, {
        props: defaultProps,
        global: {
          plugins: [i18n],
        },
      })

      const treeNodes = wrapper.findAll('[role="treeitem"]')
      expect(treeNodes).toHaveLength(2)
      const firstNode = treeNodes[0]
      const secondNode = treeNodes[1]
      if (!firstNode || !secondNode) {
        throw new Error('Expected two tree items')
      }
      expect(firstNode.attributes('aria-selected')).toBe('false')
      expect(secondNode.attributes('aria-selected')).toBe('false')
    })

    it('should handle keyboard navigation events', async () => {
      const wrapper = mount(TreeView, {
        props: defaultProps,
        global: {
          plugins: [i18n],
        },
      })

      const treeView = wrapper.find('.file-tree-view')

      // Test arrow down
      await treeView.trigger('keydown', { key: 'ArrowDown' })
      expect(wrapper.emitted('select')).toBeTruthy()

      // Test enter key
      await treeView.trigger('keydown', { key: 'Enter' })
      expect(wrapper.emitted('select')).toBeTruthy()

      // Test space key
      await treeView.trigger('keydown', { key: ' ' })
      expect(wrapper.emitted('select')).toBeTruthy()
    })
  })
})

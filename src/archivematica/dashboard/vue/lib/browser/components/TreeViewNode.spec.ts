import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import TreeViewNode from '@/browser/components/TreeViewNode.vue'
import type { FileNode } from '@/shared/models'

const i18n = createI18nMock()

describe('TreeViewNode', () => {
  const createFileNode = (overrides: Partial<FileNode> = {}): FileNode => ({
    name: 'test-file',
    path: '/test/path',
    type: 'file',
    children_fetched: false,
    ...overrides,
  })

  const createDirectoryNode = (overrides: Partial<FileNode> = {}): FileNode => ({
    name: 'test-folder',
    path: '/test/folder',
    type: 'directory',
    children: [],
    children_fetched: false,
    ...overrides,
  })

  const defaultProps = {
    selectedPath: '',
    transferType: 'standard',
    expandedPaths: [],
  }

  describe('File Nodes', () => {
    it('renders file icon for file nodes', () => {
      const fileNode = createFileNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.find('.tree-icon-file').exists()).toBe(true)
      expect(wrapper.text()).toContain('test-file')
    })

    it('displays file size when available', () => {
      const fileNode = createFileNode({ size: 1024 })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('(1 KB)')
    })

    it('does not display size for directories', () => {
      const dirNode = createDirectoryNode({ size: 1024 })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).not.toContain('(1 KB)')
    })

    it('emits select event when file is clicked even if not addable', async () => {
      const fileNode = createFileNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      // For 'standard' transfer type, files should not be selectable (only directories)
      const content = wrapper.find('.tree-node-content')
      expect(content.classes()).toContain('disabled')

      await content.trigger('click')

      expect(wrapper.emitted('select')).toEqual([['/test/path']])
    })
  })

  describe('Directory Nodes', () => {
    it('renders closed folder icon for collapsed directories', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.find('.tree-icon-collapsed').exists()).toBe(true)
      expect(wrapper.text()).toContain('test-folder')
    })

    it('renders open folder icon for expanded directories', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          expandedPaths: ['/test/folder'],
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.find('.tree-icon-expanded').exists()).toBe(true)
    })

    it('emits toggle event when folder icon is clicked', async () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const toggle = wrapper.find('.tree-node-toggle')
      await toggle.trigger('click')

      expect(wrapper.emitted('toggle')).toEqual([['/test/folder']])
    })

    it('emits expand event when expanding unfetched directory', async () => {
      const dirNode = createDirectoryNode({ children_fetched: false })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const toggle = wrapper.find('.tree-node-toggle')
      await toggle.trigger('click')

      expect(wrapper.emitted('expand')).toEqual([[dirNode]])
    })

    it('does not emit expand event when expanding already fetched directory', async () => {
      const dirNode = createDirectoryNode({
        children_fetched: true,
        children: [createFileNode({ name: 'child.txt', path: '/test/folder/child.txt' })],
      })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const toggle = wrapper.find('.tree-node-toggle')
      await toggle.trigger('click')

      expect(wrapper.emitted('expand')).toBeUndefined()
      expect(wrapper.emitted('toggle')).toEqual([['/test/folder']])
    })

    it('shows loading state when node is loading', () => {
      const dirNode = createDirectoryNode({ loading: true })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          expandedPaths: ['/test/folder'],
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('Loading...')
      // Note: Loading spinners were removed per user request - only text indicator remains
      expect(wrapper.find('.tree-node-loading').exists()).toBe(true)
    })

    it('shows empty directory message when fetched but no children', () => {
      const dirNode = createDirectoryNode({
        children_fetched: true,
        children: [],
      })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          expandedPaths: ['/test/folder'],
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('No files or folders to display')
    })

    it('renders child nodes when expanded and has children', () => {
      const childNode = createFileNode({ name: 'child.txt', path: '/test/folder/child.txt' })
      const dirNode = createDirectoryNode({
        children_fetched: true,
        children: [childNode],
      })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          expandedPaths: ['/test/folder'],
        },
        global: {
          plugins: [i18n],
        },
      })

      // Should render a child TreeViewNode
      const childNodes = wrapper.findAllComponents(TreeViewNode)
      expect(childNodes).toHaveLength(1) // The child node (parent is rendered as this component)
    })
  })

  describe('Selection and Transfer Types', () => {
    it('allows directory selection for standard transfer type', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          transferType: 'standard',
        },
        global: {
          plugins: [i18n],
        },
      })

      const content = wrapper.find('.tree-node-content')
      expect(content.classes()).toContain('selectable')
      expect(content.classes()).not.toContain('disabled')
    })

    it('disables file selection for standard transfer type', () => {
      const fileNode = createFileNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
          transferType: 'standard',
        },
        global: {
          plugins: [i18n],
        },
      })

      const content = wrapper.find('.tree-node-content')
      expect(content.classes()).toContain('disabled')
      expect(content.classes()).not.toContain('selectable')
    })

    it('allows compressed file selection for zipfile transfer type', () => {
      const zipFile = createFileNode({ name: 'archive.zip' })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: zipFile,
          transferType: 'zipfile',
        },
        global: {
          plugins: [i18n],
        },
      })

      const content = wrapper.find('.tree-node-content')
      expect(content.classes()).toContain('selectable')
      expect(content.classes()).not.toContain('disabled')
    })

    it('emits select event when selectable node is clicked', async () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          transferType: 'standard',
        },
        global: {
          plugins: [i18n],
        },
      })

      const content = wrapper.find('.tree-node-content')
      await content.trigger('click')

      expect(wrapper.emitted('select')).toEqual([['/test/folder']])
    })

    it('highlights selected node', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          selectedPath: '/test/folder',
        },
        global: {
          plugins: [i18n],
        },
      })

      const content = wrapper.find('.tree-node-content')
      expect(content.classes()).toContain('selected')
    })
  })

  describe('File Size Formatting', () => {
    it('formats bytes correctly', () => {
      const fileNode = createFileNode({ size: 500 })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('(500 bytes)')
    })

    it('formats kilobytes correctly', () => {
      const fileNode = createFileNode({ size: 2048 })
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('(2 KB)')
    })

    it('formats megabytes correctly', () => {
      const fileNode = createFileNode({ size: 2097152 }) // 2 MB
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('(2 MB)')
    })

    it('formats gigabytes correctly', () => {
      const fileNode = createFileNode({ size: 3221225472 }) // 3 GB
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      expect(wrapper.text()).toContain('(3 GB)')
    })
  })

  describe('Event Propagation', () => {
    it('stops propagation when toggle is clicked', async () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const toggle = wrapper.find('.tree-node-toggle')
      await toggle.trigger('click')

      // The actual event stopping is handled by Vue's .stop modifier
      // We can verify that clicking toggle doesn't trigger content click
      expect(wrapper.emitted('select')).toBeUndefined()
    })
  })

  describe('WCAG Compliance', () => {
    it('should have proper treeitem role and ARIA attributes', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          level: 2,
        },
        global: {
          plugins: [i18n],
        },
      })

      const treeNode = wrapper.find('.tree-node')
      expect(treeNode.attributes('role')).toBe('treeitem')
      // The level should be 2 as explicitly provided
      expect(treeNode.attributes('aria-level')).toBe('2')
      expect(treeNode.attributes('aria-selected')).toBe('false')
      expect(treeNode.attributes('aria-expanded')).toBe('false')
      expect(treeNode.attributes('aria-disabled')).toBe('false')
      expect(treeNode.attributes('id')).toMatch(/^node-/)
      expect(treeNode.attributes('tabindex')).toBeUndefined()
    })

    it('should sanitize special characters in node ids', () => {
      const specialNode = {
        ...createDirectoryNode(),
        path: '/Weird Folder/child#(draft)',
      }

      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: specialNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const treeNode = wrapper.find('.tree-node')
      expect(treeNode.attributes('id')).toBe('node-Weird-Folder-child-draft')
    })

    it('should have proper ARIA attributes for selected node', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
          selectedPath: '/test/folder',
        },
        global: {
          plugins: [i18n],
        },
      })

      const treeNode = wrapper.find('.tree-node')
      expect(treeNode.attributes('aria-selected')).toBe('true')
      expect(treeNode.attributes('tabindex')).toBeUndefined()
    })

    it('should have accessible labels for toggle buttons', () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const toggle = wrapper.find('.tree-node-toggle')
      expect(toggle.attributes('role')).toBe('button')
      expect(toggle.attributes('aria-label')).toBe('Expand folder')
      expect(toggle.attributes('tabindex')).toBe('-1')
    })

    it('should have screen reader status information', () => {
      const fileNode = createFileNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: fileNode,
          transferType: 'standard', // Files not selectable for standard
        },
        global: {
          plugins: [i18n],
        },
      })

      const statusInfo = wrapper.find('.sr-only')
      expect(statusInfo.exists()).toBe(true)
      expect(statusInfo.text()).toContain('not selectable for standard transfer')
    })

    it('should handle click events for selection', async () => {
      const dirNode = createDirectoryNode()
      const wrapper = mount(TreeViewNode, {
        props: {
          ...defaultProps,
          node: dirNode,
        },
        global: {
          plugins: [i18n],
        },
      })

      const treeNodeContent = wrapper.find('.tree-node-content')

      // Test click on selectable node
      await treeNodeContent.trigger('click')
      expect(wrapper.emitted('select')).toBeTruthy()
      expect(wrapper.emitted('select')?.[0]).toEqual(['/test/folder'])
    })
  })
})

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import TreeViewContainer from '@/browser/components/TreeViewContainer.vue'
import TreeView from '@/shared/components/TreeView.vue'
import type { FileNode } from '@/browser/types'
import type { SourceLocation } from '@/shared/http/transfer'

const i18n = createI18nMock()

describe('TreeViewContainer', () => {
  const mockEnabledLocations: SourceLocation[] = [
    {
      uuid: 'loc1',
      description: 'Location 1',
      enabled: true,
      path: '/path1',
      purpose: 'TS',
      relative_path: '/path1',
      space: 'space1',
      used: 0,
      quota: null,
    },
    {
      uuid: 'loc2',
      description: 'Location 2',
      enabled: true,
      path: '/path2',
      purpose: 'TS',
      relative_path: '/path2',
      space: 'space2',
      used: 0,
      quota: null,
    },
  ]

  // Global config for mounting components with i18n
  const global = {
    mocks: {
      $t: (key: string, params?: Record<string, string>) => {
        const translations: Record<string, string> = {
          'fileBrowser.browser': 'File browser',
          'fileBrowser.addToTransfer': `Add ${params?.path || ''} to transfer`,
          'fileBrowser.selectFileOrFolder': 'Select a file or folder to add',
        }
        return translations[key] || key
      },
    },
  }

  const mockFileNodes: FileNode[] = [
    {
      name: 'folder1',
      path: '/folder1',
      type: 'directory',
      size: 0,
      children: [],
      children_fetched: false,
    },
    {
      name: 'file1.txt',
      path: '/file1.txt',
      type: 'file',
      size: 1024,
      children: [],
      children_fetched: false,
    },
  ]

  const defaultProps = {
    currentLocation: '',
    enabledLocations: mockEnabledLocations,
    loading: false,
    apiError: null,
    fileNodes: [],
    transferType: 'standard',
    expandedPaths: [],
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders location selector with enabled locations', () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: defaultProps,
    })

    const select = wrapper.find('select')
    expect(select.exists()).toBe(true)

    const options = select.findAll('option')
    expect(options).toHaveLength(2) // 2 locations (no placeholder)
    const firstOption = options[0]
    const secondOption = options[1]
    if (!firstOption || !secondOption) {
      throw new Error('Expected two location options')
    }
    expect(firstOption.text()).toBe('Location 1')
    expect(secondOption.text()).toBe('Location 2')
  })

  it('emits update:currentLocation when location is selected', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: defaultProps,
    })

    const select = wrapper.find('select')
    await select.setValue('loc1')

    const updateEvents = wrapper.emitted('update:currentLocation') ?? []
    const firstUpdate = updateEvents[0]
    if (!firstUpdate) {
      throw new Error('Expected update:currentLocation event payload')
    }
    expect(firstUpdate).toEqual(['loc1'])
  })

  it('accepts loading prop without displaying loading indicators', () => {
    // Note: Loading spinners were removed per user request
    // The loading prop is still accepted for API compatibility but not displayed
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        loading: true,
      },
    })

    // Component should render normally without loading indicators
    expect(wrapper.find('.fa-spinner').exists()).toBe(false)
    expect(wrapper.find('.transfer-tree-container').exists()).toBe(true)
  })

  it('shows error message when apiError is provided', () => {
    const errorMessage = 'Failed to load files'
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        apiError: errorMessage,
      },
    })

    const alert = wrapper.find('.alert-danger')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toBe(errorMessage)
  })

  it('renders TreeView when location is selected and data is loaded', () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    expect(treeView.exists()).toBe(true)
    expect(treeView.props('items')).toEqual(mockFileNodes)
    expect(treeView.props('expanded')).toEqual([])
    expect(treeView.props('variant')).toBe('compact')
    expect(treeView.props('frameStyle')).toBe('well')
    expect(treeView.props('autoFocusOnMount')).toBe(true)
    expect(treeView.props('autoFocusTarget')).toBe('selected')
  })

  it('emits expand event when tree node is expanded', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    const firstFileNode = mockFileNodes[0]
    if (!firstFileNode) {
      throw new Error('Expected at least one file node')
    }
    treeView.vm.$emit('toggle', firstFileNode)

    const expandEvents = wrapper.emitted('expand') ?? []
    const firstExpand = expandEvents[0]
    if (!firstExpand) {
      throw new Error('Expected expand event payload')
    }
    expect(firstExpand).toEqual([firstFileNode])
    expect(wrapper.emitted('toggle')).toEqual([[firstFileNode.path]])
  })

  it('renders external Add button and keeps it disabled without selection', () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    const externalAddButton = wrapper.find('button.transfer-tree-add-btn')
    expect(externalAddButton.exists()).toBe(true)
    expect(externalAddButton.attributes('disabled')).toBeDefined()
  })

  it('emits add event when external Add button is clicked with a selectable node', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    const firstNode = mockFileNodes[0]
    if (!firstNode) {
      throw new Error('Expected at least one file node')
    }
    treeView.vm.$emit('update:modelValue', firstNode)
    await wrapper.vm.$nextTick()

    const externalAddButton = wrapper.find('button.transfer-tree-add-btn')
    expect(externalAddButton.attributes('disabled')).toBeUndefined()
    await externalAddButton.trigger('click')

    const addEvents = wrapper.emitted('add') ?? []
    const firstAdd = addEvents[0]
    if (!firstAdd) {
      throw new Error('Expected add event payload')
    }
    expect(firstAdd[0]).toEqual(firstNode)
  })

  it('does not render per-row Add action buttons', () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    expect(wrapper.find('.transfer-tree-action').exists()).toBe(false)
  })

  it('renders 0-byte size text for file nodes', () => {
    const zeroByteFile: FileNode = {
      name: 'empty.txt',
      path: '/empty.txt',
      type: 'file',
      size: 0,
    }

    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: [zeroByteFile],
      },
    })

    expect(wrapper.text()).toContain('(0 bytes)')
  })

  it('includes 0-byte size in aria labels for file nodes', () => {
    const zeroByteFile: FileNode = {
      name: 'empty.txt',
      path: '/empty.txt',
      type: 'file',
      size: 0,
    }

    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: [zeroByteFile],
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    const getAriaLabel = treeView.props('getAriaLabel') as ((node: FileNode, context: {
      node: FileNode
      isExpanded: boolean
      isSelected: boolean
      isDisabled: boolean
    }) => string) | undefined
    if (!getAriaLabel) {
      throw new Error('Expected getAriaLabel handler')
    }

    const label = getAriaLabel(zeroByteFile, {
      node: zeroByteFile,
      isExpanded: false,
      isSelected: false,
      isDisabled: false,
    })
    expect(label).toContain('0 bytes')
  })

  it('localizes directory aria label item count for one child', () => {
    const directoryNode: FileNode = {
      name: 'folder',
      path: '/folder',
      type: 'directory',
      children_fetched: true,
      children: [
        {
          name: 'child.txt',
          path: '/folder/child.txt',
          type: 'file',
        },
      ],
    }

    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: [directoryNode],
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    const getAriaLabel = treeView.props('getAriaLabel') as ((node: FileNode, context: {
      node: FileNode
      isExpanded: boolean
      isSelected: boolean
      isDisabled: boolean
    }) => string) | undefined
    if (!getAriaLabel) {
      throw new Error('Expected getAriaLabel handler')
    }

    const label = getAriaLabel(directoryNode, {
      node: directoryNode,
      isExpanded: true,
      isSelected: false,
      isDisabled: false,
    })
    expect(label).toContain('containing 1 item')
  })

  it('localizes directory aria label item count for multiple children', () => {
    const directoryNode: FileNode = {
      name: 'folder',
      path: '/folder',
      type: 'directory',
      children_fetched: true,
      children: [
        {
          name: 'child-1.txt',
          path: '/folder/child-1.txt',
          type: 'file',
        },
        {
          name: 'child-2.txt',
          path: '/folder/child-2.txt',
          type: 'file',
        },
      ],
    }

    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: [directoryNode],
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    const getAriaLabel = treeView.props('getAriaLabel') as ((node: FileNode, context: {
      node: FileNode
      isExpanded: boolean
      isSelected: boolean
      isDisabled: boolean
    }) => string) | undefined
    if (!getAriaLabel) {
      throw new Error('Expected getAriaLabel handler')
    }

    const label = getAriaLabel(directoryNode, {
      node: directoryNode,
      isExpanded: true,
      isSelected: false,
      isDisabled: false,
    })
    expect(label).toContain('containing 2 items')
  })

  it('emits add event on Enter key select', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    const firstNode = mockFileNodes[0]
    if (!firstNode) {
      throw new Error('Expected at least one file node')
    }

    const onEnter = treeView.props('onEnter') as ((node: FileNode) => void) | undefined
    if (!onEnter) {
      throw new Error('Expected onEnter handler')
    }
    onEnter(firstNode)

    const addEvents = wrapper.emitted('add') ?? []
    const firstAdd = addEvents[0]
    if (!firstAdd) {
      throw new Error('Expected add event payload')
    }
    expect(firstAdd[0]).toEqual(firstNode)
  })

  it('emits escape when TreeView emits escape', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
      },
    })

    const treeView = wrapper.findComponent(TreeView)
    treeView.vm.$emit('escape')
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('escape')).toHaveLength(1)
  })

  describe('compressed file rules', () => {
    const triggerEnter = (transferType: string, node: FileNode) => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          transferType,
          fileNodes: [node],
        },
      })

      const treeView = wrapper.findComponent(TreeView)
      const onEnter = treeView.props('onEnter') as ((node: FileNode) => void) | undefined
      if (!onEnter) {
        throw new Error('Expected onEnter handler')
      }
      onEnter(node)
      return wrapper
    }

    it.each(['zipfile', 'zipped bag'])(
      'allows supported compressed extensions for %s transfer type',
      (transferType) => {
        for (const ext of ['zip', 'tgz', 'tar.gz']) {
          const node: FileNode = {
            name: `archive.${ext}`,
            path: `/archive.${ext}`,
            type: 'file',
          }

          const wrapper = triggerEnter(transferType, node)

          const addEvents = wrapper.emitted('add') ?? []
          const firstAdd = addEvents[0]
          if (!firstAdd) {
            throw new Error('Expected add event payload')
          }
          expect(firstAdd[0]).toEqual(node)
        }
      },
    )

    it.each(['zipfile', 'zipped bag'])('rejects .7z for %s transfer type', (transferType) => {
      const node: FileNode = {
        name: 'archive.7z',
        path: '/archive.7z',
        type: 'file',
      }

      const wrapper = triggerEnter(transferType, node)

      expect(wrapper.emitted('add')).toBeUndefined()
    })

    it.each(['zipfile', 'zipped bag'])(
      'keeps non-addable directories navigable while keeping non-addable files disabled for %s',
      (transferType) => {
        const wrapper = mount(TreeViewContainer, {
          global: {
            ...global,
            plugins: [i18n],
          },
          props: {
            ...defaultProps,
            currentLocation: 'loc1',
            transferType,
            fileNodes: [],
          },
        })

        const treeView = wrapper.findComponent(TreeView)
        const getDisabled = treeView.props('getDisabled') as ((node: FileNode) => boolean) | undefined
        const getContentClass = treeView.props('getContentClass') as ((node: FileNode) => Record<string, boolean>) | undefined

        if (!getDisabled || !getContentClass) {
          throw new Error('Expected getDisabled and getContentClass handlers')
        }

        const directoryNode: FileNode = {
          name: 'ZippedDirectoryTransfers',
          path: '/ZippedDirectoryTransfers',
          type: 'directory',
          children: [],
          children_fetched: true,
        }
        const nonAddableFileNode: FileNode = {
          name: 'README.md',
          path: '/README.md',
          type: 'file',
        }

        expect(getDisabled(directoryNode)).toBe(false)
        expect(getContentClass(directoryNode)).toMatchObject({
          'tree-node-expandable': true,
          'tree-node-not-addable': true,
          'tree-node-not-addable-dir': true,
        })

        expect(getDisabled(nonAddableFileNode)).toBe(true)
        expect(getContentClass(nonAddableFileNode)).toMatchObject({
          'tree-node-expandable': false,
          'tree-node-not-addable': true,
          'tree-node-not-addable-file': true,
        })
      },
    )
  })

  it('does not show tree container when no location is selected', () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: defaultProps,
    })

    expect(wrapper.find('.transfer-tree-container').exists()).toBe(false)
    expect(wrapper.find('.transfer-tree-add-btn').exists()).toBe(false)
  })

  describe('WCAG Compliance', () => {
    it('should have proper location selector labeling', () => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: defaultProps,
      })

      const select = wrapper.find('#source-location-select')
      expect(select.exists()).toBe(true)
      expect(select.attributes('aria-describedby')).toBe('location-help')

      const label = wrapper.find('label[for="source-location-select"]')
      expect(label.exists()).toBe(true)
      expect(label.classes()).toContain('sr-only')

      const helpText = wrapper.find('#location-help')
      expect(helpText.exists()).toBe(true)
      expect(helpText.classes()).toContain('sr-only')
    })

    it('should have proper tree container ARIA attributes', () => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          fileNodes: mockFileNodes,
        },
      })

      const treeContainer = wrapper.find('.transfer-tree-container')
      expect(treeContainer.attributes('role')).toBe('region')
      expect(treeContainer.attributes('aria-label')).toBe('File browser')
      expect(treeContainer.attributes('aria-busy')).toBe('false')

      // The tree role is now on the TreeView component, not the container
      const treeView = wrapper.findComponent(TreeView)
      expect(treeView.exists()).toBe(true)
    })

    it('should have accessible error states', () => {
      const errorMessage = 'Failed to load files'
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          apiError: errorMessage,
        },
      })

      const alert = wrapper.find('.alert-danger')
      expect(alert.attributes('role')).toBe('alert')
      expect(alert.attributes('aria-live')).toBe('assertive')
      expect(alert.text()).toBe(errorMessage)
    })

    it('should have accessible external add action', () => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          fileNodes: mockFileNodes,
        },
      })

      const externalAddButton = wrapper.find('.transfer-tree-add-btn')
      expect(externalAddButton.attributes('type')).toBe('button')
      expect(externalAddButton.attributes('aria-label')).toBe('Select a file or folder to add')
    })

    it('should update aria-busy when loading', () => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          loading: true,
        },
      })

      const treeContainer = wrapper.find('.transfer-tree-container')
      expect(treeContainer.attributes('aria-busy')).toBe('true')
    })
  })
})

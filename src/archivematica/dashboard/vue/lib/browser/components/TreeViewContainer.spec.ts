import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import TreeViewContainer from '@/browser/components/TreeViewContainer.vue'
import TreeView from '@/browser/components/TreeView.vue'
import type { SourceLocation, FileNode } from '@/shared/models'

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
    selectedPath: '',
    canAddSelectedPath: false,
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
    expect(treeView.props()).toEqual({
      nodes: mockFileNodes,
      selectedPath: '',
      transferType: 'standard',
      expandedPaths: [],
    })
  })

  it('emits select event when tree node is selected', async () => {
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
    treeView.vm.$emit('select', { path: '/folder1', canAdd: true })

    const selectEvents = wrapper.emitted('select') ?? []
    const firstSelect = selectEvents[0]
    if (!firstSelect) {
      throw new Error('Expected select event payload')
    }
    expect(firstSelect).toEqual([{ path: '/folder1', canAdd: true }])
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
    treeView.vm.$emit('expand', firstFileNode)

    const expandEvents = wrapper.emitted('expand') ?? []
    const firstExpand = expandEvents[0]
    if (!firstExpand) {
      throw new Error('Expected expand event payload')
    }
    expect(firstExpand).toEqual([firstFileNode])
  })

  it('disables Add button when no path is selected', () => {
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

    const addButton = wrapper.find('button.add-button')
    expect(addButton.attributes('disabled')).toBeDefined()
  })

  it('enables Add button when path is selected', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
        selectedPath: '/folder1',
        canAddSelectedPath: true,
      },
    })

    const addButton = wrapper.find('button.add-button')
    expect(addButton.attributes('disabled')).toBeUndefined()
  })

  it('emits add event when Add button is clicked', async () => {
    const wrapper = mount(TreeViewContainer, {
      global: {
        ...global,
        plugins: [i18n],
      },
      props: {
        ...defaultProps,
        currentLocation: 'loc1',
        fileNodes: mockFileNodes,
        selectedPath: '/folder1',
        canAddSelectedPath: true,
      },
    })

    const addButton = wrapper.find('button.add-button')
    await addButton.trigger('click')

    expect(wrapper.emitted('add')).toBeTruthy()
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
  })

  it('updates selected path in tree when prop changes', async () => {
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
    expect(treeView.props('selectedPath')).toBe('')

    await wrapper.setProps({ selectedPath: '/folder1' })

    expect(treeView.props('selectedPath')).toBe('/folder1')
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

    it('should have accessible add button', () => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          fileNodes: mockFileNodes,
          selectedPath: '/folder1',
          canAddSelectedPath: true,
        },
      })

      const addButton = wrapper.find('.add-button')
      expect(addButton.attributes('type')).toBe('button')
      expect(addButton.attributes('aria-disabled')).toBe('false')
      expect(addButton.attributes('aria-label')).toBe('Add /folder1 to transfer')
    })

    it('should have proper disabled state for add button', () => {
      const wrapper = mount(TreeViewContainer, {
        global: {
          ...global,
          plugins: [i18n],
        },
        props: {
          ...defaultProps,
          currentLocation: 'loc1',
          fileNodes: mockFileNodes,
          selectedPath: '',
        },
      })

      const addButton = wrapper.find('.add-button')
      expect(addButton.attributes('aria-disabled')).toBe('true')
      expect(addButton.attributes('disabled')).toBeDefined()
      expect(addButton.attributes('aria-label')).toBe('Select a file or folder to add')
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

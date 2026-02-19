import { describe, it, expect, beforeEach, beforeAll, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createI18nMock } from '@/shared/i18n'
import App from './App.vue'
import type { TransferComponent, TransferFormData } from '@/browser/types'
import { TRANSFER_STARTED_EVENT } from '@/shared/events/monitor'

// Type for the TransferBrowser component instance
type TransferBrowserComponent = {
  transferComponents: TransferComponent[]
  transferFormData: TransferFormData
  editComponent: (id: string) => void
  removeComponent: (id: string) => void
  alerts: Array<{ type: string, message: string }>
  currentLocation: string
  showBrowseTree: boolean
  addSelectedPath: (node: { path: string }) => void
  [key: string]: unknown
}

// Mock the useTransferBrowser composable
const mockCreateTransfer = vi.fn()
const mockGetProcessingConfigs = vi.fn()
const mockGetSourceLocations = vi.fn()
const mockBrowseLocation = vi.fn()
const mockOpenComponentEditor = vi.fn()

vi.mock('./composables/useTransferBrowser', () => {
  const loading = ref(false)
  const error = ref<string | null>(null)
  return {
    useTransferBrowser: () => ({
      loading,
      error,
      getProcessingConfigs: mockGetProcessingConfigs,
      getSourceLocations: mockGetSourceLocations,
      browseLocation: mockBrowseLocation,
      createTransfer: mockCreateTransfer,
      openComponentEditor: mockOpenComponentEditor,
    }),
  }
})

let i18nMock: Awaited<ReturnType<typeof createI18nMock>>

beforeAll(async () => {
  i18nMock = await createI18nMock()
})

describe('TransferBrowser', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Setup default mocks
    mockGetProcessingConfigs.mockResolvedValue([
      { pk: 'default', name: 'default' },
      { pk: 'automated', name: 'automated' },
    ])

    mockGetSourceLocations.mockResolvedValue([
      {
        uuid: 'loc-1',
        description: 'Location 1',
        enabled: true,
        path: '/path1',
        purpose: 'TS',
        relative_path: '/path1',
        space: 'space1',
        used: 0,
        quota: null,
      },
    ])

    mockBrowseLocation.mockResolvedValue([])
  })

  describe('Source Locations', () => {
    it('auto-selects the first enabled location when multiple are available', async () => {
      mockGetSourceLocations.mockResolvedValueOnce([
        {
          uuid: 'loc-1',
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
          uuid: 'loc-2',
          description: 'Location 2',
          enabled: true,
          path: '/path2',
          purpose: 'TS',
          relative_path: '/path2',
          space: 'space2',
          used: 0,
          quota: null,
        },
      ])

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      expect(transferBrowser.currentLocation).toBe('loc-1')
      expect(mockBrowseLocation).toHaveBeenCalledWith('loc-1', '')
    })
  })

  describe('Transfer Components', () => {
    it('does not add duplicate components for the same location and path', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.addSelectedPath({ path: '/same-path' })
      transferBrowser.addSelectedPath({ path: '/same-path' })

      expect(transferBrowser.transferComponents).toHaveLength(1)
    })

    it('removes a component when removal is confirmed', async () => {
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents = [
        {
          id: 'component-1',
          path: '/home/artefactual',
          location: 'loc-1',
        },
      ]

      await wrapper.vm.$nextTick()

      transferBrowser.removeComponent('component-1')

      expect(confirmSpy).toHaveBeenCalledWith(
        'Are you sure you want to remove this transfer component (/home/artefactual)?',
      )
      expect(transferBrowser.transferComponents).toHaveLength(0)
    })

    it('keeps a component when removal is cancelled', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(false)

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents = [
        {
          id: 'component-1',
          path: '/home/artefactual',
          location: 'loc-1',
        },
      ]

      await wrapper.vm.$nextTick()

      transferBrowser.removeComponent('component-1')

      expect(transferBrowser.transferComponents).toHaveLength(1)
    })
  })

  describe('Processing Configuration Behavior', () => {
    it('should call startTransfer with "default" when main button is clicked', async () => {
      mockCreateTransfer.mockResolvedValue({ name: 'test-transfer' })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      // Wait for component to initialize
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      // Add a component to enable transfer buttons
      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      // Set transfer name
      transferBrowser.transferFormData.name = 'test-transfer'

      await wrapper.vm.$nextTick()

      // Find and click the main "Start transfer" button
      const startButton = wrapper.find('button.btn-success').element as HTMLButtonElement
      expect(startButton.disabled).toBe(false)

      await wrapper.find('button.btn-success').trigger('click')

      expect(mockCreateTransfer).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'test-transfer',
          processingConfig: 'default',
        }),
      )
    })

    it('should display correct dropdown text for processing configurations', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      // Wait for component to initialize
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      // Check dropdown menu items
      const dropdownItems = wrapper.findAll('.processing-config-choice')
      expect(dropdownItems).toHaveLength(2)

      const defaultConfigItem = dropdownItems[0]
      const automatedConfigItem = dropdownItems[1]
      if (!defaultConfigItem || !automatedConfigItem) {
        throw new Error('Expected two processing configuration menu items')
      }

      expect(defaultConfigItem.text()).toBe('Start with "default" configuration')
      expect(automatedConfigItem.text()).toBe('Start with "automated" configuration')
    })

    it('should call startTransfer with specific config when dropdown item is clicked', async () => {
      mockCreateTransfer.mockResolvedValue({ name: 'test-transfer' })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      // Wait for component to initialize
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      // Add a component to enable transfer buttons
      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      // Set transfer name
      transferBrowser.transferFormData.name = 'test-transfer'

      await wrapper.vm.$nextTick()

      // Click on automated config dropdown item
      const automatedConfigItem = wrapper.findAll('.processing-config-choice')[1]
      if (!automatedConfigItem) {
        throw new Error('Expected automated processing configuration menu item')
      }
      await automatedConfigItem.trigger('click')

      expect(mockCreateTransfer).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'test-transfer',
          processingConfig: 'automated',
        }),
      )
    })

    it('shows info alert with transfer name and processing configuration', async () => {
      mockCreateTransfer.mockResolvedValue({
        uuid: 'transfer-uuid',
        name: 'test-transfer',
        status: 'processing',
      })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })
      transferBrowser.transferFormData.name = 'test-transfer'

      await wrapper.vm.$nextTick()
      await wrapper.find('button.btn-success').trigger('click')
      await flushPromises()

      const lastAlert = transferBrowser.alerts[transferBrowser.alerts.length - 1]
      expect(lastAlert).toBeDefined()
      expect(lastAlert?.type).toBe('info')
      expect(lastAlert?.message).toBe(
        'Transfer "test-transfer" started with processing configuration "default".',
      )
    })

    it('dispatches a transfer-started event after a successful transfer', async () => {
      mockCreateTransfer.mockResolvedValue({
        id: 'transfer-1',
      })
      const dispatchSpy = vi.spyOn(document, 'dispatchEvent')

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })
      transferBrowser.transferFormData.name = 'test-transfer'

      await wrapper.vm.$nextTick()
      await wrapper.find('button.btn-success').trigger('click')
      await flushPromises()

      expect(
        dispatchSpy.mock.calls.some(([event]) => event.type === TRANSFER_STARTED_EVENT),
      ).toBe(true)
      dispatchSpy.mockRestore()
    })
  })

  describe('Transfer Name Logic', () => {
    it('should use user-provided name for standard transfers', async () => {
      mockCreateTransfer.mockResolvedValue({ name: 'my-transfer' })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      transferBrowser.transferFormData.name = 'my-transfer'
      transferBrowser.transferFormData.type = 'standard'

      await wrapper.vm.$nextTick()
      await wrapper.find('button.btn-success').trigger('click')

      expect(mockCreateTransfer).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'my-transfer',
        }),
      )
    })

    it('should use "ZippedBag" for zipped bag transfers', async () => {
      mockCreateTransfer.mockResolvedValue({ name: 'ZippedBag' })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      transferBrowser.transferFormData.name = 'user-provided-name'
      transferBrowser.transferFormData.type = 'zipped bag'

      await wrapper.vm.$nextTick()
      await wrapper.find('button.btn-success').trigger('click')

      expect(mockCreateTransfer).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'ZippedBag',
        }),
      )

      // Check that the success alert would show "ZippedBag"
      // Note: This is tested through the component's internal logic
      // The actual alert display would need integration testing
    })

    it('should use "ZipFile" for zipfile transfers', async () => {
      mockCreateTransfer.mockResolvedValue({ name: 'ZipFile' })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      transferBrowser.transferFormData.name = 'user-provided-name'
      transferBrowser.transferFormData.type = 'zipfile'

      await wrapper.vm.$nextTick()
      await wrapper.find('button.btn-success').trigger('click')

      expect(mockCreateTransfer).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'ZipFile',
        }),
      )
    })
  })

  describe('Button States', () => {
    it('should disable transfer buttons when no components are added', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const startButton = wrapper.find('button.btn-success').element as HTMLButtonElement
      const dropdownButton = wrapper.find('button.dropdown-toggle').element as HTMLButtonElement

      expect(startButton.disabled).toBe(true)
      expect(dropdownButton.disabled).toBe(true)
    })

    it('should enable transfer buttons when components are added and name is provided', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      transferBrowser.transferFormData.name = 'test-transfer'

      await wrapper.vm.$nextTick()

      const startButton = wrapper.find('button.btn-success').element as HTMLButtonElement
      const dropdownButton = wrapper.find('button.dropdown-toggle').element as HTMLButtonElement

      expect(startButton.disabled).toBe(false)
      expect(dropdownButton.disabled).toBe(false)
    })

    it('should retain current location after a successful transfer', async () => {
      mockCreateTransfer.mockResolvedValueOnce({
        uuid: 'transfer-uuid',
        name: 'Test Transfer',
        status: 'processing',
      })

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await flushPromises()

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })
      transferBrowser.transferFormData.name = 'test-transfer'

      await wrapper.vm.$nextTick()

      await wrapper.find('button.btn-success').trigger('click')
      await flushPromises()

      expect(transferBrowser.currentLocation).toBe('loc-1')
    })
  })

  describe('Transfer Type Select', () => {
    it('should disable transfer type selection after components are added', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      const transferBrowser = wrapper.vm as unknown as TransferBrowserComponent
      transferBrowser.transferComponents.push({
        id: '1',
        path: '/test/path',
        location: 'loc-1',
      })

      await wrapper.vm.$nextTick()

      const transferTypeSelect = wrapper.find('#transfer-type').element as HTMLSelectElement
      expect(transferTypeSelect.disabled).toBe(true)
    })
  })

  describe('Tree Rendering Guards', () => {
    it('does not render file size for directory-typed nodes without children arrays', async () => {
      mockBrowseLocation.mockResolvedValueOnce([
        {
          name: 'dir-no-children-array',
          path: '/dir-no-children-array',
          type: 'directory',
          size: 2048,
          children: undefined,
          children_fetched: true,
          loading: false,
        },
        {
          name: 'file-with-size.txt',
          path: '/file-with-size.txt',
          type: 'file',
          size: 2048,
          children: undefined,
          children_fetched: false,
          loading: false,
        },
      ])

      const wrapper = mount(App, {
        global: {
          plugins: [i18nMock],
        },
      })

      await wrapper.vm.$nextTick()
      await flushPromises()

      await wrapper.find('button.btn-browse').trigger('click')
      await wrapper.vm.$nextTick()

      const nodeRows = wrapper.findAll('.tree-node-content')
      const directoryRow = nodeRows.find(row => row.text().includes('dir-no-children-array'))
      const fileRow = nodeRows.find(row => row.text().includes('file-with-size.txt'))

      expect(directoryRow).toBeDefined()
      expect(fileRow).toBeDefined()
      expect(directoryRow?.text()).not.toContain('2 KB')
      expect(fileRow?.text()).toContain('2 KB')
    })
  })

  describe('WCAG Compliance', () => {
    beforeEach(async () => {
      mockGetProcessingConfigs.mockResolvedValue([
        { pk: 'default', name: 'default' },
        { pk: 'automated', name: 'automated' },
      ])
      mockGetSourceLocations.mockResolvedValue([
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
      ])
    })

    it('should have proper form labeling and ARIA attributes', async () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Check form role and label
      const form = wrapper.find('#transfer-browser-form')
      expect(form.attributes('role')).toBe('form')
      expect(form.attributes('aria-label')).toBe('Transfer configuration form')

      // Check select has proper labeling
      const transferTypeSelect = wrapper.find('#transfer-type')
      expect(transferTypeSelect.exists()).toBe(true)
      expect(transferTypeSelect.attributes('aria-describedby')).toBe('transfer-type-help')

      const transferTypeLabel = wrapper.find('label[for="transfer-type"]')
      expect(transferTypeLabel.exists()).toBe(true)
      expect(transferTypeLabel.classes()).toContain('sr-only')

      // Check help text is properly associated
      const helpText = wrapper.find('#transfer-type-help')
      expect(helpText.exists()).toBe(true)
      expect(helpText.classes()).toContain('help-block')
    })

    it('should have proper button labeling and states', async () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Check browse button
      const browseButton = wrapper.find('button[aria-expanded]')
      expect(browseButton.exists()).toBe(true)
      expect(browseButton.attributes('aria-expanded')).toBe('false')

      // Check start transfer button
      const startButton = wrapper.find('button.btn-success')
      expect(startButton.attributes('aria-disabled')).toBe('true')
      expect(startButton.attributes('disabled')).toBeDefined()

      // Check dropdown toggle
      const dropdownToggle = wrapper.find('button.dropdown-toggle')
      expect(dropdownToggle.attributes('aria-haspopup')).toBe('true')
      expect(dropdownToggle.attributes('aria-expanded')).toBe('false')
    })

    it('should have accessible checkbox', async () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      const checkbox = wrapper.find('#auto-approve-checkbox')
      expect(checkbox.exists()).toBe(true)
      expect(checkbox.attributes('aria-describedby')).toBe('auto-approve-help')

      const label = wrapper.find('label[for="auto-approve-checkbox"]')
      expect(label.exists()).toBe(true)

      const helpText = wrapper.find('#auto-approve-help')
      expect(helpText.exists()).toBe(true)
      expect(helpText.classes()).toContain('sr-only')
    })

    it('should have skip link for accessibility', () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      const skipLink = wrapper.find('a[href="#file-browser"]')
      expect(skipLink.exists()).toBe(true)
      expect(skipLink.classes()).toContain('sr-only')
      expect(skipLink.classes()).toContain('sr-only-focusable')
      expect(skipLink.text()).toBe('Skip to file browser')
    })

    it('should have semantic HTML structure', () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      // Check main element
      const main = wrapper.find('section')
      expect(main.exists()).toBe(true)
    })
  })

  describe('Disk Image Edit Functionality', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('should call openComponentEditor for disk image components', async () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      await wrapper.vm.$nextTick()

      // Set transfer type to disk image
      const vm = wrapper.vm as unknown as TransferBrowserComponent
      vm.transferFormData.type = 'disk image'

      // Add a component
      vm.transferComponents = [
        {
          id: 'component-1',
          path: '/test/path',
          location: 'location-1',
          uuid: 'existing-uuid-123',
        },
      ]

      await wrapper.vm.$nextTick()

      // Call editComponent directly
      await vm.editComponent('component-1')

      // Should call the composable with correct parameters
      const firstComponent = vm.transferComponents[0]
      if (!firstComponent) {
        throw new Error('Expected transfer component to be present')
      }
      expect(mockOpenComponentEditor).toHaveBeenCalledWith(firstComponent, 'disk image')
    })

    it('should handle component not found gracefully', async () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      await wrapper.vm.$nextTick()

      // Set transfer type to disk image
      const vm = wrapper.vm as unknown as TransferBrowserComponent
      vm.transferFormData.type = 'disk image'
      vm.transferComponents = []

      await wrapper.vm.$nextTick()

      // Call editComponent with non-existent ID
      await vm.editComponent('non-existent-id')

      // Should not call the composable
      expect(mockOpenComponentEditor).not.toHaveBeenCalled()
    })

    it('should handle openComponentEditor errors', async () => {
      const wrapper = mount(App, {
        global: { plugins: [i18nMock] },
      })

      await wrapper.vm.$nextTick()

      // Set transfer type to disk image
      const vm = wrapper.vm as unknown as TransferBrowserComponent
      vm.transferFormData.type = 'disk image'

      // Add a component
      vm.transferComponents = [
        {
          id: 'component-1',
          path: '/test/path',
          location: 'location-1',
          uuid: 'existing-uuid-123',
        },
      ]

      // Mock openComponentEditor to throw an error
      mockOpenComponentEditor.mockImplementationOnce(() => {
        throw new Error('Editor not available')
      })

      await wrapper.vm.$nextTick()

      // Call editComponent directly
      await vm.editComponent('component-1')

      // Should call the composable once
      expect(mockOpenComponentEditor).toHaveBeenCalledTimes(1)
    })
  })
})

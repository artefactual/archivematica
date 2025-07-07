import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import PathContainer from '@/browser/components/PathContainer.vue'
import type { TransferComponent } from '@/shared/models'

const i18n = createI18nMock()

describe('PathContainer', () => {
  const mockComponents: TransferComponent[] = [
    {
      id: '1',
      path: '/home/user/documents/file1.txt',
      location: 'uuid-1',
    },
    {
      id: '2',
      path: '/home/user/documents/folder/file2.pdf',
      location: 'uuid-2',
    },
  ]

  const defaultProps = {
    components: mockComponents,
    transferType: 'standard',
  }

  it('renders all transfer components', () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const items = wrapper.findAll('.transfer-component-item')
    expect(items).toHaveLength(2)

    const firstItem = items[0]
    const secondItem = items[1]
    if (!firstItem || !secondItem) {
      throw new Error('Expected two transfer component items')
    }

    expect(firstItem.find('.transfer_path').text()).toBe('/home/user/documents/file1.txt')
    expect(secondItem.find('.transfer_path').text()).toBe('/home/user/documents/folder/file2.pdf')
  })

  it('renders correct IDs for each component item', () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const items = wrapper.findAll('.transfer-component-item')
    const firstItem = items[0]
    const secondItem = items[1]
    if (!firstItem || !secondItem) {
      throw new Error('Expected two transfer component items')
    }
    expect(firstItem.attributes('id')).toBe('transfer-component-path-item-1')
    expect(secondItem.attributes('id')).toBe('transfer-component-path-item-2')
  })

  it('shows edit button only for disk image transfer type', async () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    // Should not show edit buttons for standard transfer
    expect(wrapper.findAll('.transfer_path_edit_btn')).toHaveLength(0)

    // Should show edit buttons for disk image transfer
    await wrapper.setProps({ transferType: 'disk image' })
    const editButtons = wrapper.findAll('.transfer_path_edit_btn')
    expect(editButtons).toHaveLength(2)
  })

  it('emits edit event when edit button is clicked', async () => {
    const wrapper = mount(PathContainer, {
      props: {
        ...defaultProps,
        transferType: 'disk image',
      },
      global: {
        plugins: [i18n],
      },
    })

    const editButtons = wrapper.findAll('.transfer_path_edit_btn')
    const firstEditButton = editButtons[0]
    if (!firstEditButton) {
      throw new Error('Expected an edit button')
    }
    await firstEditButton.trigger('click')

    const editEvents = wrapper.emitted('edit') ?? []
    const firstEditEvent = editEvents[0]
    if (!firstEditEvent) {
      throw new Error('Expected an edit event payload')
    }
    expect(firstEditEvent).toEqual(['1'])
  })

  it('emits remove event when delete button is clicked', async () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const deleteButtons = wrapper.findAll('.transfer_path_delete_btn')
    const secondDeleteButton = deleteButtons[1]
    if (!secondDeleteButton) {
      throw new Error('Expected a second delete button')
    }
    await secondDeleteButton.trigger('click')

    const removeEvents = wrapper.emitted('remove') ?? []
    const firstRemoveEvent = removeEvents[0]
    if (!firstRemoveEvent) {
      throw new Error('Expected a remove event payload')
    }
    expect(firstRemoveEvent).toEqual(['2'])
  })

  it('renders correct aria-labels for buttons', () => {
    const wrapper = mount(PathContainer, {
      props: {
        ...defaultProps,
        transferType: 'disk image',
      },
      global: {
        plugins: [i18n],
      },
    })

    const editButtons = wrapper.findAll('.transfer_path_edit_btn')
    const deleteButtons = wrapper.findAll('.transfer_path_delete_btn')
    const editButton = editButtons[0]
    const deleteButton = deleteButtons[0]

    if (!editButton || !deleteButton) {
      throw new Error('Expected edit and delete buttons')
    }

    expect(editButton.attributes('aria-label')).toBe('Edit component: /home/user/documents/file1.txt')
    expect(deleteButton.attributes('aria-label')).toBe('Remove component: /home/user/documents/file1.txt')
  })

  it('renders empty state correctly', () => {
    const wrapper = mount(PathContainer, {
      props: {
        components: [],
        transferType: 'standard',
      },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.findAll('.transfer-component-item')).toHaveLength(0)
    expect(wrapper.find('#path_container').exists()).toBe(true)
  })

  it('handles components with long paths correctly', () => {
    const longPathComponent: TransferComponent = {
      id: '3',
      path: '/very/long/path/that/might/need/to/wrap/in/the/ui/component/display/area/file.txt',
      location: 'uuid-3',
    }

    const wrapper = mount(PathContainer, {
      props: {
        components: [longPathComponent],
        transferType: 'standard',
      },
      global: {
        plugins: [i18n],
      },
    })

    const pathElement = wrapper.find('.transfer_path')
    expect(pathElement.text()).toBe(longPathComponent.path)
    // Just check that the element exists with the long path - CSS testing is not reliable in unit tests
    expect(pathElement.exists()).toBe(true)
  })
})

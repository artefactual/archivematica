import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import PathContainer from './PathContainer.vue'

const i18n = createI18nMock()

describe('PathContainer', () => {
  const mockItems = [
    {
      id: '1',
      path: '/home/user/documents/file1.txt',
    },
    {
      id: '2',
      path: '/home/user/documents/folder/file2.pdf',
    },
  ]

  const defaultProps = {
    items: mockItems,
    editLabel: (path: string) => `Edit path: ${path}`,
    removeLabel: (path: string) => `Remove path: ${path}`,
  }

  it('renders all transfer components', () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const items = wrapper.findAll('.path-item')
    expect(items).toHaveLength(2)

    const firstItem = items[0]
    const secondItem = items[1]
    if (!firstItem || !secondItem) {
      throw new Error('Expected two transfer component items')
    }

    expect(firstItem.find('.path').text()).toBe('/home/user/documents/file1.txt')
    expect(secondItem.find('.path').text()).toBe('/home/user/documents/folder/file2.pdf')
  })

  it('renders correct IDs for each component item', () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    const items = wrapper.findAll('.path-item')
    const firstItem = items[0]
    const secondItem = items[1]
    if (!firstItem || !secondItem) {
      throw new Error('Expected two transfer component items')
    }
    expect(firstItem.attributes('id')).toBe('path-item-1')
    expect(secondItem.attributes('id')).toBe('path-item-2')
  })

  it('shows edit button only when enabled', async () => {
    const wrapper = mount(PathContainer, {
      props: defaultProps,
      global: {
        plugins: [i18n],
      },
    })

    // Should not show edit buttons by default
    expect(wrapper.findAll('.edit-btn')).toHaveLength(0)

    // Should show edit buttons when enabled
    await wrapper.setProps({ showEdit: true })
    const editButtons = wrapper.findAll('.edit-btn')
    expect(editButtons).toHaveLength(2)
  })

  it('emits edit event when edit button is clicked', async () => {
    const wrapper = mount(PathContainer, {
      props: {
        ...defaultProps,
        showEdit: true,
      },
      global: {
        plugins: [i18n],
      },
    })

    const editButtons = wrapper.findAll('.edit-btn')
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

    const deleteButtons = wrapper.findAll('.delete-btn')
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
        showEdit: true,
      },
      global: {
        plugins: [i18n],
      },
    })

    const editButtons = wrapper.findAll('.edit-btn')
    const deleteButtons = wrapper.findAll('.delete-btn')
    const editButton = editButtons[0]
    const deleteButton = deleteButtons[0]

    if (!editButton || !deleteButton) {
      throw new Error('Expected edit and delete buttons')
    }

    expect(editButton.attributes('aria-label')).toBe('Edit path: /home/user/documents/file1.txt')
    expect(deleteButton.attributes('aria-label')).toBe('Remove path: /home/user/documents/file1.txt')
  })

  it('renders empty state correctly', () => {
    const wrapper = mount(PathContainer, {
      props: {
        items: [],
        removeLabel: (path: string) => `Remove path: ${path}`,
      },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.findAll('.path-item')).toHaveLength(0)
    expect(wrapper.find('.path-container').exists()).toBe(true)
  })

  it('handles components with long paths correctly', () => {
    const longPathItem = {
      id: '3',
      path: '/very/long/path/that/might/need/to/wrap/in/the/ui/component/display/area/file.txt',
    }

    const wrapper = mount(PathContainer, {
      props: {
        items: [longPathItem],
        removeLabel: (path: string) => `Remove path: ${path}`,
      },
      global: {
        plugins: [i18n],
      },
    })

    const pathElement = wrapper.find('.path')
    expect(pathElement.text()).toBe(longPathItem.path)
    expect(pathElement.exists()).toBe(true)
  })
})

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import TreeNode from './TreeNode.vue'

vi.mock('reka-ui', () => {
  const TreeItem = defineComponent({
    name: 'TreeItem',
    setup(_, { slots }) {
      return () => h('div', { class: 'tree-item', role: 'treeitem' }, slots.default?.({
        isExpanded: true,
        isSelected: false,
      }))
    },
  })

  return {
    TreeItem,
    injectTreeRootContext: () => null,
  }
})

describe('TreeNode', () => {
  it('renders a leaf node label and file icon', () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: { id: 'node-1', label: 'Node 1' },
        level: 1,
      },
    })

    expect(wrapper.find('.tree-node-content').exists()).toBe(true)
    expect(wrapper.text()).toContain('Node 1')
    expect(wrapper.find('.tree-node-icon-file').exists()).toBe(true)
    expect(wrapper.find('.tree-node-toggle').exists()).toBe(false)
  })

  it('renders a branch node with folder icon', () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'node-2',
          label: 'Node 2',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
      },
    })

    expect(wrapper.find('.fa-folder, .fa-folder-open').exists()).toBe(true)
    expect(wrapper.find('.tree-node-toggle').exists()).toBe(false)
    expect(wrapper.find('.tree-children').exists()).toBe(true)
  })

  it('exposes structural metadata in slot props', () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'node-2',
          label: 'Node 2',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 2,
      },
      slots: {
        label: ({ level, hasChildren }) => `L${String(level)}-${String(hasChildren)}`,
      },
    })

    expect(wrapper.text()).toContain('L2-true')
  })

  it('does not prevent default Right Arrow behavior when rightToggles is false', async () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'node-2',
          label: 'Node 2',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
        rightToggles: false,
      },
    })

    const event = new KeyboardEvent('keydown', {
      key: 'ArrowRight',
      bubbles: true,
      cancelable: true,
    })
    wrapper.find('[role="treeitem"]').element.dispatchEvent(event)
    await wrapper.vm.$nextTick()

    expect(event.defaultPrevented).toBe(false)
    expect(wrapper.emitted('toggle')).toBeUndefined()
  })

  it('prevents default and toggles on Right Arrow when rightToggles is true', async () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'node-3',
          label: 'Node 3',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
        rightToggles: true,
      },
    })

    const event = new KeyboardEvent('keydown', {
      key: 'ArrowRight',
      bubbles: true,
      cancelable: true,
    })
    wrapper.find('[role="treeitem"]').element.dispatchEvent(event)
    await wrapper.vm.$nextTick()

    expect(event.defaultPrevented).toBe(true)
    expect(wrapper.emitted('toggle')).toHaveLength(1)
  })

  it('forwards originalEvent from recursive child select emits', async () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'parent',
          label: 'Parent',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
      },
    })

    const treeItems = wrapper.findAll('[role="treeitem"]')
    const childItem = treeItems[1]
    if (!childItem) {
      throw new Error('Expected recursive child tree item to be rendered')
    }
    await childItem.trigger('keydown.enter', { key: 'Enter' })

    const events = wrapper.emitted('select')
    expect(events).toHaveLength(1)
    expect(events?.[0]?.[0]).toEqual({ id: 'child-1', label: 'Child 1' })
    expect(events?.[0]?.[1]).toBeInstanceOf(KeyboardEvent)
  })

  it('applies actionsFocusable=false to nested action slots', () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'parent',
          label: 'Parent',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
        actionsFocusable: false,
      },
      slots: {
        actions: ({ actionProps }) => h('button', { class: 'action-btn', ...actionProps }, 'Add'),
      },
    })

    const actionButtons = wrapper.findAll('.action-btn')
    expect(actionButtons).toHaveLength(2)
    const firstButton = actionButtons[0]
    const secondButton = actionButtons[1]
    if (!firstButton || !secondButton) {
      throw new Error('Expected parent and child action buttons')
    }
    expect(firstButton.attributes('tabindex')).toBe('-1')
    expect(secondButton.attributes('tabindex')).toBe('-1')
  })

  it('does not emit select or toggle for disabled node interactions', async () => {
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'disabled-parent',
          label: 'Disabled Parent',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
        getDisabled: () => true,
        rightToggles: true,
      },
    })

    const treeItem = wrapper.find('[role="treeitem"]')
    await treeItem.trigger('keydown.enter', { key: 'Enter' })
    await treeItem.trigger('keydown.space', { key: ' ' })
    await treeItem.trigger('keydown.right', { key: 'ArrowRight' })
    await treeItem.trigger('keydown.left', { key: 'ArrowLeft' })
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('select')).toBeUndefined()
    expect(wrapper.emitted('toggle')).toBeUndefined()
  })

  it('does not invoke onEnter for disabled nodes', async () => {
    const onEnter = vi.fn()
    const wrapper = mount(TreeNode, {
      props: {
        node: {
          id: 'disabled-enter',
          label: 'Disabled Enter',
          children: [{ id: 'child-1', label: 'Child 1' }],
        },
        level: 1,
        getDisabled: () => true,
        onEnter,
      },
    })

    await wrapper.find('[role="treeitem"]').trigger('keydown.enter', { key: 'Enter' })
    expect(onEnter).not.toHaveBeenCalled()
    expect(wrapper.emitted('select')).toBeUndefined()
    expect(wrapper.emitted('toggle')).toBeUndefined()
  })
})

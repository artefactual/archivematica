import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Tree from '@/shared/components/TreeView.vue'
import { h } from 'vue'

const sampleTree = [
  {
    id: 'root',
    label: 'Root',
    children: [
      { id: 'file-1', label: 'File 1' },
      {
        id: 'dir-1',
        label: 'Dir 1',
        children: [{ id: 'file-2', label: 'File 2' }],
      },
    ],
  },
]

const sampleTreeMultiRoot = [
  { id: 'first', label: 'First' },
  { id: 'second', label: 'Second' },
]

const sampleTreeWithoutIds = [
  { label: 'First' },
  { label: 'Second' },
]

describe('TreeView', () => {
  it('renders a root list container', () => {
    const wrapper = mount(Tree, { props: { items: sampleTree } })
    expect(wrapper.find('.tree').exists()).toBe(true)
  })

  it('renders labels for nodes', () => {
    const wrapper = mount(Tree, { props: { items: sampleTree } })
    expect(wrapper.text()).toContain('Root')
  })

  it('emits select with node payload', async () => {
    const wrapper = mount(Tree, { props: { items: sampleTree } })
    const treeNode = wrapper.findComponent({ name: 'TreeNode' })
    ;(treeNode.vm as { $emit: (event: string, payload: unknown) => void }).$emit('select', sampleTree[0])
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('select')?.[0]?.[0]).toEqual(sampleTree[0])
  })

  it('emits toggle with node payload', async () => {
    const wrapper = mount(Tree, { props: { items: sampleTree } })
    const treeNode = wrapper.findComponent({ name: 'TreeNode' })
    ;(treeNode.vm as { $emit: (event: string, payload: unknown) => void }).$emit('toggle', sampleTree[0])
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('toggle')?.[0]?.[0]).toEqual(sampleTree[0])
  })

  it('renders label and action slots when provided', () => {
    const wrapper = mount(Tree, {
      props: { items: sampleTree },
      slots: {
        label: ({ node }) => `Label:${node.label}`,
        actions: () => h('button', { class: 'action-slot' }, 'Action'),
      },
    })
    expect(wrapper.text()).toContain('Label:Root')
    expect(wrapper.find('.action-slot').exists()).toBe(true)
  })

  it('renders row container for interaction styles', () => {
    const wrapper = mount(Tree, { props: { items: sampleTree } })
    expect(wrapper.find('.tree-node-content').exists()).toBe(true)
  })

  it('applies shared framed style when frameStyle is framed', () => {
    const wrapper = mount(Tree, { props: { items: sampleTree, frameStyle: 'framed' } })
    expect(wrapper.find('.tree').classes()).toContain('tree-frame-framed')
  })

  it('applies shared well style when frameStyle is well', () => {
    const wrapper = mount(Tree, { props: { items: sampleTree, frameStyle: 'well' } })
    expect(wrapper.find('.tree').classes()).toContain('tree-frame-well')
  })

  it('applies compact variant class when variant is compact', () => {
    const wrapper = mount(Tree, { props: { items: sampleTree, variant: 'compact' } })
    expect(wrapper.find('.tree').classes()).toContain('tree-variant-compact')
  })

  it('emits escape when Escape key is pressed within the tree', async () => {
    const wrapper = mount(Tree, { props: { items: sampleTree } })
    await wrapper.find('[role="tree"]').trigger('keydown', { key: 'Escape' })
    expect(wrapper.emitted('escape')).toHaveLength(1)
  })

  it('focuses selected item by default', () => {
    const wrapper = mount(Tree, {
      attachTo: document.body,
      props: {
        items: sampleTreeMultiRoot,
        modelValue: sampleTreeMultiRoot[1],
      },
    })
    ;(wrapper.vm as unknown as { focusTree: (options?: { target?: 'selected' | 'first' }) => void }).focusTree()
    const treeItems = wrapper.findAll('[role="treeitem"]')
    expect(document.activeElement).toBe(treeItems[1]?.element ?? null)
    wrapper.unmount()
  })

  it('focuses first item when requested', () => {
    const wrapper = mount(Tree, {
      attachTo: document.body,
      props: {
        items: sampleTreeMultiRoot,
        modelValue: sampleTreeMultiRoot[1],
      },
    })
    ;(wrapper.vm as unknown as { focusTree: (options?: { target?: 'selected' | 'first' }) => void }).focusTree({ target: 'first' })
    const treeItems = wrapper.findAll('[role="treeitem"]')
    expect(document.activeElement).toBe(treeItems[0]?.element ?? null)
    wrapper.unmount()
  })

  it('auto-focuses first item on mount when enabled', async () => {
    const wrapper = mount(Tree, {
      attachTo: document.body,
      props: {
        items: sampleTreeMultiRoot,
        autoFocusOnMount: true,
        autoFocusTarget: 'first',
      },
    })
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const treeItems = wrapper.findAll('[role="treeitem"]')
    expect(document.activeElement).toBe(treeItems[0]?.element ?? null)
    wrapper.unmount()
  })

  it('auto-focuses when items become available and enabled', async () => {
    const wrapper = mount(Tree, {
      attachTo: document.body,
      props: {
        items: [],
        autoFocusOnItemsChange: true,
        autoFocusTarget: 'first',
      },
    })
    await wrapper.setProps({ items: sampleTreeMultiRoot })
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const treeItems = wrapper.findAll('[role="treeitem"]')
    expect(document.activeElement).toBe(treeItems[0]?.element ?? null)
    wrapper.unmount()
  })

  it('auto-focuses when non-empty items are replaced and enabled', async () => {
    const wrapper = mount(Tree, {
      attachTo: document.body,
      props: {
        items: sampleTreeMultiRoot,
        autoFocusOnItemsChange: true,
        autoFocusTarget: 'first',
      },
    })
    document.body.focus()
    await wrapper.setProps({
      items: [
        { id: 'third', label: 'Third' },
        { id: 'fourth', label: 'Fourth' },
      ],
    })
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const treeItems = wrapper.findAll('[role="treeitem"]')
    expect(document.activeElement).toBe(treeItems[0]?.element ?? null)
    wrapper.unmount()
  })

  it('generates unique DOM ids for root nodes without ids', () => {
    const wrapper = mount(Tree, {
      props: {
        items: sampleTreeWithoutIds,
      },
    })

    const ids = wrapper.findAll('[role="treeitem"]').map(node => node.attributes('id'))
    expect(ids).toHaveLength(2)
    expect(ids[0]).toBeDefined()
    expect(ids[1]).toBeDefined()
    expect(ids[0]).not.toBe(ids[1])
  })

  it('generates unique DOM ids when custom getKey returns empty strings', () => {
    const wrapper = mount(Tree, {
      props: {
        items: sampleTreeWithoutIds,
        getKey: () => '',
      },
    })

    const ids = wrapper.findAll('[role="treeitem"]').map(node => node.attributes('id'))
    expect(ids).toHaveLength(2)
    expect(ids[0]).toBeDefined()
    expect(ids[1]).toBeDefined()
    expect(ids[0]).not.toBe(ids[1])
  })

  it('keeps root rendering stable when custom getKey returns empty strings', async () => {
    const first = { label: 'First' }
    const second = { label: 'Second' }
    const wrapper = mount(Tree, {
      props: {
        items: [first, second],
        getKey: () => '',
      },
    })

    let labels = wrapper.findAll('.tree-node-label').map(node => node.text())
    expect(labels).toEqual(['First', 'Second'])

    await wrapper.setProps({ items: [second, first] })
    labels = wrapper.findAll('.tree-node-label').map(node => node.text())
    expect(labels).toEqual(['Second', 'First'])
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { createI18nMock } from '@/shared/i18n'
import { encodeBase64 } from '@/shared/encoding/base64'
import App from './App.vue'

const mockGetFilesystemContents = vi.fn()
const mockOpenFilesystemDownload = vi.fn()

vi.mock('@/shared/http', () => ({
  getFilesystemContents: (...args: unknown[]) => mockGetFilesystemContents(...args),
  openFilesystemDownload: (...args: unknown[]) => mockOpenFilesystemDownload(...args),
}))

const TreeViewStub = defineComponent({
  name: 'TreeView',
  props: {
    items: {
      type: Array,
      default: () => [],
    },
    autoFocusOnItemsChange: {
      type: Boolean,
      default: false,
    },
    autoFocusTarget: {
      type: String,
      default: undefined,
    },
  },
  setup(props, { slots }) {
    return () =>
      h('div', { 'data-testid': 'tree-view' }, [
        slots.icon?.({
          node: (props.items as unknown[])[0],
          isExpanded: false,
          isFocused: false,
        }),
      ])
  },
})

const i18n = createI18nMock()

const mountBrowser = (directory = '/var/aip') =>
  mount(App, {
    props: { directory },
    global: {
      plugins: [i18n],
      stubs: {
        TreeView: TreeViewStub,
      },
    },
  })

describe('AipBrowser', () => {
  beforeEach(() => {
    mockGetFilesystemContents.mockReset()
    mockOpenFilesystemDownload.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads the directory contents and configures shared tree autofocus', async () => {
    mockGetFilesystemContents.mockResolvedValueOnce({
      name: encodeBase64('root'),
      children: [
        { name: encodeBase64('folder'), children: [] },
        { name: encodeBase64('file.txt') },
      ],
    })

    const wrapper = mountBrowser('/var/aip')

    await flushPromises()
    await nextTick()

    expect(mockGetFilesystemContents).toHaveBeenCalledWith(
      '/var/aip',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )

    const tree = wrapper.findComponent(TreeViewStub)
    expect(tree.exists()).toBe(true)
    expect(tree.props('autoFocusOnItemsChange')).toBe(true)
    expect(tree.props('autoFocusTarget')).toBe('first')

    const items = tree.props('items') as Array<{ label?: string, children?: Array<{ label?: string }> }>
    const rootNode = items[0]
    if (!rootNode) {
      throw new Error('Expected root tree node')
    }
    expect(rootNode.label).toBe('aip')
    expect(rootNode.children?.map(child => child.label)).toEqual(['folder', 'file.txt'])
  })

  it('downloads files when a leaf node is selected', async () => {
    mockGetFilesystemContents.mockResolvedValueOnce({
      name: encodeBase64('root'),
      children: [],
    })

    const wrapper = mountBrowser('/var/aip')
    await flushPromises()

    const tree = wrapper.findComponent(TreeViewStub)
    tree.vm.$emit('select', { path: '/var/aip/file.txt' })

    expect(mockOpenFilesystemDownload).toHaveBeenCalledWith(
      encodeBase64('/var/aip/file.txt'),
    )
  })

  it('does not download when an empty directory is selected', async () => {
    mockGetFilesystemContents.mockResolvedValueOnce({
      name: encodeBase64('root'),
      children: [],
    })

    const wrapper = mountBrowser('/var/aip')
    await flushPromises()

    const tree = wrapper.findComponent(TreeViewStub)
    tree.vm.$emit('select', { path: '/var/aip/empty-dir', children: [] })

    expect(mockOpenFilesystemDownload).not.toHaveBeenCalled()
  })

  it('shows a message when no directory is provided', async () => {
    const wrapper = mountBrowser('')

    await flushPromises()

    const alert = wrapper.find('.alert-danger')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('Failed to load AIP contents')
    expect(alert.text()).toContain('No directory provided for AIP browser.')
  })

  it('retries loading after a failure', async () => {
    mockGetFilesystemContents
      .mockRejectedValueOnce(new Error('Load failed'))
      .mockResolvedValueOnce({ name: encodeBase64('root'), children: [] })

    const wrapper = mountBrowser('/var/aip')
    await flushPromises()

    const alert = wrapper.find('.alert-danger')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('Load failed')

    const retryButton = wrapper.find('button')
    await retryButton.trigger('click')
    await flushPromises()

    expect(mockGetFilesystemContents).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.alert-danger').exists()).toBe(false)
    const tree = wrapper.findComponent(TreeViewStub)
    expect(tree.exists()).toBe(true)
    expect(tree.props('autoFocusOnItemsChange')).toBe(true)
    expect(tree.props('autoFocusTarget')).toBe('first')
  })

  it('shows the spinner only after the delay while loading', async () => {
    vi.useFakeTimers()
    mockGetFilesystemContents.mockReturnValue(new Promise(() => {}))

    const wrapper = mountBrowser('/var/aip')

    expect(wrapper.find('.fa-spinner').exists()).toBe(false)

    await vi.advanceTimersByTimeAsync(200)
    await nextTick()

    expect(wrapper.find('.fa-spinner').exists()).toBe(true)

    wrapper.unmount()
  })
})

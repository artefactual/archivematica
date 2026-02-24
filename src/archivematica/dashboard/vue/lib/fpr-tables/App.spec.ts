import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import App from './App.vue'

const i18n = createI18nMock()
const waitForSearchDebounce = (ms = 120) => new Promise(resolve => setTimeout(resolve, ms))

const makeRows = (count: number) =>
  Array.from({ length: count }, (_, index) => ({
    id: String(index + 1),
    description: `Format ${index + 1}`,
    formatSlug: `format-${index + 1}`,
    groupName: index % 2 === 0 ? 'Documents' : 'Images',
    actions: [{ key: 'view' as const, style: 'default' as const }],
  }))

const makePayload = (rowCount = 12) => ({
  version: 1,
  kind: 'format-list' as const,
  columns: [
    { key: 'description' },
    { key: 'groupName' },
    { key: 'actions', sortable: false },
  ],
  rows: makeRows(rowCount),
  ui: {
    create: {
      style: 'primary' as const,
    },
  },
})

describe('FprTables App', () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn()
  })

  it('renders paginated rows and pager info', () => {
    const wrapper = mount(App, {
      props: { payload: makePayload(12) },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.text()).toContain('Create new format')
    expect(wrapper.text()).toContain('Showing 1 to 10 of 12 entries')
    expect(wrapper.text()).toContain('Format 1')
    expect(wrapper.text()).toContain('Format 10')
    expect(wrapper.text()).not.toContain('Format 11')
  })

  it('moves to next page and scrolls table top into view', async () => {
    const wrapper = mount(App, {
      props: { payload: makePayload(12) },
      global: {
        plugins: [i18n],
      },
    })

    const nextButton = wrapper.findAll('.fpr-pagination-list button').find(button => button.text() === 'Next')
    expect(nextButton).toBeTruthy()

    await nextButton!.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Showing 11 to 12 of 12 entries')
    expect(wrapper.text()).toContain('Format 11')
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
  })

  it('filters rows and updates pagination info', async () => {
    const wrapper = mount(App, {
      props: { payload: makePayload(12) },
      global: {
        plugins: [i18n],
      },
    })

    await wrapper.find('input[type="search"]').setValue('Format 12')
    await waitForSearchDebounce()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain(
      'Showing 1 to 1 of 1 entries (filtered from 12 total entries)',
    )
    const bodyText = wrapper.find('tbody').text()
    expect(bodyText).toContain('Format 12')
    expect(bodyText).not.toContain('Format 11')
  })

  it('shows a no-match message when search filters all rows out', async () => {
    const wrapper = mount(App, {
      props: { payload: makePayload(12) },
      global: {
        plugins: [i18n],
      },
    })

    await wrapper.find('input[type="search"]').setValue('does-not-exist')
    await waitForSearchDebounce()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('No matching records found.')
    expect(wrapper.find('table').exists()).toBe(false)
  })

  it('shows the table empty message when payload has no rows', () => {
    const wrapper = mount(App, {
      props: { payload: makePayload(0) },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.text()).toContain('No formats exist.')
  })

  it('renders code-based values with Vue i18n labels', () => {
    const wrapper = mount(App, {
      props: {
        payload: {
          version: 1,
          kind: 'fprule-list',
          columns: [
            { key: 'purpose' },
            { key: 'format' },
            { key: 'command' },
            { key: 'success' },
            { key: 'enabled' },
            { key: 'actions', sortable: false },
          ],
          rows: [
            {
              id: 'rule-1',
              purpose: 'validation',
              format: 'TIFF',
              formatSlug: 'tiff',
              formatVersion: '6.0',
              formatPronomId: 'fmt/353',
              command: 'Validate TIFF',
              success: '3/5',
              successOkay: 3,
              successAttempts: 5,
              enabled: true,
              actions: [{ key: 'view' as const, style: 'default' as const }],
            },
          ],
          ui: { create: null },
        },
      },
      global: {
        plugins: [i18n],
      },
    })

    const text = wrapper.text()
    expect(text).toContain('Validation')
    expect(text).toContain('TIFF (version: 6.0, fmt/353)')
    expect(text).toContain('3 out of 5')
  })
})

import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import ResultsPagination from './ResultsPagination.vue'

const i18n = createI18nMock()

describe('ResultsPagination', () => {
  it('renders page-number mode and emits navigation/page-size events', async () => {
    const wrapper = mount(ResultsPagination, {
      props: {
        pageIndex: 0,
        pageCount: 4,
        pageSize: 10,
        pageSizeOptions: [10, 25, 50],
        canPreviousPage: false,
        canNextPage: true,
        startRow: 1,
        endRow: 10,
        filteredCount: 32,
        totalCount: 32,
        controlMode: 'pages',
      },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.text()).toContain('Showing 1 to 10 of 32 entries')
    expect(wrapper.find('.fpr-pagination-length select').exists()).toBe(true)
    expect(wrapper.find('.fpr-pagination-list').exists()).toBe(true)

    const pageTwoButton = wrapper.findAll('.fpr-pagination-list button').find(button => button.text() === '2')
    expect(pageTwoButton).toBeTruthy()
    await pageTwoButton!.trigger('click')
    expect(wrapper.emitted('setPageIndex')).toEqual([[1]])

    await wrapper.find('select').setValue('25')
    expect(wrapper.emitted('setPageSize')).toEqual([[25]])
  })

  it('renders edge mode and emits first/last/prev/next/page-size events', async () => {
    const wrapper = mount(ResultsPagination, {
      props: {
        pageIndex: 1,
        pageCount: 3,
        pageSize: 10,
        pageSizeOptions: [10, 25, 50],
        canPreviousPage: true,
        canNextPage: true,
        startRow: 11,
        endRow: 20,
        filteredCount: 25,
        totalCount: 25,
        controlMode: 'edges',
        infoStyle: 'chip',
        pageSizeLabelMode: 'show',
      },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.find('.pagination-row').exists()).toBe(true)
    expect(wrapper.text()).toContain('Page 2 of 3')
    expect(wrapper.text()).toContain('Showing 11 to 20 of 25 entries')

    const buttons = wrapper.findAll('.pagination-row button')
    const firstButton = buttons[0]
    const previousButton = buttons[1]
    const nextButton = buttons[2]
    const lastButton = buttons[3]
    if (!firstButton || !previousButton || !nextButton || !lastButton) {
      throw new Error('Expected all pagination buttons')
    }

    await firstButton.trigger('click')
    await previousButton.trigger('click')
    await nextButton.trigger('click')
    await lastButton.trigger('click')

    expect(wrapper.emitted('firstPage')).toHaveLength(1)
    expect(wrapper.emitted('previousPage')).toHaveLength(1)
    expect(wrapper.emitted('nextPage')).toHaveLength(1)
    expect(wrapper.emitted('lastPage')).toHaveLength(1)

    await wrapper.find('select').setValue('25')
    expect(wrapper.emitted('setPageSize')).toEqual([[25]])
  })
})

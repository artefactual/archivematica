import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import TablePagination from './TablePagination.vue'

const i18n = createI18nMock()

const baseProps = {
  pageIndex: 0,
  pageCount: 4,
  pageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],
  canPreviousPage: false,
  canNextPage: true,
  startRow: 1,
  endRow: 10,
  filteredCount: 32,
}

describe('TablePagination', () => {
  it('renders info, size selector, and page links', () => {
    const wrapper = mount(TablePagination, {
      props: baseProps,
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.text()).toContain('Showing 1 to 10 of 32 entries')
    expect(wrapper.find('.fpr-pagination-length select').exists()).toBe(true)
    expect(wrapper.find('.pagination').exists()).toBe(true)
    expect(wrapper.find('.pagination .active').text()).toContain('1')
  })

  it('emits page and page-size events', async () => {
    const wrapper = mount(TablePagination, {
      props: baseProps,
      global: {
        plugins: [i18n],
      },
    })

    const pageTwoButton = wrapper.findAll('.pagination button').find(button => button.text() === '2')
    expect(pageTwoButton).toBeTruthy()
    await pageTwoButton!.trigger('click')
    expect(wrapper.emitted('setPageIndex')).toEqual([[1]])

    await wrapper.find('select').setValue('25')
    expect(wrapper.emitted('setPageSize')).toEqual([[25]])
  })
})

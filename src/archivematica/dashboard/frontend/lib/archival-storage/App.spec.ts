import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import App from './App.vue'

const mockSearchArchivalStorage = vi.fn()
const mockLoadArchivalStorageState = vi.fn()
const mockSaveArchivalStorageState = vi.fn()
const mockOpenArchivalStorageCsv = vi.fn()

vi.mock('@/shared/http', () => ({
  createArchivalStorageAicUrl: vi.fn(() => '/archival-storage/search/create_aic/?'),
  createArchivalStorageAipFileDownloadUrl: vi.fn((fileUuid: string) => `/archival-storage/download/aip/file/${fileUuid}/`),
  createArchivalStorageAipUrl: vi.fn((uuid: string) => `/archival-storage/${uuid}/`),
  createArchivalStorageRawFileUrl: vi.fn((documentIdNoHyphens: string) => `/archival-storage/search/json/file/${documentIdNoHyphens}/`),
  createArchivalStorageThumbnailUrl: vi.fn((fileUuid: string) => `/archival-storage/thumbnail/${fileUuid}/`),
  openArchivalStorageCsv: (...args: unknown[]) => mockOpenArchivalStorageCsv(...args),
  searchArchivalStorage: (...args: unknown[]) => mockSearchArchivalStorage(...args),
  loadArchivalStorageState: (...args: unknown[]) => mockLoadArchivalStorageState(...args),
  saveArchivalStorageState: (...args: unknown[]) => mockSaveArchivalStorageState(...args),
}))

describe('ArchivalStorage App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.history.replaceState(null, '', '/archival-storage/')

    mockLoadArchivalStorageState.mockResolvedValue({ columns: [] })
    mockSaveArchivalStorageState.mockResolvedValue({ success: true })
    mockSearchArchivalStorage.mockResolvedValue({
      aaData: [
        {
          uuid: 'aip-uuid-1',
          name: 'AIP One',
          AICID: '',
          isPartOf: '',
        },
      ],
      iTotalRecords: 1,
    })
  })

  it('shows "Create an AIC" only after explicit search submission', async () => {
    const wrapper = mount(App, {
      props: {
        totalSize: '',
        filesIndexedCount: 0,
      },
      global: {
        plugins: [createI18nMock()],
      },
    })

    await flushPromises()
    const initialSearchCalls = mockSearchArchivalStorage.mock.calls.length
    expect(initialSearchCalls).toBeGreaterThanOrEqual(1)
    expect(wrapper.find('#create-aic-btn').exists()).toBe(false)

    await wrapper.find('#search_form').trigger('submit')
    await flushPromises()

    expect(mockSearchArchivalStorage.mock.calls.length).toBeGreaterThan(initialSearchCalls)
    expect(wrapper.find('#create-aic-btn').exists()).toBe(true)
  })
})

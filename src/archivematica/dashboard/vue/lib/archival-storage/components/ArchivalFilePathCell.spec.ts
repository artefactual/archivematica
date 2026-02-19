import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createI18nMock } from '@/shared/i18n'
import ArchivalFilePathCell from './ArchivalFilePathCell.vue'

describe('ArchivalFilePathCell', () => {
  it('renders en template as path + linked "view raw"', () => {
    const wrapper = mount(ArchivalFilePathCell, {
      props: {
        path: 'objects/foo.txt',
        rawUrl: '/raw/foo.txt',
      },
      global: {
        plugins: [createI18nMock()],
      },
    })

    expect(wrapper.text()).toContain('objects/foo.txt (view raw)')
    const link = wrapper.find('a')
    expect(link.exists()).toBe(true)
    expect(link.text()).toBe('view raw')
    expect(link.attributes('href')).toBe('/raw/foo.txt')
  })

  it('respects locale-controlled order and punctuation', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'xx',
      fallbackLocale: 'xx',
      messages: {
        xx: {
          archivalStorage: {
            filePathWithRawTemplate: '{link}: {path}',
            viewRaw: 'raw link',
          },
        },
      },
    })

    const wrapper = mount(ArchivalFilePathCell, {
      props: {
        path: 'objects/foo.txt',
        rawUrl: '/raw/foo.txt',
      },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.text()).toContain('raw link: objects/foo.txt')
  })
})

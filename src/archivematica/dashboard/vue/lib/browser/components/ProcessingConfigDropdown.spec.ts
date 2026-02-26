import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProcessingConfigDropdown from './ProcessingConfigDropdown.vue'

const defaultProps = {
  configs: [
    { pk: 'automated', name: 'automated' },
    { pk: 'default', name: 'default' },
  ],
  disabled: false,
  startLabel: 'Start transfer',
  submissionOptionsLabel: 'Transfer submission options',
  showConfigOptionsLabel: 'Show processing configuration options',
  startWithConfigLabel: (configName: string) => `Start with "${configName}" configuration`,
  defaultConfigName: 'default',
}

describe('ProcessingConfigDropdown', () => {
  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('shows and hides the menu when the caret toggle is clicked', async () => {
    const wrapper = mount(ProcessingConfigDropdown, {
      attachTo: document.body,
      props: defaultProps,
    })

    const root = wrapper.get('.dropdown')
    const toggle = wrapper.get('button.dropdown-toggle')
    const menu = wrapper.get('.dropdown-menu')

    expect(root.classes()).not.toContain('open')
    expect(menu.attributes('style')).toContain('display: none')

    await toggle.trigger('click')

    expect(root.classes()).toContain('open')
    expect(menu.attributes('style') ?? '').not.toContain('display: none')

    await toggle.trigger('click')

    expect(root.classes()).not.toContain('open')
    expect(menu.attributes('style')).toContain('display: none')

    wrapper.unmount()
  })

  it('stops click propagation so document-level dropdown handlers do not interfere', async () => {
    const documentClickSpy = vi.fn()
    document.addEventListener('click', documentClickSpy)

    const wrapper = mount(ProcessingConfigDropdown, {
      attachTo: document.body,
      props: defaultProps,
    })

    await wrapper.get('button.dropdown-toggle').trigger('click')

    expect(documentClickSpy).not.toHaveBeenCalled()
    expect(wrapper.get('.dropdown').classes()).toContain('open')

    wrapper.unmount()
    document.removeEventListener('click', documentClickSpy)
  })

  it('stops keydown propagation while preserving keyboard open behavior', async () => {
    const documentKeydownSpy = vi.fn()
    document.addEventListener('keydown', documentKeydownSpy)

    const wrapper = mount(ProcessingConfigDropdown, {
      attachTo: document.body,
      props: defaultProps,
    })

    await wrapper.get('button.dropdown-toggle').trigger('keydown', { key: 'ArrowDown' })

    expect(documentKeydownSpy).not.toHaveBeenCalled()
    expect(wrapper.get('.dropdown').classes()).toContain('open')
    expect(wrapper.get('.dropdown-menu').attributes('style') ?? '').not.toContain('display: none')

    wrapper.unmount()
    document.removeEventListener('keydown', documentKeydownSpy)
  })
})

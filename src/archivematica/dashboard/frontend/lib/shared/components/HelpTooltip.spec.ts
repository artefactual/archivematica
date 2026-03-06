import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import HelpTooltip from './HelpTooltip.vue'

const i18n = createI18nMock()
const rekaStubs = {
  TooltipProvider: { template: '<div class="tooltip-provider"><slot /></div>' },
  TooltipRoot: { template: '<div class="tooltip-root"><slot /></div>' },
  TooltipTrigger: { template: '<div class="tooltip-trigger"><slot /></div>' },
  TooltipPortal: { template: '<div class="tooltip-portal"><slot /></div>' },
  TooltipContent: { template: '<div class="tooltip-content"><slot /></div>' },
  TooltipArrow: { template: '<div class="tooltip-arrow" />' },
}

describe('HelpTooltip', () => {
  it('renders question mark trigger with default help aria label', () => {
    const wrapper = mount(HelpTooltip, {
      props: {
        content: 'Tooltip content',
      },
      global: {
        plugins: [i18n],
        stubs: rekaStubs,
      },
    })

    const trigger = wrapper.find('.help-tooltip-trigger')
    expect(trigger.exists()).toBe(true)
    expect(trigger.classes()).toContain('fa-question-circle')
    expect(trigger.attributes('aria-label')).toBe('Help')
  })

  it('renders tooltip content text', () => {
    const wrapper = mount(HelpTooltip, {
      props: {
        content: 'Create a SIP from the transfer.',
      },
      global: {
        plugins: [i18n],
        stubs: rekaStubs,
      },
    })

    expect(wrapper.text()).toContain('Create a SIP from the transfer.')
    expect(wrapper.find('.help-tooltip-content').exists()).toBe(true)
  })
})

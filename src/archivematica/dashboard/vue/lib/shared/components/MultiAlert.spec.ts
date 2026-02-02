import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import MultiAlert from './MultiAlert.vue'
import type { Alert } from './MultiAlert.vue'

const i18n = createI18nMock()

describe('MultiAlert', () => {
  const mockAlerts: Alert[] = [
    {
      id: '1',
      message: 'Operation successful',
      type: 'success',
    },
    {
      id: '2',
      message: 'Warning: Check your settings',
      type: 'warning',
    },
    {
      id: '3',
      message: 'Error occurred',
      type: 'danger',
      showSpinner: true,
    },
  ]

  it('renders all alerts', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const alertElements = wrapper.findAll('.alert')
    expect(alertElements).toHaveLength(3)

    const successAlert = alertElements[0]
    if (!successAlert) {
      throw new Error('Expected success alert element')
    }
    expect(successAlert.classes()).toContain('alert-success')

    const warningAlert = alertElements[1]
    if (!warningAlert) {
      throw new Error('Expected warning alert element')
    }
    expect(warningAlert.classes()).toContain('alert-warning')

    const dangerAlert = alertElements[2]
    if (!dangerAlert) {
      throw new Error('Expected danger alert element')
    }
    expect(dangerAlert.classes()).toContain('alert-danger')
  })

  it('displays alert messages correctly', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const alertElements = wrapper.findAll('.alert')

    const successAlert = alertElements[0]
    if (!successAlert) {
      throw new Error('Expected success alert element')
    }
    expect(successAlert.text()).toContain('Operation successful')

    const warningAlert = alertElements[1]
    if (!warningAlert) {
      throw new Error('Expected warning alert element')
    }
    expect(warningAlert.text()).toContain('Warning: Check your settings')

    const dangerAlert = alertElements[2]
    if (!dangerAlert) {
      throw new Error('Expected danger alert element')
    }
    expect(dangerAlert.text()).toContain('Error occurred')
  })

  it('renders spinner when showSpinner is true', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const spinners = wrapper.findAll('.fa-spinner')
    expect(spinners).toHaveLength(1)

    const spinner = spinners[0]
    if (!spinner) {
      throw new Error('Expected spinner element')
    }
    expect(spinner.classes()).toContain('fa-spin')
  })

  it('emits dismiss event when close button is clicked', async () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const closeButtons = wrapper.findAll('.close')
    const secondButton = closeButtons[1]
    if (!secondButton) {
      throw new Error('Expected second close button')
    }
    await secondButton.trigger('click')

    const dismissEvents = wrapper.emitted('dismiss') ?? []
    expect(dismissEvents).toHaveLength(1)
    const firstDismiss = dismissEvents[0]
    if (!firstDismiss) {
      throw new Error('Expected dismiss payload')
    }
    expect(firstDismiss).toEqual(['2'])
  })

  it('emits dismiss event on Enter key', async () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const closeButtons = wrapper.findAll('.close')
    const firstButton = closeButtons[0]
    if (!firstButton) {
      throw new Error('Expected first close button')
    }
    await firstButton.trigger('keydown.enter')

    const dismissEvents = wrapper.emitted('dismiss') ?? []
    expect(dismissEvents).toHaveLength(1)
    const firstDismiss = dismissEvents[0]
    if (!firstDismiss) {
      throw new Error('Expected dismiss payload')
    }
    expect(firstDismiss).toEqual(['1'])
  })

  it('emits dismiss event on Space key', async () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const closeButtons = wrapper.findAll('.close')
    const thirdButton = closeButtons[2]
    if (!thirdButton) {
      throw new Error('Expected third close button')
    }
    await thirdButton.trigger('keydown.space')

    const dismissEvents = wrapper.emitted('dismiss') ?? []
    expect(dismissEvents).toHaveLength(1)
    const firstDismiss = dismissEvents[0]
    if (!firstDismiss) {
      throw new Error('Expected dismiss payload')
    }
    expect(firstDismiss).toEqual(['3'])
  })

  it('sets correct aria attributes', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const container = wrapper.find('.multi-alert')
    expect(container.attributes('role')).toBe('region')
    expect(container.attributes('aria-label')).toBe('Notifications')

    const alertElements = wrapper.findAll('.alert')

    // Success and warning alerts have polite aria-live
    const successAlert = alertElements[0]
    if (!successAlert) {
      throw new Error('Expected success alert element')
    }
    expect(successAlert.attributes('role')).toBe('alert')
    expect(successAlert.attributes('aria-live')).toBe('polite')

    const warningAlert = alertElements[1]
    if (!warningAlert) {
      throw new Error('Expected warning alert element')
    }
    expect(warningAlert.attributes('aria-live')).toBe('polite')

    // Danger alerts have assertive aria-live
    const dangerAlert = alertElements[2]
    if (!dangerAlert) {
      throw new Error('Expected danger alert element')
    }
    expect(dangerAlert.attributes('aria-live')).toBe('assertive')
  })

  it('sets correct aria-labels for close buttons', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const closeButtons = wrapper.findAll('.close')

    const firstButton = closeButtons[0]
    if (!firstButton) {
      throw new Error('Expected first close button')
    }
    expect(firstButton.attributes('aria-label')).toBe('Dismiss success alert: Operation successful')

    const secondButton = closeButtons[1]
    if (!secondButton) {
      throw new Error('Expected second close button')
    }
    expect(secondButton.attributes('aria-label')).toBe('Dismiss warning alert: Warning: Check your settings')

    const thirdButton = closeButtons[2]
    if (!thirdButton) {
      throw new Error('Expected third close button')
    }
    expect(thirdButton.attributes('aria-label')).toBe('Dismiss danger alert: Error occurred')
  })

  it('renders empty state correctly', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: [],
      },
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.findAll('.alert')).toHaveLength(0)
    expect(wrapper.find('.multi-alert').exists()).toBe(true)
  })

  it('renders info type alert correctly', () => {
    const infoAlert: Alert = {
      id: '4',
      message: 'Information message',
      type: 'info',
    }

    const wrapper = mount(MultiAlert, {
      props: {
        alerts: [infoAlert],
      },
      global: {
        plugins: [i18n],
      },
    })

    const alertElement = wrapper.find('.alert')
    expect(alertElement.classes()).toContain('alert-info')
    expect(alertElement.attributes('aria-live')).toBe('polite')
  })

  it('makes alerts focusable with tabindex', () => {
    const wrapper = mount(MultiAlert, {
      props: {
        alerts: mockAlerts,
      },
      global: {
        plugins: [i18n],
      },
    })

    const alertElements = wrapper.findAll('.alert')
    alertElements.forEach((alert) => {
      expect(alert.attributes('tabindex')).toBe('0')
    })
  })

  it('renders spinner with correct aria attributes', () => {
    const alertWithSpinner: Alert = {
      id: '5',
      message: 'Loading...',
      type: 'info',
      showSpinner: true,
    }

    const wrapper = mount(MultiAlert, {
      props: {
        alerts: [alertWithSpinner],
      },
      global: {
        plugins: [i18n],
      },
    })

    const spinnerContainer = wrapper.find('[role="status"]')
    expect(spinnerContainer.exists()).toBe(true)
    expect(spinnerContainer.attributes('aria-label')).toBe('Loading')

    const spinner = spinnerContainer.find('.fa-spinner')
    expect(spinner.attributes('aria-hidden')).toBe('true')
  })
})

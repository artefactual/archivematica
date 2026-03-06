import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import { createI18nMock } from '@/shared/i18n'
import MetadataSubmitStatus from './MetadataSubmitStatus.vue'

describe('MetadataSubmitStatus', () => {
  const mountStatus = (
    props: Partial<InstanceType<typeof MetadataSubmitStatus>['$props']> = {},
  ) =>
    mount(MetadataSubmitStatus, {
      props: {
        submitting: false,
        message: null,
        status: null,
        ...props,
      },
      global: {
        plugins: [createI18nMock()],
      },
    })

  it('shows spinner while submitting', () => {
    const wrapper = mountStatus({ submitting: true })

    expect(wrapper.find('.activity-indicator').exists()).toBe(true)
    expect(wrapper.find('.alert').exists()).toBe(false)
  })

  it('shows alert message with status class', () => {
    const wrapper = mountStatus({
      message: 'Uploaded',
      status: 'success',
    })

    const alert = wrapper.get('.alert')
    expect(alert.text()).toContain('Uploaded')
    expect(alert.classes()).toContain('alert-success')
  })

  it('emits dismiss when close is clicked', async () => {
    const wrapper = mountStatus({
      message: 'Failed',
      status: 'danger',
    })

    await wrapper.get('button.close').trigger('click')

    expect(wrapper.emitted('dismiss')).toHaveLength(1)
  })
})

import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import { createI18nMock } from '@/shared/i18n'
import MetadataSourceForm from './MetadataSourceForm.vue'

describe('MetadataSourceForm', () => {
  const locationOptions: [string, string][] = [
    ['loc1', '/home'],
    ['loc2', '/var'],
  ]

  const mountForm = (props: Partial<InstanceType<typeof MetadataSourceForm>['$props']> = {}) =>
    mount(MetadataSourceForm, {
      props: {
        modelValue: 'loc1',
        locationOptions,
        submitting: false,
        ...props,
      },
      global: {
        plugins: [createI18nMock()],
      },
    })

  it('renders location options', () => {
    const wrapper = mountForm()
    const options = wrapper.findAll('option')

    expect(options).toHaveLength(2)
    expect(options[0]?.text()).toBe('/home')
    expect(options[1]?.text()).toBe('/var')
  })

  it('emits model updates when location changes', async () => {
    const wrapper = mountForm()

    await wrapper.get('#metadata-source-select').setValue('loc2')

    expect(wrapper.emitted('update:modelValue')).toEqual([['loc2']])
  })

  it('emits browse and submit events', async () => {
    const wrapper = mountForm()

    await wrapper.get('button.btn.btn-default').trigger('click')
    await wrapper.get('button.btn.btn-success').trigger('click')

    expect(wrapper.emitted('browse')).toHaveLength(1)
    expect(wrapper.emitted('submit')).toHaveLength(1)
  })
})

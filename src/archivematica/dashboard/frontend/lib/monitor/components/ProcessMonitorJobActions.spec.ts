import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import type { ProcessingJob } from '@/shared/http/processing'
import ProcessMonitorJobActions from './ProcessMonitorJobActions.vue'

const mountActions = (job: Partial<ProcessingJob> = {}) => mount(ProcessMonitorJobActions, {
  props: {
    job: {
      uuid: 'newest-job',
      link_id: 'workflow-link',
      type: 'Normalize for preservation',
      microservicegroup: 'Normalize',
      currentstep: 2,
      timestamp: 1,
      produces_tasks: true,
      ...job,
    },
    unitUuid: 'sip-uuid',
    selectedChoice: '',
    isExecutingChoice: false,
  },
  global: { plugins: [createI18nMock()] },
})

describe('ProcessMonitorJobActions history navigation', () => {
  it('opens explicitly labelled Job history for a repeated task-producing Job', async () => {
    const wrapper = mountActions({ count: 14000 })
    const action = wrapper.get('.btn_show_tasks')

    expect(action.attributes('title')).toBe('Job history')
    expect(action.attributes('aria-label')).toBe('Job history')
    await action.trigger('click')

    expect(wrapper.emitted('show-job-history')).toEqual([[{
      unitUuid: 'sip-uuid',
      linkId: 'workflow-link',
    }]])
    expect(wrapper.emitted('show-tasks')).toBeUndefined()
    wrapper.unmount()
  })

  it.each([undefined, 1])('opens Tasks directly when the Job count is %s', async (count) => {
    const wrapper = mountActions({ count })
    const action = wrapper.get('.btn_show_tasks')

    expect(action.attributes('title')).toBe('Tasks')
    await action.trigger('click')

    expect(wrapper.emitted('show-tasks')).toEqual([['newest-job']])
    expect(wrapper.emitted('show-job-history')).toBeUndefined()
    wrapper.unmount()
  })

  it('preserves the Tasks target for legacy rows without a workflow link', async () => {
    const wrapper = mountActions({ count: 2, link_id: undefined })

    await wrapper.get('.btn_show_tasks').trigger('click')

    expect(wrapper.emitted('show-tasks')).toEqual([['newest-job']])
    expect(wrapper.emitted('show-job-history')).toBeUndefined()
    wrapper.unmount()
  })

  it('does not add task actions to Jobs that do not produce Tasks', () => {
    const wrapper = mountActions({ count: 2, produces_tasks: false })

    expect(wrapper.find('.btn_show_tasks').exists()).toBe(false)
    wrapper.unmount()
  })
})

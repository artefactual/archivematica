import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import ProcessMonitor from './ProcessMonitor.vue'
import ProcessMonitorUnit from './ProcessMonitorUnit.vue'

vi.mock('@/shared/http/transfer', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http/transfer')>('@/shared/http/transfer')
  return {
    ...actual,
    getTransferSummaries: vi.fn(),
  }
})

vi.mock('@/shared/http/ingest', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http/ingest')>('@/shared/http/ingest')
  return {
    ...actual,
    getIngestSummaries: vi.fn(),
  }
})

vi.mock('@/shared/http', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http')>('@/shared/http')
  return {
    ...actual,
    deleteUnit: vi.fn(),
    executeChoice: vi.fn(),
    getIngestUploadAsUrl: vi.fn(actual.getIngestUploadAsUrl),
    getIngestJobGroups: vi.fn(),
    getTransferJobGroups: vi.fn(),
    getUploadTarget: vi.fn(),
    setUploadTarget: vi.fn(),
  }
})

import { getTransferSummaries } from '@/shared/http/transfer'
import { getIngestSummaries } from '@/shared/http/ingest'
import {
  deleteUnit,
  executeChoice,
  getIngestJobGroups,
  getIngestUploadAsUrl,
  getTransferJobGroups,
  getUploadTarget,
  setUploadTarget,
} from '@/shared/http'
import { PROCESSING_UNIT_STATE } from '@/shared/http/processing'
import type { MonitorConfig } from '@/monitor/composables'
import { SilkTableEditIcon } from '@/shared/icons'

type PermissiveAsyncMock = {
  mockReset: () => void
  mockResolvedValue: (value: unknown) => void
  mockResolvedValueOnce: (value: unknown) => void
}

// Most component cases intentionally retain the legacy eager payload. This
// verifies that the UI refactor does not break embedded callers while focused
// cases below exercise the new summary and lazy job-group contracts.
const transferSummariesMock = vi.mocked(getTransferSummaries) as unknown as PermissiveAsyncMock
const ingestSummariesMock = vi.mocked(getIngestSummaries) as unknown as PermissiveAsyncMock

const i18n = createI18nMock()

const defaultConfig: MonitorConfig = {
  polling_interval: 10,
  microservices_help: {},
  job_statuses: {
    0: 'Unknown',
    1: 'Awaiting decision',
    2: 'Completed successfully',
    3: 'Executing command(s)',
    4: 'Failed',
  },
}

const createDeferred = <T>() => {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise
  })
  return { promise, resolve }
}

describe('ProcessMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
    vi.mocked(getTransferJobGroups).mockResolvedValue({ results: [] })
    vi.mocked(getIngestJobGroups).mockResolvedValue({ results: [] })
  })

  it('fetches transfer statuses when unitType is Transfer', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [{ uuid: 't-1', directory: 'Transfer-1', timestamp: 1, jobs: [] }],
      mcp: true,
    })
    ingestSummariesMock.mockResolvedValueOnce({ objects: [], mcp: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getTransferSummaries).toHaveBeenCalledTimes(1)
    expect(getIngestSummaries).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Transfer-1')
  })

  it('loads aggregated jobs only after a summary row is expanded', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 2,
          started_at: 1,
          status: {
            currentstep: 2,
            type: 'Latest job',
            microservicegroup: 'Group A',
          },
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })
    vi.mocked(getTransferJobGroups).mockResolvedValueOnce({
      results: [{
        name: 'Group A',
        jobs: [{
          key: 'link-1:2',
          uuid: 'j-aggregated',
          link_id: 'link-1',
          type: 'Repeated job',
          microservicegroup: 'Group A',
          currentstep: 2,
          timestamp: 2,
          first_timestamp: 1,
          count: 14000,
          produces_tasks: false,
        }],
      }],
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    expect(getTransferJobGroups).not.toHaveBeenCalled()
    expect(wrapper.text()).not.toContain('Repeated job')

    await wrapper.get('.sip-detail-directory').trigger('click')
    await flushPromises()

    expect(getTransferJobGroups).toHaveBeenCalledExactlyOnceWith('t-1')

    await wrapper.get('.microservice-group').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Repeated job')
    expect(wrapper.text()).toContain('14,000')
    expect(wrapper.get('.job-detail-microservice span[title]').text()).toBe('Repeated job')
    expect(wrapper.get('.job-count').text()).toBe('× 14,000')
  })

  it('keeps the metadata edit icon when a unit is collapsed or expanded', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 1,
          started_at: 1,
          status: null,
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    expect(wrapper.findComponent(SilkTableEditIcon).exists()).toBe(true)

    await wrapper.get('.sip-detail-directory').trigger('click')
    await flushPromises()

    expect(wrapper.findComponent(SilkTableEditIcon).exists()).toBe(true)
  })

  it('shows a waiting icon for jobless transfers waiting to start', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-queued"}]}',
      data: {
        results: [{
          uuid: 't-queued',
          directory: 'Transfer-queued',
          timestamp: 0,
          started_at: 0,
          processing_state: PROCESSING_UNIT_STATE.waitingForProcessing,
          active: true,
          status: null,
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })
    ingestSummariesMock.mockResolvedValueOnce({ objects: [], mcp: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(
      wrapper.find('.sip-detail-icon-status .monitor-status-icon-hourglass').exists(),
    ).toBe(true)
    expect(
      wrapper.find('.sip-detail-icon-status .monitor-status-icon-accept').exists(),
    ).toBe(false)
    expect(
      wrapper.find('.sip-detail-icon-status .monitor-status-icon-arrow-refresh').exists(),
    ).toBe(false)
    expect(wrapper.get('.monitor-status-label').text()).toBe('Waiting for processing')
    expect(wrapper.get('.sip').classes()).not.toContain('sip-expandable')

    const unitExpander = wrapper.get('.sip-detail-directory')
    expect(unitExpander.attributes('role')).toBeUndefined()
    expect(unitExpander.attributes('tabindex')).toBeUndefined()
    expect(unitExpander.attributes('aria-expanded')).toBeUndefined()
    expect(unitExpander.attributes('aria-controls')).toBeUndefined()

    await wrapper.get('.sip-detail-icon-status').trigger('click')
    await unitExpander.trigger('keydown.enter')
    await wrapper.get('.sip-detail-actions').trigger('click')
    await flushPromises()

    expect(wrapper.get('.sip').classes()).not.toContain('sip-selected')
    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(false)
    expect(getTransferJobGroups).not.toHaveBeenCalled()

    expect(wrapper.find('.btn_show_metadata').exists()).toBe(true)
    expect(wrapper.find('.btn_remove_sip').exists()).toBe(false)
    expect(deleteUnit).not.toHaveBeenCalled()
    expect(getTransferJobGroups).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('fetches ingest statuses when unitType is SIP', async () => {
    ingestSummariesMock.mockResolvedValueOnce({
      objects: [{ uuid: 's-1', directory: 'SIP-1', timestamp: 1, jobs: [] }],
      mcp: true,
    })
    transferSummariesMock.mockResolvedValueOnce({ objects: [], mcp: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getIngestSummaries).toHaveBeenCalledTimes(1)
    expect(getTransferSummaries).not.toHaveBeenCalled()
    expect(wrapper.find('#sip-units').exists()).toBe(true)
  })

  it('polls using polling_interval from transfer monitor config', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValue({
      objects: [{ uuid: 't-1', directory: 'Transfer-1', timestamp: 1, jobs: [] }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: {
        unitType: 'Transfer',
        config: { ...defaultConfig, polling_interval: 1 },
      },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    expect(getTransferSummaries).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    await flushPromises()
    expect(getTransferSummaries).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })

  it('keeps current rows visible while polling refreshes', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValue({
      objects: [{ uuid: 't-1', directory: 'Transfer-1', timestamp: 1, jobs: [] }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: {
        unitType: 'Transfer',
        config: { ...defaultConfig, polling_interval: 1 },
      },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    expect(wrapper.find('#sip-loading').exists()).toBe(false)
    expect(wrapper.find('#sip-units').exists()).toBe(true)

    vi.advanceTimersByTime(1000)
    await flushPromises()

    expect(wrapper.find('#sip-loading').exists()).toBe(false)
    expect(wrapper.find('#sip-units').exists()).toBe(true)

    wrapper.unmount()
  })

  it('toggles job container when clicking non-action row areas', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 't-1',
        directory: 'Transfer-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Job 1',
          microservicegroup: 'Group A',
          currentstep: 2,
          timestamp: 1,
          produces_tasks: true,
        }],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(false)

    await wrapper.find('.sip-detail-icon-status').trigger('click')
    await flushPromises()

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(true)

    await wrapper.find('.sip-detail-actions').trigger('click')
    await flushPromises()

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(false)
    wrapper.unmount()
  })

  it('exposes keyboard-operable unit and group expanders', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 't-1',
        directory: 'Transfer-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Job 1',
          microservicegroup: 'Group A',
          currentstep: 2,
          timestamp: 1,
          produces_tasks: true,
        }],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    const unitExpander = wrapper.get('.sip-detail-directory')
    expect(unitExpander.attributes()).toMatchObject({
      'role': 'button',
      'tabindex': '0',
      'aria-expanded': 'false',
      'aria-controls': 'sip-jobs-t-1',
    })

    await unitExpander.trigger('keydown.enter')
    await wrapper.vm.$nextTick()

    expect(unitExpander.attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('#sip-jobs-t-1').exists()).toBe(true)

    const groupExpander = wrapper.get('.microservice-group')
    expect(groupExpander.attributes()).toMatchObject({
      'role': 'button',
      'tabindex': '0',
      'aria-expanded': 'false',
    })

    await groupExpander.trigger('keydown.space')
    await wrapper.vm.$nextTick()

    expect(groupExpander.attributes('aria-expanded')).toBe('true')
    const controlledId = groupExpander.attributes('aria-controls')
    expect(controlledId).toBeTruthy()
    expect(wrapper.find(`#${controlledId}`).exists()).toBe(true)
    wrapper.unmount()
  })

  it('does not toggle a unit when clicking its action controls', async () => {
    const unit = {
      uuid: 't-1',
      directory: 'Transfer-1',
      timestamp: 1,
      jobs: [],
    }
    const wrapper = mount(ProcessMonitorUnit, {
      props: {
        unit,
        isExpandable: true,
        isExpanded: false,
        isLoadingJobGroups: false,
        hasJobGroupsError: false,
        unitGroups: [],
        expandedGroupKeys: {},
        executingChoiceJobUuids: {},
        selectedChoicesByJobUuid: {},
        microservicesHelp: {},
        jobStatuses: {},
      },
      global: { plugins: [i18n] },
    })

    await wrapper.get('.btn_show_metadata').trigger('click')

    expect(wrapper.emitted('open-panel')).toEqual([['t-1']])
    expect(wrapper.emitted('toggle-unit')).toBeUndefined()

    await wrapper.get('.btn_remove_sip .monitor-action-icon').trigger('click')

    expect(wrapper.emitted('remove-unit')).toEqual([[unit]])
    expect(wrapper.emitted('toggle-unit')).toBeUndefined()
    wrapper.unmount()
  })

  it('keeps Metadata available while queued and restores removal after the waiting state ends', async () => {
    const wrapper = mount(ProcessMonitorUnit, {
      props: {
        unit: {
          uuid: 't-queued',
          directory: 'Transfer-queued',
          timestamp: 1,
          processing_state: 'waiting_for_processing',
          jobs: [],
        },
        isExpandable: false,
        isExpanded: false,
        isLoadingJobGroups: false,
        hasJobGroupsError: false,
        unitGroups: [],
        expandedGroupKeys: {},
        executingChoiceJobUuids: {},
        selectedChoicesByJobUuid: {},
        microservicesHelp: {},
        jobStatuses: {},
      },
      global: { plugins: [i18n] },
    })

    await wrapper.get('.btn_show_metadata').trigger('click')
    expect(wrapper.emitted('open-panel')).toEqual([['t-queued']])
    expect(wrapper.find('.btn_remove_sip').exists()).toBe(false)
    expect(wrapper.emitted('remove-unit')).toBeUndefined()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.get('.sip-detail-directory').trigger('keydown.enter')
    await wrapper.get('.sip-detail-directory').trigger('keydown.space')
    expect(wrapper.emitted('toggle-unit')).toBeUndefined()
    expect(wrapper.get('.sip-detail-directory').attributes('tabindex')).toBeUndefined()

    // A transfer can fail before its first Job. Zero Jobs alone must not
    // prevent removal once the transfer is no longer queued.
    await wrapper.setProps({
      isExpandable: true,
      unit: { ...wrapper.props('unit'), processing_state: undefined, active: false },
    })

    expect(wrapper.find('.btn_show_metadata').exists()).toBe(true)
    expect(wrapper.find('.btn_remove_sip').exists()).toBe(true)
    await wrapper.get('.btn_remove_sip').trigger('click')
    expect(wrapper.emitted('remove-unit')).toEqual([[wrapper.props('unit')]])
    await wrapper.get('.sip-detail-directory').trigger('keydown.enter')
    expect(wrapper.emitted('toggle-unit')).toEqual([[wrapper.props('unit')]])
    wrapper.unmount()
  })

  it('keeps a legacy unit awaiting decision collapsed', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 't-1',
        directory: 'Transfer-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Job 1',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          produces_tasks: true,
        }],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(false)
    expect(
      wrapper.find('.sip-detail-icon-status .monitor-status-icon-bell').exists(),
    ).toBe(true)
    wrapper.unmount()
  })

  it('loads decision jobs after the user expands a pending unit', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 1,
          started_at: 1,
          status: {
            currentstep: 1,
            type: 'Awaiting job',
            microservicegroup: 'Group A',
          },
          has_awaiting_decision: true,
          awaiting_job_uuids: ['j-1'],
        }],
      },
    })
    vi.mocked(getTransferJobGroups).mockResolvedValueOnce({
      results: [{
        name: 'Group A',
        jobs: [{
          key: 'job:j-1',
          uuid: 'j-1',
          link_id: 'link-1',
          type: 'Awaiting job',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          count: 1,
          produces_tasks: false,
          choices: { approve: 'Approve' },
        }],
      }],
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    expect(getTransferJobGroups).not.toHaveBeenCalled()
    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(false)
    expect(
      wrapper.find('.sip-detail-icon-status .monitor-status-icon-bell').exists(),
    ).toBe(true)

    await wrapper.get('.sip-detail-directory').trigger('click')
    await flushPromises()

    expect(getTransferJobGroups).toHaveBeenCalledExactlyOnceWith('t-1')
    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(true)
    expect(wrapper.text()).toContain('Awaiting job')
    expect(wrapper.find('option[value="approve"]').exists()).toBe(true)
  })

  it('keeps multiple units awaiting decisions collapsed', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"},{"uuid":"t-2"}]}',
      data: {
        results: [
          {
            uuid: 't-1',
            directory: 'Transfer-1',
            timestamp: 2,
            started_at: 1,
            status: null,
            has_awaiting_decision: true,
            awaiting_job_uuids: ['j-1'],
          },
          {
            uuid: 't-2',
            directory: 'Transfer-2',
            timestamp: 1,
            started_at: 1,
            status: null,
            has_awaiting_decision: true,
            awaiting_job_uuids: ['j-1'],
          },
        ],
      },
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    expect(wrapper.findAll('.sip-expanded')).toHaveLength(0)
    expect(getTransferJobGroups).not.toHaveBeenCalled()
    expect(
      wrapper.findAll('.sip-detail-icon-status .monitor-status-icon-bell'),
    ).toHaveLength(2)
  })

  it('refreshes expanded job groups after an unchanged summary poll', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 1,
          started_at: 1,
          status: null,
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })
    transferSummariesMock.mockResolvedValueOnce({
      changed: false,
      raw: '{"results":[{"uuid":"t-1"}]}',
    })

    const wrapper = mount(ProcessMonitor, {
      props: {
        unitType: 'Transfer',
        config: { ...defaultConfig, polling_interval: 1 },
      },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    await wrapper.get('.sip-detail-directory').trigger('click')
    await flushPromises()
    expect(getTransferJobGroups).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    await flushPromises()
    expect(getTransferJobGroups).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })

  it('shows an accessible loading state while lazy job groups are pending', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 1,
          started_at: 1,
          status: null,
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })
    const jobGroups = createDeferred<Awaited<ReturnType<typeof getTransferJobGroups>>>()
    vi.mocked(getTransferJobGroups).mockImplementationOnce(() => jobGroups.promise)

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()

    const container = wrapper.get('.sip-detail-job-container')
    expect(container.attributes('aria-busy')).toBe('true')
    expect(container.get('[role="status"]').text()).toBe('Loading...')

    jobGroups.resolve({ results: [] })
    await flushPromises()

    expect(container.attributes('aria-busy')).toBe('false')
    expect(container.find('[role="status"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('retains stale job history without choices when a newer summary arrives', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1","timestamp":1}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 1,
          started_at: 1,
          status: null,
          has_awaiting_decision: true,
          awaiting_job_uuids: ['j-1'],
        }],
      },
    })
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1","timestamp":2}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 2,
          started_at: 1,
          status: null,
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })
    transferSummariesMock.mockResolvedValueOnce({
      changed: false,
      raw: '{"results":[{"uuid":"t-1","timestamp":2}]}',
    })
    const staleGroups = createDeferred<Awaited<ReturnType<typeof getTransferJobGroups>>>()
    const currentGroups = createDeferred<Awaited<ReturnType<typeof getTransferJobGroups>>>()
    vi.mocked(getTransferJobGroups)
      .mockImplementationOnce(() => staleGroups.promise)
      .mockImplementationOnce(() => currentGroups.promise)

    const wrapper = mount(ProcessMonitor, {
      props: {
        unitType: 'Transfer',
        config: { ...defaultConfig, polling_interval: 1 },
      },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    expect(getTransferJobGroups).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    await flushPromises()

    staleGroups.resolve({
      results: [{
        name: 'Group A',
        jobs: [{
          key: 'job:j-stale',
          uuid: 'j-stale',
          link_id: 'link-1',
          type: 'Stale decision',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          count: 1,
          produces_tasks: false,
          choices: { approve: 'Approve' },
        }],
      }],
    })
    await flushPromises()

    expect(getTransferJobGroups).toHaveBeenCalledTimes(1)
    expect(wrapper.find('select').exists()).toBe(false)
    vi.advanceTimersByTime(1000)
    await flushPromises()
    expect(getTransferJobGroups).toHaveBeenCalledTimes(2)
    expect(wrapper.find('option[value="approve"]').exists()).toBe(false)
    expect(wrapper.get('.sip-detail-job-container').attributes('aria-busy')).toBe('true')

    currentGroups.resolve({ results: [] })
    await flushPromises()

    expect(wrapper.find('option[value="approve"]').exists()).toBe(false)
    expect(wrapper.get('.sip-detail-job-container').attributes('aria-busy')).toBe('false')
    wrapper.unmount()
  })

  it('warns when job groups fail to load and clears the warning after retry', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"}]}',
      data: {
        results: [{
          uuid: 't-1',
          directory: 'Transfer-1',
          timestamp: 1,
          started_at: 1,
          status: null,
          has_awaiting_decision: false,
          awaiting_job_uuids: [],
        }],
      },
    })
    transferSummariesMock.mockResolvedValueOnce({
      changed: false,
      raw: '{"results":[{"uuid":"t-1"}]}',
    })
    vi.mocked(getTransferJobGroups)
      .mockRejectedValueOnce(new Error('Unavailable'))
      .mockResolvedValueOnce({
        results: [{
          name: 'Group A',
          jobs: [{
            key: 'link-1:2',
            uuid: 'j-1',
            link_id: 'link-1',
            type: 'Recovered job',
            microservicegroup: 'Group A',
            currentstep: 2,
            timestamp: 1,
            first_timestamp: 1,
            count: 1,
            produces_tasks: false,
          }],
        }],
      })

    const wrapper = mount(ProcessMonitor, {
      props: {
        unitType: 'Transfer',
        config: { ...defaultConfig, polling_interval: 1 },
      },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    await wrapper.get('.sip-detail-directory').trigger('click')
    await flushPromises()

    const warning = wrapper.get('.monitor-job-groups-warning')
    expect(warning.attributes('role')).toBe('alert')
    expect(warning.text()).toBe('Unable to load job details. Retrying...')
    expect(wrapper.text()).not.toContain('Recovered job')

    vi.advanceTimersByTime(1000)
    await flushPromises()

    expect(getTransferJobGroups).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.monitor-job-groups-warning').exists()).toBe(false)
    await wrapper.get('.microservice-group').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Recovered job')
    wrapper.unmount()
  })

  it('refreshes job groups for only the currently expanded unit', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValueOnce({
      changed: true,
      raw: '{"results":[{"uuid":"t-1"},{"uuid":"t-2"}]}',
      data: {
        results: [
          {
            uuid: 't-1',
            directory: 'Transfer-1',
            timestamp: 2,
            started_at: 1,
            status: null,
            has_awaiting_decision: false,
            awaiting_job_uuids: [],
          },
          {
            uuid: 't-2',
            directory: 'Transfer-2',
            timestamp: 1,
            started_at: 1,
            status: null,
            has_awaiting_decision: false,
            awaiting_job_uuids: [],
          },
        ],
      },
    })
    transferSummariesMock.mockResolvedValueOnce({
      changed: false,
      raw: '{"results":[{"uuid":"t-1"},{"uuid":"t-2"}]}',
    })

    const wrapper = mount(ProcessMonitor, {
      props: {
        unitType: 'Transfer',
        config: { ...defaultConfig, polling_interval: 1 },
      },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    const unitRows = wrapper.findAll('.sip-detail-directory')
    await unitRows[0]?.trigger('click')
    await flushPromises()
    await unitRows[1]?.trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.sip-expanded')).toHaveLength(1)
    expect(getTransferJobGroups).toHaveBeenNthCalledWith(1, 't-1')
    expect(getTransferJobGroups).toHaveBeenNthCalledWith(2, 't-2')

    vi.advanceTimersByTime(1000)
    await flushPromises()

    expect(getTransferJobGroups).toHaveBeenCalledTimes(3)
    expect(getTransferJobGroups).toHaveBeenNthCalledWith(3, 't-2')

    wrapper.unmount()
  })

  it('applies job row status class based on status', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 't-1',
        directory: 'Transfer-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Job 1',
          microservicegroup: 'Group A',
          currentstep: 3,
          timestamp: 1,
          produces_tasks: true,
        }],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.find('.microservice-group').trigger('click')
    await wrapper.vm.$nextTick()

    const job = wrapper.find('.job')
    expect(job.exists()).toBe(true)
    expect(job.classes()).toContain('job-status-executing')
    wrapper.unmount()
  })

  it('keeps completed failed-transfer report jobs styled as successful', async () => {
    const config: MonitorConfig = {
      ...defaultConfig,
      job_statuses: {
        2: 'Completed successfully',
      },
    }

    transferSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 't-1',
        directory: 'test-virus',
        timestamp: 1,
        jobs: [{
          uuid: 'j-email-fail-report',
          type: 'Email fail report',
          microservicegroup: 'Failed transfer',
          currentstep: 2,
          timestamp: 1,
          produces_tasks: true,
        }],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.find('.microservice-group').trigger('click')
    await wrapper.vm.$nextTick()

    const job = wrapper.find('.job')
    expect(job.exists()).toBe(true)
    expect(job.text()).toContain('Email fail report')
    expect(job.text()).toContain('Completed successfully')
    expect(job.classes()).toContain('job-status-success')
    expect(job.classes()).not.toContain('job-status-failed')
    wrapper.unmount()
  })

  it('sorts units and jobs by timestamp descending', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [
        {
          uuid: 'u-1',
          directory: 'First',
          timestamp: 1,
          jobs: [
            {
              uuid: 'j-1',
              type: 'Older',
              microservicegroup: 'Group A',
              currentstep: 2,
              timestamp: 10,
              produces_tasks: true,
            },
            {
              uuid: 'j-2',
              type: 'Newer',
              microservicegroup: 'Group A',
              currentstep: 2,
              timestamp: 30,
              produces_tasks: true,
            },
          ],
        },
        {
          uuid: 'u-2',
          directory: 'Second',
          timestamp: 3,
          jobs: [],
        },
      ],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    const unitRows = wrapper.findAll('.sip-detail-uuid')
    const firstUnit = unitRows[0]
    if (!firstUnit) {
      throw new Error('Expected at least one unit row')
    }
    expect(firstUnit.text()).toBe('u-2')

    const sipU1 = wrapper.findAll('.sip').find(sip => sip.find('#sip-row-u-1').exists())
    if (!sipU1) {
      throw new Error('Expected SIP row for u-1')
    }
    await sipU1.find('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    await sipU1.find('.microservice-group').trigger('click')
    await wrapper.vm.$nextTick()
    const firstJob = sipU1.find('.job .job-detail-microservice span[title]')
    expect(firstJob.text()).toBe('Newer')
    wrapper.unmount()
  })

  it('renders ingest review links by link_id with legacy status gating', async () => {
    ingestSummariesMock.mockReset()
    ingestSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 's-1',
        directory: 'SIP-1',
        timestamp: 1,
        jobs: [
          {
            uuid: 'j-aip',
            type: 'Store AIP',
            link_id: '2d32235c-02d4-4686-88a6-96f4d6c7b1c3',
            microservicegroup: 'Group A',
            currentstep: 1,
            timestamp: 4,
            produces_tasks: true,
          },
          {
            uuid: 'j-normalization-awaiting',
            type: 'Approve normalization',
            link_id: 'de909a42-c5b5-46e1-9985-c031b50e9d30',
            microservicegroup: 'Group A',
            currentstep: 1,
            timestamp: 3,
            produces_tasks: true,
          },
          {
            uuid: 'j-normalization-complete',
            type: 'Approve normalization',
            link_id: 'de909a42-c5b5-46e1-9985-c031b50e9d30',
            microservicegroup: 'Group A',
            currentstep: 2,
            timestamp: 2,
            produces_tasks: true,
          },
          {
            uuid: 'j-dip',
            type: 'Move to uploadedDIPs directory',
            link_id: '2e31580d-1678-474b-83e5-a53d97d150f6',
            microservicegroup: 'Group A',
            currentstep: 2,
            timestamp: 1,
            produces_tasks: true,
          },
        ],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getIngestSummaries).toHaveBeenCalledTimes(1)
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    if (!wrapper.find('.microservice-group').exists()) {
      throw new Error(`Expected group row. HTML: ${wrapper.html()}`)
    }

    if (!wrapper.find('.job').exists()) {
      await wrapper.find('.microservice-group').trigger('click')
      await wrapper.vm.$nextTick()
    }

    const reviewLinks = wrapper.findAll('a.btn.btn-default.btn-xs')
    const hrefs = reviewLinks
      .map(item => item.attributes('href'))
      .filter((href): href is string => typeof href === 'string')
    const paths = hrefs.map(href => new URL(href, 'http://localhost').pathname)

    expect(paths).toContain('/ingest/preview/aip/j-aip/')
    expect(paths).toContain(
      '/ingest/preview/normalization/j-normalization-awaiting/',
    )
    expect(paths).toContain('/ingest/preview/dip/j-dip/')
    expect(paths).not.toContain(
      '/ingest/preview/normalization/j-normalization-complete/',
    )
    wrapper.unmount()
  })

  it('renders ingest inline actions by link_id', async () => {
    ingestSummariesMock.mockReset()
    ingestSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 's-1',
        directory: 'SIP-1',
        timestamp: 1,
        jobs: [
          {
            uuid: 'j-normalization',
            type: 'Approve normalization',
            link_id: 'de909a42-c5b5-46e1-9985-c031b50e9d30',
            microservicegroup: 'Group A',
            currentstep: 2,
            timestamp: 3,
            produces_tasks: true,
          },
          {
            uuid: 'j-as-mapping',
            type: 'Choose Config for ArchivesSpace DIP Upload',
            link_id: 'a0db8294-f02a-4f49-a557-b1310a715ffc',
            microservicegroup: 'Group A',
            currentstep: 2,
            timestamp: 2,
            produces_tasks: true,
          },
          {
            uuid: 'j-other',
            type: 'Other',
            link_id: '00000000-0000-0000-0000-000000000000',
            microservicegroup: 'Group A',
            currentstep: 2,
            timestamp: 1,
            produces_tasks: true,
          },
        ],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()

    if (!wrapper.find('.job').exists()) {
      await wrapper.find('.microservice-group').trigger('click')
      await wrapper.vm.$nextTick()
    }

    const normalizationReportLink = wrapper.find('.job-detail-actions a.btn_normalization_report')
    const asMappingLink = wrapper.find('.job-detail-actions a.btn_as_upload')

    expect(normalizationReportLink.exists()).toBe(true)
    expect(asMappingLink.exists()).toBe(true)
    const normalizationReportHref = normalizationReportLink.attributes('href')
    const asMappingHref = asMappingLink.attributes('href')
    if (!normalizationReportHref || !asMappingHref) {
      throw new Error('Expected inline action links to include href attributes')
    }
    expect(new URL(normalizationReportHref, 'http://localhost').pathname).toBe(
      '/ingest/normalization-report/s-1/',
    )
    expect(new URL(asMappingHref, 'http://localhost').pathname).toBe(
      '/ingest/s-1/upload/as/',
    )

    wrapper.unmount()
  })

  it('executes job choice on select change and removes the decision select on success', async () => {
    transferSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 't-1',
        directory: 'Transfer-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Job 1',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          produces_tasks: true,
          choices: {
            approve: 'Approve transfer',
          },
        }],
      }],
      mcp: true,
    })
    vi.mocked(executeChoice).mockResolvedValueOnce('ok')

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    const choiceSelect = wrapper.find('.job-detail-actions select')
    expect(choiceSelect.exists()).toBe(true)
    expect((choiceSelect.element as HTMLSelectElement).value).toBe('')
    expect(choiceSelect.find('option').text()).toContain('Actions')
    expect(wrapper.find('.sip').classes()).toContain('sip-selected')

    await choiceSelect.setValue('approve')
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(executeChoice).toHaveBeenCalledWith({
      uuid: 'j-1',
      choice: 'approve',
    })
    expect(wrapper.find('.job-detail-actions select').exists()).toBe(false)
    expect(wrapper.find('.sip').classes()).toContain('sip-selected')
    expect(wrapper.find('.sip-detail-icon-status .monitor-status-icon-arrow-refresh').exists()).toBe(true)
    wrapper.unmount()
  })

  it('accelerates polling after executing a job choice', async () => {
    vi.useFakeTimers()
    transferSummariesMock.mockResolvedValue({
      objects: [{
        uuid: 't-1',
        directory: 'Transfer-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Job 1',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          produces_tasks: true,
          choices: {
            approve: 'Approve transfer',
          },
        }],
      }],
      mcp: true,
    })
    vi.mocked(executeChoice).mockResolvedValueOnce('ok')

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    expect(getTransferSummaries).toHaveBeenCalledTimes(1)

    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    const choiceSelect = wrapper.find('.job-detail-actions select')
    expect(choiceSelect.exists()).toBe(true)
    await choiceSelect.setValue('approve')
    await flushPromises()
    await wrapper.vm.$nextTick()
    expect(executeChoice).toHaveBeenCalledWith({
      uuid: 'j-1',
      choice: 'approve',
    })

    await vi.advanceTimersByTimeAsync(999)
    await flushPromises()
    expect(getTransferSummaries).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1)
    await flushPromises()
    expect(getTransferSummaries).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })

  it('redirects to SIP upload mapping page for Upload DIP to ArchivesSpace choice', async () => {
    ingestSummariesMock.mockReset()
    vi.mocked(getIngestUploadAsUrl).mockClear()
    vi.mocked(getIngestUploadAsUrl).mockReturnValueOnce('#upload-as')
    ingestSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 's-1',
        directory: 'SIP-1',
        timestamp: 1,
        jobs: [{
          uuid: 'j-1',
          type: 'Upload DIP',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          produces_tasks: true,
          choices: {
            '3572f844-5e69-4000-a24b-4e32d3487f82': 'Upload DIP to ArchivesSpace',
          },
        }],
      }],
      mcp: true,
    })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    const choiceSelect = wrapper.find('.job-detail-actions select')
    expect(choiceSelect.exists()).toBe(true)

    await choiceSelect.setValue('3572f844-5e69-4000-a24b-4e32d3487f82')
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(executeChoice).not.toHaveBeenCalled()
    expect(getIngestUploadAsUrl).toHaveBeenCalledTimes(1)
    expect(getIngestUploadAsUrl).toHaveBeenCalledWith('s-1')
    wrapper.unmount()
  })

  it('opens Upload DIP dialog when AtoM target is missing, then posts target and executes choice', async () => {
    ingestSummariesMock.mockReset()
    vi.mocked(getUploadTarget).mockReset()
    vi.mocked(setUploadTarget).mockReset()

    ingestSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 's-1',
        directory: 'SIP-1',
        timestamp: 1,
        access_system_id: '',
        jobs: [{
          uuid: 'j-1',
          type: 'Upload DIP',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          produces_tasks: true,
          choices: {
            '0fe9842f-9519-4067-a691-8a363132ae24': 'Upload DIP to AtoM',
          },
        }],
      }],
      mcp: true,
    })
    vi.mocked(getUploadTarget).mockResolvedValueOnce({ target: '' })
    vi.mocked(setUploadTarget).mockResolvedValueOnce({ ready: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    const choiceSelect = wrapper.find('.job-detail-actions select')
    expect(choiceSelect.exists()).toBe(true)

    await choiceSelect.setValue('0fe9842f-9519-4067-a691-8a363132ae24')
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getUploadTarget).toHaveBeenCalledTimes(1)
    expect(getUploadTarget).toHaveBeenCalledWith('s-1')
    expect(executeChoice).not.toHaveBeenCalled()

    const targetInput = document.querySelector('.monitor-upload-modal input') as HTMLInputElement | null
    expect(targetInput).not.toBeNull()
    if (!targetInput) {
      throw new Error('Expected upload target input')
    }
    targetInput.value = 'atom-target-1'
    targetInput.dispatchEvent(new Event('input'))
    const uploadForm = document.querySelector('.monitor-upload-modal form') as HTMLFormElement | null
    expect(uploadForm).not.toBeNull()
    if (!uploadForm) {
      throw new Error('Expected upload target form')
    }
    uploadForm.dispatchEvent(new Event('submit'))
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(setUploadTarget).toHaveBeenCalledWith('s-1', 'atom-target-1')
    expect(executeChoice).toHaveBeenCalledWith({
      uuid: 'j-1',
      choice: '0fe9842f-9519-4067-a691-8a363132ae24',
    })
    wrapper.unmount()
  })

  it('posts stored AtoM target and executes choice without opening Upload DIP dialog', async () => {
    ingestSummariesMock.mockReset()
    vi.mocked(getUploadTarget).mockReset()
    vi.mocked(setUploadTarget).mockReset()

    ingestSummariesMock.mockResolvedValueOnce({
      objects: [{
        uuid: 's-1',
        directory: 'SIP-1',
        timestamp: 1,
        access_system_id: 'stored-target',
        jobs: [{
          uuid: 'j-1',
          type: 'Upload DIP',
          microservicegroup: 'Group A',
          currentstep: 1,
          timestamp: 1,
          produces_tasks: true,
          choices: {
            '0fe9842f-9519-4067-a691-8a363132ae24': 'Upload DIP to AtoM',
          },
        }],
      }],
      mcp: true,
    })
    vi.mocked(setUploadTarget).mockResolvedValueOnce({ ready: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()
    const choiceSelect = wrapper.find('.job-detail-actions select')
    expect(choiceSelect.exists()).toBe(true)

    await choiceSelect.setValue('0fe9842f-9519-4067-a691-8a363132ae24')
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getUploadTarget).not.toHaveBeenCalled()
    expect(setUploadTarget).toHaveBeenCalledWith('s-1', 'stored-target')
    expect(executeChoice).toHaveBeenCalledWith({
      uuid: 'j-1',
      choice: '0fe9842f-9519-4067-a691-8a363132ae24',
    })
    wrapper.unmount()
  })
})

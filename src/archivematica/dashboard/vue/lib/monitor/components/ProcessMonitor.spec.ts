import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import ProcessMonitor from './ProcessMonitor.vue'

vi.mock('@/shared/http/transfer', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http/transfer')>('@/shared/http/transfer')
  return {
    ...actual,
    getTransferStatuses: vi.fn(),
  }
})

vi.mock('@/shared/http/ingest', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http/ingest')>('@/shared/http/ingest')
  return {
    ...actual,
    getIngestStatuses: vi.fn(),
  }
})

vi.mock('@/shared/http', async () => {
  const actual = await vi.importActual<typeof import('@/shared/http')>('@/shared/http')
  return {
    ...actual,
    executeChoice: vi.fn(),
    getIngestUploadAsUrl: vi.fn(actual.getIngestUploadAsUrl),
    getUploadTarget: vi.fn(),
    setUploadTarget: vi.fn(),
  }
})

import { getTransferStatuses } from '@/shared/http/transfer'
import { getIngestStatuses } from '@/shared/http/ingest'
import { executeChoice, getIngestUploadAsUrl, getUploadTarget, setUploadTarget } from '@/shared/http'
import type { MonitorConfig } from '@/monitor/composables'

const i18n = createI18nMock()

const defaultConfig: MonitorConfig = {
  polling_interval: 10,
  microservices_help: {},
  job_statuses: {},
}

describe('ProcessMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  it('fetches transfer statuses when unitType is Transfer', async () => {
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
      objects: [{ uuid: 't-1', directory: 'Transfer-1', timestamp: 1, jobs: [] }],
      mcp: true,
    })
    vi.mocked(getIngestStatuses).mockResolvedValueOnce({ objects: [], mcp: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'Transfer', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getTransferStatuses).toHaveBeenCalledTimes(1)
    expect(getIngestStatuses).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Transfer-1')
  })

  it('fetches ingest statuses when unitType is SIP', async () => {
    vi.mocked(getIngestStatuses).mockResolvedValueOnce({
      objects: [{ uuid: 's-1', directory: 'SIP-1', timestamp: 1, jobs: [] }],
      mcp: true,
    })
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({ objects: [], mcp: true })

    const wrapper = mount(ProcessMonitor, {
      props: { unitType: 'SIP', config: defaultConfig },
      global: {
        plugins: [i18n],
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(getIngestStatuses).toHaveBeenCalledTimes(1)
    expect(getTransferStatuses).not.toHaveBeenCalled()
    expect(wrapper.find('#sip-units').exists()).toBe(true)
  })

  it('polls using polling_interval from transfer monitor config', async () => {
    vi.useFakeTimers()
    vi.mocked(getTransferStatuses).mockResolvedValue({
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
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })

  it('keeps current rows visible while polling refreshes', async () => {
    vi.useFakeTimers()
    vi.mocked(getTransferStatuses).mockResolvedValue({
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

  it('toggles job container when clicking row details', async () => {
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
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

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(true)

    await wrapper.find('.sip-detail-directory').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(false)
    wrapper.unmount()
  })

  it('does not toggle job container when clicking row status icon', async () => {
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
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

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(true)

    await wrapper.find('.sip-detail-icon-status').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(true)
    wrapper.unmount()
  })

  it('auto-expands a unit when a job is awaiting decision', async () => {
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
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
    expect(wrapper.find('.sip-detail-job-container').exists()).toBe(true)
    wrapper.unmount()
  })

  it('applies job row status class based on status', async () => {
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
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
    await wrapper.find('.microservice-group').trigger('click')
    await wrapper.vm.$nextTick()

    const job = wrapper.find('.job')
    expect(job.exists()).toBe(true)
    expect(job.classes()).toContain('job-status-executing')
    wrapper.unmount()
  })

  it('sorts units and jobs by timestamp descending', async () => {
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
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
    await sipU1.find('.microservice-group').trigger('click')
    await wrapper.vm.$nextTick()
    const firstJob = sipU1.find('.job .job-detail-microservice span[title]')
    expect(firstJob.text()).toBe('Newer')
    wrapper.unmount()
  })

  it('renders ingest review links by link_id with legacy status gating', async () => {
    vi.mocked(getIngestStatuses).mockReset()
    vi.mocked(getIngestStatuses).mockResolvedValueOnce({
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

    expect(getIngestStatuses).toHaveBeenCalledTimes(1)
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
    vi.mocked(getIngestStatuses).mockReset()
    vi.mocked(getIngestStatuses).mockResolvedValueOnce({
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
    vi.mocked(getTransferStatuses).mockResolvedValueOnce({
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
    expect(wrapper.find('.sip-detail-icon-status img').attributes('src')).toContain('arrow_refresh.png')
    wrapper.unmount()
  })

  it('redirects to SIP upload mapping page for Upload DIP to ArchivesSpace choice', async () => {
    vi.mocked(getIngestStatuses).mockReset()
    vi.mocked(getIngestUploadAsUrl).mockClear()
    vi.mocked(getIngestUploadAsUrl).mockReturnValueOnce('#upload-as')
    vi.mocked(getIngestStatuses).mockResolvedValueOnce({
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
    vi.mocked(getIngestStatuses).mockReset()
    vi.mocked(getUploadTarget).mockReset()
    vi.mocked(setUploadTarget).mockReset()

    vi.mocked(getIngestStatuses).mockResolvedValueOnce({
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
    vi.mocked(getIngestStatuses).mockReset()
    vi.mocked(getUploadTarget).mockReset()
    vi.mocked(setUploadTarget).mockReset()

    vi.mocked(getIngestStatuses).mockResolvedValueOnce({
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

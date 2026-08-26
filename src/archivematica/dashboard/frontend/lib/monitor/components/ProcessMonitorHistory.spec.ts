import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import type { MonitorUnitType } from '@/monitor/composables'
import type { ProcessingJobGroupsResponse, ProcessingUnitSummariesResponse } from '@/shared/http/processing'
import ProcessMonitor from './ProcessMonitor.vue'

vi.mock('@/shared/http/transfer', async () => ({
  ...await vi.importActual<typeof import('@/shared/http/transfer')>('@/shared/http/transfer'),
  getTransferSummaries: vi.fn(),
}))
vi.mock('@/shared/http/ingest', async () => ({
  ...await vi.importActual<typeof import('@/shared/http/ingest')>('@/shared/http/ingest'),
  getIngestSummaries: vi.fn(),
}))
vi.mock('@/shared/http', async () => ({
  ...await vi.importActual<typeof import('@/shared/http')>('@/shared/http'),
  getTransferJobGroups: vi.fn(),
  getIngestJobGroups: vi.fn(),
}))

import { getTransferSummaries } from '@/shared/http/transfer'
import { getIngestSummaries } from '@/shared/http/ingest'
import { getTransferJobGroups, getIngestJobGroups } from '@/shared/http'

const unitUuid = '59402c61-3aba-4af7-966a-996073c0601d'
const linkId = '440ef381-8fe8-4b6e-9198-270ee5653454'
const jobUuid = 'c1319b63-ad30-49e2-b6d5-43a8b83136cb'
const summaries: ProcessingUnitSummariesResponse = {
  results: [{
    uuid: unitUuid,
    directory: 'Example',
    timestamp: 2,
    started_at: 1,
    status: null,
    has_awaiting_decision: false, awaiting_job_uuids: [],
  }],
}
const jobGroups = (count: number): ProcessingJobGroupsResponse => ({
  results: [{
    name: 'Normalize',
    jobs: [{
      key: `${linkId}:2`,
      uuid: jobUuid,
      link_id: linkId,
      type: 'Normalize for preservation',
      microservicegroup: 'Normalize',
      currentstep: 2,
      timestamp: 2,
      count,
      produces_tasks: true,
    }],
  }],
})
let wrapper: VueWrapper | undefined

const createMonitor = async (unitType: MonitorUnitType, count: number) => {
  vi.mocked(getTransferJobGroups).mockResolvedValue(jobGroups(count))
  vi.mocked(getIngestJobGroups).mockResolvedValue(jobGroups(count))
  wrapper = mount(ProcessMonitor, {
    props: {
      unitType,
      config: {
        polling_interval: 5,
        microservices_help: {},
        job_statuses: { 2: 'Completed successfully' },
      },
    },
    global: { plugins: [createI18nMock()] },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.resetAllMocks()
  vi.useFakeTimers()
  vi.stubGlobal('fetch', vi.fn())
  vi.spyOn(window, 'open').mockReturnValue(null)
  const response = { changed: true, raw: JSON.stringify(summaries), data: summaries }
  vi.mocked(getTransferSummaries).mockResolvedValue(response)
  vi.mocked(getIngestSummaries).mockResolvedValue(response)
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
  vi.useRealTimers()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe.each([
  { unitType: 'Transfer' as const, urlPrefix: 'transfer' },
  { unitType: 'SIP' as const, urlPrefix: 'ingest' },
])('$unitType monitor Job history', ({ unitType, urlPrefix }) => {
  it('opens scoped history only when the repeated Job action is activated', async () => {
    const monitor = await createMonitor(unitType, 14000)

    expect(getTransferJobGroups).not.toHaveBeenCalled()
    expect(getIngestJobGroups).not.toHaveBeenCalled()
    expect(window.open).not.toHaveBeenCalled()
    expect(fetch).not.toHaveBeenCalled()

    await monitor.get('.sip-detail-directory').trigger('click')
    await flushPromises()
    await monitor.get('.microservice-group').trigger('click')
    await flushPromises()

    const details = unitType === 'Transfer' ? getTransferJobGroups : getIngestJobGroups
    expect(details).toHaveBeenCalledExactlyOnceWith(unitUuid)
    expect(window.open).not.toHaveBeenCalled()
    expect(fetch).not.toHaveBeenCalled()
    const action = monitor.get('.btn_show_tasks')
    expect(action.attributes('aria-label')).toBe('Job history')

    await action.trigger('click')

    expect(window.open).toHaveBeenCalledExactlyOnceWith(
      expect.stringContaining(`/${urlPrefix}/${unitUuid}/job-history/${linkId}/`),
      'output',
    )
    expect(fetch).not.toHaveBeenCalled()
    expect(monitor.find('.sip-detail-job-container').exists()).toBe(true)
  })

  it('preserves the direct Tasks URL for a singleton Job', async () => {
    const monitor = await createMonitor(unitType, 1)
    await monitor.get('.sip-detail-directory').trigger('click')
    await flushPromises()
    await monitor.get('.microservice-group').trigger('click')
    await flushPromises()
    const action = monitor.get('.btn_show_tasks')
    expect(action.attributes('aria-label')).toBe('Tasks')

    await action.trigger('click')

    expect(window.open).toHaveBeenCalledExactlyOnceWith(
      expect.stringContaining(`/tasks/${jobUuid}/`),
      'output',
    )
    expect(fetch).not.toHaveBeenCalled()
  })
})

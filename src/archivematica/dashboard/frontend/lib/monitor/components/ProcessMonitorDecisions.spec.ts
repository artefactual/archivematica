import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import ProcessMonitor from './ProcessMonitor.vue'
import type { ProcessingJob, ProcessingJobGroupsResponse } from '@/shared/http/processing'

// Exercise the real HTTP parsing and unchanged-response detection while
// controlling only the clock and the delivery of network responses.
const deferred = <T>() => {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>((yes, no) => {
    resolve = yes
    reject = no
  })
  return { promise, resolve, reject }
}
const json = (data: unknown) => new Response(JSON.stringify(data), {
  headers: { 'Content-Type': 'application/json' },
})
const summary = (awaiting: string[] = [], timestamp = 1) => ({ results: [{
  uuid: 'unit', directory: 'Decision package', timestamp, started_at: 1,
  has_awaiting_decision: awaiting.length > 0, awaiting_job_uuids: awaiting, status: null,
}] })
const groups = (awaiting: string[] = []): ProcessingJobGroupsResponse => ({ results: [{
  name: 'Group A', jobs: [...awaiting, 'history'].map(uuid => ({
    uuid, key: `job:${uuid}`, link_id: `link:${uuid}`, type: uuid,
    microservicegroup: 'Group A', timestamp: 2,
    produces_tasks: uuid === 'history', count: uuid === 'history' ? 12 : 1,
    currentstep: uuid === 'history' ? 2 : 1,
    ...(uuid === 'history' ? {} : { choices: { approve: 'Approve' } }),
  })),
}] })

let wrapper: VueWrapper | undefined
let requests: string[]
let statusReply: () => Promise<Response>
let detailReply: () => Promise<Response>
let choiceReply: (uuid: string) => Promise<Response>
let uploadReply: () => Promise<Response>
beforeEach(() => {
  vi.useFakeTimers()
  requests = []
  statusReply = async () => json(summary())
  detailReply = async () => json(groups())
  choiceReply = async () => new Response('ok')
  uploadReply = async () => json({ ready: true })
  vi.stubGlobal('fetch', vi.fn(async (url: string, options?: RequestInit) => {
    const path = new URL(url).pathname
    requests.push(path)
    if (path.endsWith('/status/')) return statusReply()
    if (path.endsWith('/job-groups/')) return detailReply()
    if (path === '/mcp/execute/') return choiceReply(new URLSearchParams(String(options?.body)).get('uuid') ?? '')
    if (path.endsWith('/upload/')) return uploadReply()
    throw new Error(`Unexpected request ${path}`)
  }))
})
afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  vi.useRealTimers()
})

it('rechecks an ingest decision after awaiting the AtoM upload target response', async () => {
  const choice = '0fe9842f-9519-4067-a691-8a363132ae24'
  statusReply = async () => json({ results: summary(['a']).results.map(unit => ({
    ...unit, access_system_id: 'stored-target',
  })) })
  detailReply = async () => {
    const payload = groups(['a'])
    payload.results[0]!.jobs[0]!.choices = { [choice]: 'Upload DIP to AtoM' }
    return json(payload)
  }
  const target = deferred<Response>()
  uploadReply = () => target.promise
  vi.spyOn(window, 'alert').mockImplementation(() => {})
  wrapper = mount(ProcessMonitor, {
    props: { unitType: 'SIP', config: { polling_interval: 5, microservices_help: {}, job_statuses: {} } },
    global: { plugins: [createI18nMock()] },
  })
  await flushPromises()
  await wrapper.get('.sip-detail-directory').trigger('click')
  await flushPromises()
  await wrapper.get('select').setValue(choice)
  await flushPromises()
  expect(requests).toContain('/ingest/unit/upload/')
  statusReply = async () => json(summary())
  await vi.advanceTimersByTimeAsync(5000)
  await flushPromises()
  target.resolve(json({ ready: true }))
  await flushPromises()
  expect(requests).not.toContain('/mcp/execute/')
})

describe.each(['Transfer', 'SIP'] as const)('Current monitor decisions for %s', (unitType) => {
  const create = async () => {
    wrapper = mount(ProcessMonitor, {
      props: { unitType, config: { polling_interval: 5, microservices_help: {}, job_statuses: {} } },
      global: { plugins: [createI18nMock()] },
    })
    await flushPromises()
    await wrapper.get('.sip-detail-directory').trigger('click')
    await flushPromises()
    return wrapper
  }
  const poll = async () => {
    await vi.advanceTimersByTimeAsync(5000)
    await flushPromises()
  }
  const detailRequests = () => requests.filter(path => path.endsWith('/job-groups/'))
  const renderedJobs = (monitor: VueWrapper): ProcessingJob[] =>
    monitor.findComponent({ name: 'ProcessMonitorUnit' }).props('unitGroups')
      .flatMap((group: { jobs: ProcessingJob[] }) => group.jobs)
  const expectHistory = (monitor: VueWrapper) => {
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
    expect(renderedJobs(monitor)).toContainEqual(expect.objectContaining({
      uuid: 'history', count: 12, produces_tasks: true, link_id: 'link:history',
    }))
    expect(monitor.get('.sip-detail-job-container').attributes('aria-busy')).toBe('false')
  }

  it('keeps history but rejects a decision captured between two no-decision summaries', async () => {
    const delayed = deferred<Response>()
    detailReply = () => delayed.promise
    const monitor = await create()
    statusReply = async () => json(summary([], 3))
    await poll()
    expect(monitor.findComponent({ name: 'ProcessMonitorUnit' }).props('unit').timestamp).toBe(3)
    delayed.resolve(json(groups(['a'])))
    await flushPromises()
    expect(monitor.find('select').exists()).toBe(false)
    expectHistory(monitor)
    expect(detailRequests()).toHaveLength(1)
    detailReply = async () => {
      throw new Error('Detail endpoint unavailable')
    }
    for (let n = 0; n < 3; n++) {
      await poll()
      expect(monitor.find('select').exists()).toBe(false)
      expect(monitor.find('.monitor-job-groups-warning').exists()).toBe(true)
      expectHistory(monitor)
    }
  })

  it('removes cached controls as soon as a summary resolves their decision, even if details fail', async () => {
    statusReply = async () => json(summary(['a']))
    detailReply = async () => json(groups(['a']))
    const monitor = await create()
    expect(monitor.find('select').exists()).toBe(true)
    statusReply = async () => json(summary())
    detailReply = async () => {
      throw new Error('Detail endpoint unavailable')
    }
    await poll()
    expect(monitor.find('select').exists()).toBe(false)
    expectHistory(monitor)
  })

  it('distinguishes replacement decisions without a timestamp or boolean change', async () => {
    statusReply = async () => json(summary(['a']))
    const delayed = deferred<Response>()
    detailReply = () => delayed.promise
    const monitor = await create()
    statusReply = async () => json(summary(['b']))
    await poll()
    delayed.resolve(json(groups(['a', 'b'])))
    await flushPromises()
    expect(monitor.findAll('select')).toHaveLength(1)
    expect(renderedJobs(monitor).find(job => job.uuid === 'a')?.choices).toBeUndefined()
    expect(renderedJobs(monitor).find(job => job.uuid === 'b')?.choices).toEqual({ approve: 'Approve' })
    expectHistory(monitor)
  })

  it('reveals an early detail decision when a later summary confirms it despite detail failure', async () => {
    detailReply = async () => json(groups(['b']))
    const monitor = await create()
    expect(monitor.find('select').exists()).toBe(false)
    expectHistory(monitor)
    statusReply = async () => json(summary(['b'], 2))
    detailReply = async () => {
      throw new Error('Detail endpoint unavailable')
    }
    await poll()
    expect(monitor.findAll('select')).toHaveLength(1)
    expect(monitor.get('select').attributes('disabled')).toBeUndefined()
  })

  it.each([false, true])('accepts a slow response across six polls when summaries change: %s', async (change) => {
    statusReply = async () => json(summary(['a']))
    const delayed = deferred<Response>()
    detailReply = () => delayed.promise
    const monitor = await create()
    for (let n = 0; n < 6; n++) {
      statusReply = async () => json(summary(['a'], change ? n + 2 : 1))
      await poll()
    }
    expect(detailRequests()).toHaveLength(1)
    delayed.resolve(json(groups(['a'])))
    await flushPromises()
    expectHistory(monitor)
    expect(monitor.findAll('select')).toHaveLength(1)
    expect(detailRequests()).toHaveLength(1)
  })

  it('rejects a stale choice event after the summary has removed its decision', async () => {
    statusReply = async () => json(summary(['a']))
    detailReply = async () => json(groups(['a']))
    const monitor = await create()
    const job = renderedJobs(monitor).find(job => job.uuid === 'a')!
    statusReply = async () => json(summary())
    await poll()
    monitor.findComponent({ name: 'ProcessMonitorUnit' }).vm.$emit('execute-job-choice', {
      job, choice: 'approve', unitUuid: 'unit',
    })
    await flushPromises()
    expect(requests).not.toContain('/mcp/execute/')
  })

  it('keeps simultaneous choices pending and allows retry only for the failed choice', async () => {
    statusReply = async () => json(summary(['a', 'b']))
    detailReply = async () => json(groups(['a', 'b']))
    const first = deferred<Response>()
    const second = deferred<Response>()
    choiceReply = uuid => uuid === 'a' ? first.promise : second.promise
    const monitor = await create()
    const selects = monitor.findAll('select')
    await selects[0]!.setValue('approve')
    await selects[1]!.setValue('approve')
    statusReply = async () => json(summary(['a', 'b'], 3))
    await poll()
    first.resolve(new Response('ok'))
    await flushPromises()
    await poll()
    expect(detailRequests()).toHaveLength(1)
    expect(monitor.findAll('select')).toHaveLength(1)
    expect(monitor.get('select').attributes('disabled')).toBeDefined()
    second.reject(new Error('Choice b failed'))
    await flushPromises()
    expect(detailRequests()).toHaveLength(2)
    expect(monitor.findAll('select')).toHaveLength(1)
    expect(monitor.get('select').attributes('disabled')).toBeUndefined()
    expect(renderedJobs(monitor).find(job => job.uuid === 'a')?.choices).toBeUndefined()
    choiceReply = async () => new Response('ok')
    await monitor.get('select').setValue('approve')
    await flushPromises()
    expect(monitor.find('select').exists()).toBe(false)
  })
})

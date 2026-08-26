import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n/testing'
import ProcessMonitor from './ProcessMonitor.vue'
import type { ProcessingUnitSummary } from '@/shared/http/processing'

vi.mock('@/shared/http/transfer', async () => ({
  ...await vi.importActual<typeof import('@/shared/http/transfer')>('@/shared/http/transfer'),
  getTransferSummaries: vi.fn(),
}))
vi.mock('@/shared/http', async () => ({
  ...await vi.importActual<typeof import('@/shared/http')>('@/shared/http'),
  executeChoice: vi.fn(),
  getTransferJobGroups: vi.fn(),
}))
import { getTransferSummaries } from '@/shared/http/transfer'
import { getTransferJobGroups, executeChoice } from '@/shared/http'

const summary = (uuid = 't-1', timestamp = 1, awaiting = false): ProcessingUnitSummary => ({
  uuid, directory: uuid, timestamp, started_at: 1, status: null, has_awaiting_decision: awaiting, awaiting_job_uuids: awaiting ? ['j-1'] : [],
})
const response = (units: ReturnType<typeof summary>[]) => ({ changed: true, raw: JSON.stringify(units), data: { results: units } })
const groups = (decision = false) => ({ results: [{ name: 'Group A', jobs: [{
  key: 'job:j-1', uuid: 'j-1', link_id: 'link-1', type: 'Review probe job',
  microservicegroup: 'Group A', currentstep: decision ? 1 : 2, timestamp: 1,
  count: 1, produces_tasks: false, ...(decision ? { choices: { approve: 'Approve' } } : {}),
}] }] })
const deferred = <T>() => {
  let resolve!: (value: T) => void
  let reject!: (value: unknown) => void
  const promise = new Promise<T>((yes, no) => {
    resolve = yes
    reject = no
  })
  return { promise, resolve, reject }
}
const summaries = vi.mocked(getTransferSummaries)
const details = vi.mocked(getTransferJobGroups)
let wrapper: VueWrapper | undefined
const create = async () => {
  wrapper = mount(ProcessMonitor, {
    props: { unitType: 'Transfer', config: { polling_interval: 5, microservices_help: {}, job_statuses: { 1: 'Awaiting decision', 2: 'Completed successfully', 3: 'Executing command(s)' } } },
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

beforeEach(() => {
  vi.resetAllMocks()
  vi.useFakeTimers()
  summaries.mockResolvedValue({ changed: false, raw: 'unchanged' })
})
afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
  vi.useRealTimers()
})

describe('ProcessMonitor pending requests', () => {
  it('renders completed detail responses despite repeated unchanged summary polls', async () => {
    summaries.mockResolvedValueOnce(response([summary()]))
    const pending = Array.from({ length: 4 }, () => deferred<ReturnType<typeof groups>>())
    for (const item of pending) details.mockImplementationOnce(() => item.promise)
    const monitor = await create()
    for (let cycle = 0; cycle < 3; cycle++) {
      await poll()
      pending[cycle]!.resolve(groups())
      await flushPromises()
      expect(monitor.findAll('.microservice-group')).toHaveLength(1)
      expect(monitor.find('[role="status"]').exists()).toBe(false)
      expect(details).toHaveBeenCalledTimes(cycle + 1)
    }
  })

  it('accepts pending details when only another unit changes', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 10), summary('t-2', 1)]))
    summaries.mockResolvedValueOnce(response([summary('t-1', 10), summary('t-2', 2)]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    details.mockImplementation(() => new Promise(() => {}))
    const monitor = await create()
    await poll()
    pending.resolve(groups())
    await flushPromises()
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
  })

  it('accepts history details as nondecision processing continues on the same unit', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1)]))
    summaries.mockResolvedValueOnce(response([summary('t-1', 2)]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    details.mockImplementation(() => new Promise(() => {}))
    const monitor = await create()
    await poll()
    pending.resolve(groups())
    await flushPromises()
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
  })

  it('shows a slow detail failure even after unchanged summary polling', async () => {
    summaries.mockResolvedValueOnce(response([summary()]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    details.mockImplementation(() => new Promise(() => {}))
    const monitor = await create()
    await poll()
    pending.reject(new Error('RPC failed after more than five seconds'))
    await flushPromises()
    expect(monitor.find('.monitor-job-groups-warning').exists()).toBe(true)
  })

  it('does not restore a decision after successful local execution before the next summary', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockResolvedValueOnce(groups(true))
    details.mockImplementationOnce(() => pending.promise)
    vi.mocked(executeChoice).mockResolvedValue('ok')
    const monitor = await create()
    await poll()
    await monitor.get('.job-detail-actions select').setValue('approve')
    await flushPromises()
    expect(monitor.find('option[value="approve"]').exists()).toBe(false)
    pending.resolve(groups(true))
    await flushPromises()
    expect(monitor.find('option[value="approve"]').exists()).toBe(false)
  })

  it('keeps pretransition history without restoring obsolete choices', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    summaries.mockResolvedValueOnce(response([summary('t-1', 2, false)]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    details.mockImplementation(() => new Promise(() => {}))
    const monitor = await create()
    await poll()
    pending.resolve(groups(true))
    await flushPromises()
    expect(monitor.find('option[value="approve"]').exists()).toBe(false)
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
    expect(details).toHaveBeenCalledTimes(1)
  })

  it('discards collapsed responses and performs no queued reload for the collapsed unit', async () => {
    summaries.mockResolvedValueOnce(response([summary()]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    const monitor = await create()
    await poll()
    await monitor.get('.sip-detail-directory').trigger('click')
    pending.resolve(groups(true))
    await flushPromises()
    expect(monitor.find('option[value="approve"]').exists()).toBe(false)
    expect(details).toHaveBeenCalledTimes(1)
    expect(monitor.find('.sip-expanded').exists()).toBe(false)
  })

  it('fetches fresh details when reopening a unit with an obsolete request pending', async () => {
    summaries.mockResolvedValueOnce(response([summary()]))
    const old = deferred<ReturnType<typeof groups>>()
    const fresh = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => old.promise).mockImplementationOnce(() => fresh.promise)
    const monitor = await create()
    await monitor.get('.sip-detail-directory').trigger('click')
    await monitor.get('.sip-detail-directory').trigger('click')
    await poll()
    old.resolve(groups(true))
    await flushPromises()
    expect(monitor.find('select').exists()).toBe(false)
    expect(details).toHaveBeenCalledTimes(2)
    await poll()
    await poll()
    fresh.resolve(groups())
    await flushPromises()
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
    expect(monitor.get('.sip-detail-job-container').attributes('aria-busy')).toBe('false')
  })

  it('accepts a decision replacement held across further unchanged polls', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    summaries.mockResolvedValueOnce(response([summary('t-1', 2, false)]))
    const old = deferred<ReturnType<typeof groups>>()
    const fresh = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => old.promise).mockImplementationOnce(() => fresh.promise)
    const monitor = await create()
    await poll()
    old.resolve(groups(true))
    await flushPromises()
    await poll()
    await poll()
    fresh.resolve(groups())
    await flushPromises()
    expect(monitor.find('select').exists()).toBe(false)
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
    expect(details).toHaveBeenCalledTimes(2)
  })

  it.each(['removed', 'waiting'] as const)('discards details when the unit becomes %s', async (state) => {
    summaries.mockResolvedValueOnce(response([summary()]))
    summaries.mockResolvedValueOnce(response(state === 'removed'
      ? []
      : [{
          ...summary(), processing_state: 'waiting_for_processing',
        }]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    const monitor = await create()
    await poll()
    pending.resolve(groups(true))
    await flushPromises()
    expect(monitor.find('.sip-expanded').exists()).toBe(false)
    expect(details).toHaveBeenCalledTimes(1)
  })

  it('does not replace the newly expanded unit with the previous unit response', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 10), summary('t-2', 1)]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise).mockResolvedValueOnce(groups())
    const monitor = await create()
    await monitor.findAll('.sip-detail-directory')[1]!.trigger('click')
    await flushPromises()
    pending.resolve(groups(true))
    await flushPromises()
    expect(monitor.findAll('.sip-expanded')).toHaveLength(1)
    expect(monitor.get('.sip-expanded').text()).toContain('t-2')
    expect(monitor.find('select').exists()).toBe(false)
    expect(details.mock.calls.map(call => call[0])).toEqual(['t-1', 't-2'])
  })

  it('does not schedule a replacement after unmounting', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    summaries.mockResolvedValueOnce(response([summary('t-1', 2, false)]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise)
    const monitor = await create()
    await poll()
    monitor.unmount()
    wrapper = undefined
    pending.resolve(groups(true))
    await flushPromises()
    expect(details).toHaveBeenCalledTimes(1)
  })

  it('keeps a choice disabled while an earlier detail response finishes during execution', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    const old = deferred<ReturnType<typeof groups>>()
    const choice = deferred<string>()
    details.mockResolvedValueOnce(groups(true)).mockImplementationOnce(() => old.promise)
    details.mockResolvedValue(groups(true))
    vi.mocked(executeChoice).mockImplementationOnce(() => choice.promise)
    const monitor = await create()
    await poll()
    await monitor.get('select').setValue('approve')
    old.resolve(groups(true))
    await flushPromises()
    await poll()
    expect(details).toHaveBeenCalledTimes(2)
    expect(monitor.get('select').attributes('disabled')).toBeDefined()
    choice.resolve('ok')
    await flushPromises()
    expect(details).toHaveBeenCalledTimes(3)
    // Even a fresh response can precede persistence of an acknowledged choice.
    expect(monitor.find('select').exists()).toBe(false)
    await vi.advanceTimersByTimeAsync(1000)
    await flushPromises()
    expect(monitor.find('select').exists()).toBe(false)
  })

  it('recovers a failed choice through a fresh request and permits retry', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    const old = deferred<ReturnType<typeof groups>>()
    const choice = deferred<string>()
    details.mockResolvedValueOnce(groups(true)).mockImplementationOnce(() => old.promise)
    details.mockResolvedValue(groups(true))
    vi.mocked(executeChoice).mockImplementationOnce(() => choice.promise).mockResolvedValue('ok')
    const monitor = await create()
    await poll()
    await monitor.get('select').setValue('approve')
    choice.reject(new Error('Choice could not be submitted'))
    await flushPromises()
    old.resolve(groups(true))
    await flushPromises()
    expect(details).toHaveBeenCalledTimes(3)
    expect(monitor.get('select').attributes('disabled')).toBeUndefined()
    await monitor.get('select').setValue('approve')
    await flushPromises()
    expect(executeChoice).toHaveBeenCalledTimes(2)
    expect(monitor.find('select').exists()).toBe(false)
  })

  it('shows a delayed error and recovers on the next ordinary poll', async () => {
    summaries.mockResolvedValueOnce(response([summary()]))
    const pending = deferred<ReturnType<typeof groups>>()
    details.mockImplementationOnce(() => pending.promise).mockResolvedValue(groups())
    const monitor = await create()
    await poll()
    await poll()
    pending.reject(new Error('Slow failure'))
    await flushPromises()
    expect(monitor.find('.monitor-job-groups-warning').exists()).toBe(true)
    expect(details).toHaveBeenCalledTimes(1)
    await poll()
    expect(monitor.find('.monitor-job-groups-warning').exists()).toBe(false)
    expect(monitor.findAll('.microservice-group')).toHaveLength(1)
  })
  it.each(['success', 'failure'] as const)('does not restart summary polling when choice completion is %s after unmount', async (outcome) => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    details.mockResolvedValue(groups(true))
    const choice = deferred<string>()
    vi.mocked(executeChoice).mockImplementationOnce(() => choice.promise)
    const monitor = await create()
    await monitor.get('select').setValue('approve')
    monitor.unmount()
    wrapper = undefined
    const callsBefore = summaries.mock.calls.length
    if (outcome === 'success') choice.resolve('ok')
    else choice.reject(new Error('Choice failed'))
    await flushPromises()
    await vi.advanceTimersByTimeAsync(16000)
    await flushPromises()
    expect(summaries).toHaveBeenCalledTimes(callsBefore)
  })

  it('does not restart summary polling when an accelerated summary finishes after unmount', async () => {
    summaries.mockResolvedValueOnce(response([summary('t-1', 1, true)]))
    details.mockResolvedValue(groups(true))
    vi.mocked(executeChoice).mockResolvedValue('ok')
    const monitor = await create()
    const pendingSummary = deferred<ReturnType<typeof response>>()
    summaries.mockImplementationOnce(() => pendingSummary.promise)
    await monitor.get('select').setValue('approve')
    await flushPromises()
    await vi.advanceTimersByTimeAsync(1000)
    await flushPromises()
    expect(summaries).toHaveBeenCalledTimes(2)
    monitor.unmount()
    wrapper = undefined
    pendingSummary.resolve(response([summary('t-1', 2, false)]))
    await flushPromises()
    await vi.advanceTimersByTimeAsync(15000)
    await flushPromises()
    expect(summaries).toHaveBeenCalledTimes(2)
  })
})

import { describe, it, expect, vi, beforeAll, beforeEach, afterAll, afterEach } from 'vitest'
import type { MockedFunction } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { useProcessingMonitor } from './useProcessingMonitor'
import type { MonitorConfigJson, MonitorUnitType } from './useProcessingMonitor'
import type { ProcessingUnit } from '@/shared/http/processing'
import type {
  TransferStatusesIfChangedOptions,
  TransferStatusesIfChangedResponse,
} from '@/shared/http/transfer'
import { TRANSFER_STARTED_EVENT } from '@/shared/events/monitor'

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

import { getTransferStatuses } from '@/shared/http/transfer'

const defaultConfig: MonitorConfigJson = {
  polling_interval: 10,
  microservices_help: {},
  job_statuses: {},
}

let visibilityState: DocumentVisibilityState = 'visible'
let originalVisibilityStateDescriptor: PropertyDescriptor | undefined
let originalHiddenDescriptor: PropertyDescriptor | undefined

const applyDocumentVisibilityState = (): void => {
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => visibilityState,
  })
  Object.defineProperty(document, 'hidden', {
    configurable: true,
    get: () => visibilityState === 'hidden',
  })
}

const setDocumentVisibility = (state: DocumentVisibilityState): void => {
  visibilityState = state
  applyDocumentVisibilityState()
  document.dispatchEvent(new Event('visibilitychange'))
}

const restoreDocumentVisibilityDescriptors = (): void => {
  if (originalVisibilityStateDescriptor) {
    Object.defineProperty(document, 'visibilityState', originalVisibilityStateDescriptor)
  } else {
    Reflect.deleteProperty(document, 'visibilityState')
  }
  if (originalHiddenDescriptor) {
    Object.defineProperty(document, 'hidden', originalHiddenDescriptor)
  } else {
    Reflect.deleteProperty(document, 'hidden')
  }
}

type ProcessingMonitorState = ReturnType<typeof useProcessingMonitor>

const mountMonitor = async (
  unitType: MonitorUnitType,
): Promise<{ wrapper: VueWrapper, monitor: ProcessingMonitorState }> => {
  let monitor: ReturnType<typeof useProcessingMonitor> | null = null
  const Harness = defineComponent({
    setup() {
      monitor = useProcessingMonitor(unitType, defaultConfig)
      return () => null
    },
  })

  const wrapper = mount(Harness)
  await flushPromises()

  if (!monitor) {
    throw new Error('Monitor composable failed to initialize in test harness.')
  }

  return { wrapper, monitor: monitor as ProcessingMonitorState }
}

describe('useProcessingMonitor', () => {
  beforeAll(() => {
    originalVisibilityStateDescriptor = Object.getOwnPropertyDescriptor(document, 'visibilityState')
    originalHiddenDescriptor = Object.getOwnPropertyDescriptor(document, 'hidden')
  })

  beforeEach(() => {
    vi.clearAllMocks()
    visibilityState = 'visible'
    applyDocumentVisibilityState()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  afterAll(() => {
    restoreDocumentVisibilityDescriptors()
  })

  it('uses changed-aware polling and skips unchanged payload updates', async () => {
    const mockGetTransferStatuses = vi.mocked(getTransferStatuses) as unknown as MockedFunction<(
      options: TransferStatusesIfChangedOptions,
    ) => Promise<TransferStatusesIfChangedResponse>>

    mockGetTransferStatuses
      .mockResolvedValueOnce({
        changed: true,
        raw: '{"objects":[{"uuid":"t-1"}],"mcp":true}',
        data: {
          objects: [{ uuid: 't-1', directory: 'Transfer-1', timestamp: 1, jobs: [] }],
          mcp: true,
        },
      })
      .mockResolvedValueOnce({
        changed: false,
        raw: '{"objects":[{"uuid":"t-1"}],"mcp":true}',
      })
      .mockResolvedValueOnce({
        changed: true,
        raw: '{"objects":[{"uuid":"t-2"}],"mcp":true}',
        data: {
          objects: [{ uuid: 't-2', directory: 'Transfer-2', timestamp: 2, jobs: [] }],
          mcp: true,
        },
      })

    const { wrapper, monitor } = await mountMonitor('Transfer')

    expect(getTransferStatuses).toHaveBeenNthCalledWith(1, { previousRaw: undefined })
    expect(monitor.units.value.map((unit: ProcessingUnit) => unit.uuid)).toEqual(['t-1'])

    await monitor.refresh()
    expect(getTransferStatuses).toHaveBeenNthCalledWith(2, {
      previousRaw: '{"objects":[{"uuid":"t-1"}],"mcp":true}',
    })
    expect(monitor.units.value.map((unit: ProcessingUnit) => unit.uuid)).toEqual(['t-1'])

    await monitor.refresh()
    expect(getTransferStatuses).toHaveBeenNthCalledWith(3, {
      previousRaw: '{"objects":[{"uuid":"t-1"}],"mcp":true}',
    })
    expect(monitor.units.value.map((unit: ProcessingUnit) => unit.uuid)).toEqual(['t-2'])

    wrapper.unmount()
  })

  it('pauses polling while hidden and resumes when visible', async () => {
    vi.useFakeTimers()

    const mockGetTransferStatuses = vi.mocked(getTransferStatuses) as unknown as MockedFunction<(
      options: TransferStatusesIfChangedOptions,
    ) => Promise<TransferStatusesIfChangedResponse>>
    mockGetTransferStatuses.mockResolvedValue({
      changed: true,
      raw: '{"objects":[],"mcp":true}',
      data: { objects: [], mcp: true },
    })

    const pollIntervalMs = defaultConfig.polling_interval * 1000
    const { wrapper } = await mountMonitor('Transfer')
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(pollIntervalMs)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    setDocumentVisibility('hidden')
    await flushPromises()

    await vi.advanceTimersByTimeAsync(pollIntervalMs * 3)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    setDocumentVisibility('visible')
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(3)

    await vi.advanceTimersByTimeAsync(pollIntervalMs)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(4)

    wrapper.unmount()
  })

  it('skips initial polling while hidden and starts after becoming visible', async () => {
    vi.useFakeTimers()
    setDocumentVisibility('hidden')

    const mockGetTransferStatuses = vi.mocked(getTransferStatuses) as unknown as MockedFunction<(
      options: TransferStatusesIfChangedOptions,
    ) => Promise<TransferStatusesIfChangedResponse>>
    mockGetTransferStatuses.mockResolvedValue({
      changed: true,
      raw: '{"objects":[],"mcp":true}',
      data: { objects: [], mcp: true },
    })

    const pollIntervalMs = defaultConfig.polling_interval * 1000
    const { wrapper } = await mountMonitor('Transfer')
    expect(getTransferStatuses).toHaveBeenCalledTimes(0)

    await vi.advanceTimersByTimeAsync(pollIntervalMs * 2)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(0)

    setDocumentVisibility('visible')
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(pollIntervalMs)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })

  it('accelerates next poll to one second when requested', async () => {
    vi.useFakeTimers()

    const mockGetTransferStatuses = vi.mocked(getTransferStatuses) as unknown as MockedFunction<(
      options: TransferStatusesIfChangedOptions,
    ) => Promise<TransferStatusesIfChangedResponse>>
    mockGetTransferStatuses.mockResolvedValue({
      changed: true,
      raw: '{"objects":[],"mcp":true}',
      data: { objects: [], mcp: true },
    })

    const pollIntervalMs = defaultConfig.polling_interval * 1000
    const { wrapper, monitor } = await mountMonitor('Transfer')
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(5000)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    monitor.requestSoonerPoll()

    await vi.advanceTimersByTimeAsync(999)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(pollIntervalMs)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(3)

    wrapper.unmount()
  })

  it('reschedules near-imminent polling to one second and keeps only one accelerated timer', async () => {
    vi.useFakeTimers()

    const mockGetTransferStatuses = vi.mocked(getTransferStatuses) as unknown as MockedFunction<(
      options: TransferStatusesIfChangedOptions,
    ) => Promise<TransferStatusesIfChangedResponse>>
    mockGetTransferStatuses.mockResolvedValue({
      changed: true,
      raw: '{"objects":[],"mcp":true}',
      data: { objects: [], mcp: true },
    })

    const { wrapper, monitor } = await mountMonitor('Transfer')
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(defaultConfig.polling_interval * 1000 - 500)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    monitor.requestSoonerPoll()

    await vi.advanceTimersByTimeAsync(500)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    monitor.requestSoonerPoll()

    await vi.advanceTimersByTimeAsync(999)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })

  it('accelerates polling when a transfer-started event is received', async () => {
    vi.useFakeTimers()

    const mockGetTransferStatuses = vi.mocked(getTransferStatuses) as unknown as MockedFunction<(
      options: TransferStatusesIfChangedOptions,
    ) => Promise<TransferStatusesIfChangedResponse>>
    mockGetTransferStatuses.mockResolvedValue({
      changed: true,
      raw: '{"objects":[],"mcp":true}',
      data: { objects: [], mcp: true },
    })

    const { wrapper } = await mountMonitor('Transfer')
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(5000)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    document.dispatchEvent(new CustomEvent(TRANSFER_STARTED_EVENT))

    await vi.advanceTimersByTimeAsync(999)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1)
    await flushPromises()
    expect(getTransferStatuses).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })
})

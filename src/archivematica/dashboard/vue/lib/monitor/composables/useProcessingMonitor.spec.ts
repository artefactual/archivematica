import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
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
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
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
})

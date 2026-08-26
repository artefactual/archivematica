import { useDocumentVisibility } from '@vueuse/core'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { getIngestSummaries } from '@/shared/http/ingest'
import { getTransferSummaries } from '@/shared/http/transfer'
import type {
  ProcessingJob,
  ProcessingStatusesResponse,
  ProcessingUnit,
  ProcessingUnitSummariesResponse,
} from '@/shared/http/processing'
import { TRANSFER_STARTED_EVENT } from '@/shared/events/monitor'

export type MonitorUnitType = 'Transfer' | 'SIP'

export type MonitorConfigJson = {
  polling_interval: number
  microservices_help: Record<string, string>
  job_statuses: Record<string, string>
}

export const getMonitorConfig = (scriptId: string): MonitorConfigJson => {
  const el = document.getElementById(scriptId)
  if (!(el instanceof HTMLScriptElement)) {
    throw new Error(`#${scriptId} not found or not a <script> tag.`)
  }
  const raw = el.textContent?.trim()
  if (!raw) {
    throw new Error(`#${scriptId} is empty.`)
  }
  try {
    return JSON.parse(raw) as MonitorConfigJson
  } catch {
    throw new Error(`Invalid JSON in #${scriptId}.`)
  }
}

const getPollingIntervalSeconds = (config: MonitorConfigJson): number => {
  const value = config.polling_interval
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return value
  }
  throw new Error('Invalid monitor config: "polling_interval" must be a positive number.')
}

export const useProcessingMonitor = (unitType: MonitorUnitType, config: MonitorConfigJson) => {
  let disposed = false
  const pollingIntervalSeconds = getPollingIntervalSeconds(config)
  const pollingIntervalMs = pollingIntervalSeconds * 1000
  const acceleratedPollingDelayMs = 1000
  const pollingIntervalTimer = ref<number | null>(null)
  const acceleratedPollingTimer = ref<number | null>(null)
  const documentVisibility = useDocumentVisibility()
  const unitsState = ref<ProcessingUnit[]>([])
  const loadingState = ref<boolean>(true)
  const errorState = ref<string | null>(null)
  const refreshVersionState = ref(0)
  // Opaque token used by changed-aware status fetches.
  const previousSummariesRaw = ref<string | null>(null)
  const isRefreshing = ref<boolean>(false)

  const fetchSummaries = async (): Promise<ProcessingStatusesResponse | {
    changed: boolean
    raw: string
    data?: ProcessingUnitSummariesResponse | ProcessingStatusesResponse
  }> => {
    const options = { previousRaw: previousSummariesRaw.value ?? undefined }
    return unitType === 'Transfer'
      ? getTransferSummaries(options)
      : getIngestSummaries(options)
  }

  const sortByTimestampDesc = <T extends { timestamp: number }>(items: T[]): T[] => {
    return [...items].sort((a, b) => b.timestamp - a.timestamp)
  }

  type IncomingProcessingUnit = Omit<ProcessingUnit, 'jobs'> & { jobs?: ProcessingJob[] }

  const upsertUnits = (incomingUnits: IncomingProcessingUnit[]): void => {
    // Keep row identity stable across polls so user interactions (expanded rows,
    // focused controls, pending choices) are less likely to be interrupted.
    const existingByUuid = new Map(unitsState.value.map(unit => [unit.uuid, unit]))
    const nextUnits: ProcessingUnit[] = []
    const sortedIncomingUnits = sortByTimestampDesc(incomingUnits)

    for (const incomingUnit of sortedIncomingUnits) {
      const existingUnit = existingByUuid.get(incomingUnit.uuid)
      const sortedJobs = incomingUnit.jobs
        ? sortByTimestampDesc(incomingUnit.jobs)
        : undefined
      if (!existingUnit) {
        nextUnits.push({
          ...incomingUnit,
          jobs: sortedJobs ?? [],
        })
        continue
      }

      existingUnit.directory = incomingUnit.directory
      existingUnit.timestamp = incomingUnit.timestamp
      existingUnit.active = incomingUnit.active
      existingUnit.access_system_id = incomingUnit.access_system_id
      existingUnit.processing_state = incomingUnit.processing_state
      existingUnit.started_at = incomingUnit.started_at
      existingUnit.status = incomingUnit.status
      existingUnit.has_awaiting_decision = incomingUnit.has_awaiting_decision
      existingUnit.awaiting_job_uuids = incomingUnit.awaiting_job_uuids
      if (sortedJobs !== undefined) {
        existingUnit.jobs = sortedJobs
      }
      nextUnits.push(existingUnit)
    }

    unitsState.value = nextUnits
  }

  const refresh = async (): Promise<void> => {
    if (disposed || isRefreshing.value) {
      return
    }
    isRefreshing.value = true

    try {
      const response = await fetchSummaries()

      // Changed-aware HTTP path: skip DOM/reactivity work if payload is unchanged.
      if ('changed' in response) {
        previousSummariesRaw.value = response.raw
        if (!response.changed) {
          errorState.value = null
          refreshVersionState.value += 1
          return
        }
        const data = response.data
        if (!data) {
          errorState.value = null
          return
        }
        const objects = 'results' in data
          ? data.results
          : Array.isArray(data.objects) ? data.objects : []
        upsertUnits(objects)
        errorState.value = null
        refreshVersionState.value += 1
        return
      }

      const objects = Array.isArray(response.objects) ? response.objects : []
      upsertUnits(objects)
      errorState.value = null
      refreshVersionState.value += 1
    } catch (error) {
      errorState.value = error instanceof Error ? error.message : 'Failed to load monitor status.'
    } finally {
      loadingState.value = false
      isRefreshing.value = false
    }
  }

  const units = computed<ProcessingUnit[]>(() => {
    return unitsState.value
  })
  const loading = computed<boolean>(() => loadingState.value)
  const error = computed<string | null>(() => errorState.value)
  const refreshVersion = computed<number>(() => refreshVersionState.value)

  const stopPolling = (): void => {
    if (pollingIntervalTimer.value !== null) {
      window.clearInterval(pollingIntervalTimer.value)
      pollingIntervalTimer.value = null
    }
    if (acceleratedPollingTimer.value !== null) {
      window.clearTimeout(acceleratedPollingTimer.value)
      acceleratedPollingTimer.value = null
    }
  }

  const startPolling = (): void => {
    if (
      disposed
      || pollingIntervalTimer.value !== null
      || acceleratedPollingTimer.value !== null
      || documentVisibility.value !== 'visible'
    ) {
      return
    }
    pollingIntervalTimer.value = window.setInterval(() => {
      void refresh()
    }, pollingIntervalMs)
  }

  const requestSoonerPoll = (): void => {
    if (disposed || documentVisibility.value !== 'visible') {
      return
    }

    if (pollingIntervalTimer.value !== null) {
      window.clearInterval(pollingIntervalTimer.value)
      pollingIntervalTimer.value = null
    }
    if (acceleratedPollingTimer.value !== null) {
      window.clearTimeout(acceleratedPollingTimer.value)
      acceleratedPollingTimer.value = null
    }

    acceleratedPollingTimer.value = window.setTimeout(() => {
      acceleratedPollingTimer.value = null
      void refresh().finally(() => {
        startPolling()
      })
    }, acceleratedPollingDelayMs)
  }

  const handleTransferStarted = (): void => {
    requestSoonerPoll()
  }

  watch(documentVisibility, (visibility) => {
    if (visibility !== 'visible') {
      stopPolling()
      return
    }
    void refresh()
    startPolling()
  })

  onMounted(() => {
    if (documentVisibility.value === 'visible') {
      void refresh()
    }
    startPolling()
    document.addEventListener(TRANSFER_STARTED_EVENT, handleTransferStarted)
  })

  onUnmounted(() => {
    disposed = true
    document.removeEventListener(TRANSFER_STARTED_EVENT, handleTransferStarted)
    stopPolling()
  })

  return {
    units,
    loading,
    error,
    refreshVersion,
    pollingIntervalSeconds,
    refresh,
    requestSoonerPoll,
  }
}

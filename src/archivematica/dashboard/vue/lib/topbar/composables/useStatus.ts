import { getCurrentScope, onScopeDispose, reactive, readonly } from 'vue'
import { getStatus, toHttpErrorInfo } from '@/shared/http'
import type { StatusResponse } from '@/shared/http'

type StatusCounts = StatusResponse

type StatusState = {
  counts: StatusCounts
  connected: boolean | null
  loading: boolean
  error: string | null
  lastUpdated: number | null
}

const state = reactive<StatusState>({
  counts: { sip: 0, transfer: 0, dip: 0 },
  connected: null,
  loading: false,
  error: null,
  lastUpdated: null,
})

// Single interval handle for status polling.
let pollHandle: number | null = null
// Prevent overlapping requests; drop concurrent pollOnce calls.
let inFlight = false
// Delay loading indicator to avoid flicker on fast responses.
let loadingTimer: number | null = null
const LOADING_DELAY_MS = 150

const normalizeCount = (value: unknown): number => {
  const parsed = typeof value === 'string' ? Number.parseInt(value, 10) : Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

const pollOnce = async (): Promise<void> => {
  if (inFlight) return
  inFlight = true
  if (loadingTimer !== null) {
    window.clearTimeout(loadingTimer)
  }
  loadingTimer = window.setTimeout(() => {
    state.loading = true
  }, LOADING_DELAY_MS)

  try {
    const data = await getStatus()
    state.counts = {
      sip: normalizeCount(data.sip),
      transfer: normalizeCount(data.transfer),
      dip: normalizeCount(data.dip),
    }
    state.connected = true
    state.error = null
    state.lastUpdated = Date.now()
  } catch (error) {
    state.connected = false
    const info = toHttpErrorInfo(error)
    if (info) {
      state.error = `Status request failed: ${info.status}`
    } else {
      state.error = error instanceof Error ? error.message : 'Status request failed'
    }
  } finally {
    if (loadingTimer !== null) {
      window.clearTimeout(loadingTimer)
      loadingTimer = null
    }
    state.loading = false
    inFlight = false
  }
}

// Assumes a single owner; if multiple components manage polling, add ref-counting.
const startPolling = (intervalMs = 5000): void => {
  if (pollHandle !== null) return

  pollOnce()
  pollHandle = window.setInterval(pollOnce, intervalMs)
}

const stopPolling = (): void => {
  if (pollHandle === null) return

  window.clearInterval(pollHandle)
  pollHandle = null
}

export function useStatus() {
  if (getCurrentScope()) {
    startPolling()
    onScopeDispose(stopPolling)
  }

  return {
    state: readonly(state),
    pollOnce,
    startPolling,
    stopPolling,
  }
}

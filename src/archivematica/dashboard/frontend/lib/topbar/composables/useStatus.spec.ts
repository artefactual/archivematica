import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getStatus } from '@/shared/http'
import type { StatusResponse } from '@/shared/http'

vi.mock('@/shared/http', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/shared/http')>()
  return {
    ...actual,
    getStatus: vi.fn(),
  }
})

describe('useStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('updates counts and connection state on success', async () => {
    vi.mocked(getStatus).mockResolvedValueOnce({ sip: 1, transfer: 2, dip: 3 })

    const { useStatus } = await import('@/topbar/composables/useStatus')
    const { state, pollOnce } = useStatus()

    await pollOnce()

    expect(state.counts).toEqual({ sip: 1, transfer: 2, dip: 3 })
    expect(state.connected).toBe(true)
    expect(state.error).toBeNull()
  })

  it('marks connection as failed on error response', async () => {
    vi.mocked(getStatus).mockRejectedValueOnce(new Error('Status request failed: 500'))

    const { useStatus } = await import('@/topbar/composables/useStatus')
    const { state, pollOnce } = useStatus()

    await pollOnce()

    expect(state.connected).toBe(false)
    expect(state.error).toContain('Status request failed')
  })

  it('delays loading indicator to avoid flicker', async () => {
    let resolveFetch: ((value: StatusResponse) => void) | undefined
    vi.mocked(getStatus).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve
        }) as Promise<StatusResponse>,
    )

    const { useStatus } = await import('@/topbar/composables/useStatus')
    const { state, pollOnce } = useStatus()

    const pollPromise = pollOnce()

    expect(state.loading).toBe(false)

    await vi.advanceTimersByTimeAsync(149)
    expect(state.loading).toBe(false)

    await vi.advanceTimersByTimeAsync(1)
    expect(state.loading).toBe(true)

    resolveFetch?.({ sip: 0, transfer: 0, dip: 0 })

    await pollPromise

    expect(state.loading).toBe(false)
  })
})

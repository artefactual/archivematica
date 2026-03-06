import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { useStatus } from '@/topbar/composables/useStatus'

vi.mock('@/topbar/composables/useStatus', () => ({
  useStatus: vi.fn(),
}))

describe('NavCounts', () => {
  beforeEach(() => {
    vi.mocked(useStatus).mockReturnValue({
      state: {
        counts: { sip: 1, transfer: 2, dip: 3 },
        connected: true,
        loading: false,
        error: null,
        lastUpdated: null,
      },
      pollOnce: vi.fn() as unknown as () => Promise<void>,
      startPolling: vi.fn() as unknown as (intervalMs?: number) => void,
      stopPolling: vi.fn() as unknown as () => void,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
  })

  it('teleports counts into transfer and ingest targets', async () => {
    const nav = document.createElement('ul')
    nav.className = 'nav'
    const transferLi = document.createElement('li')
    const transferLink = document.createElement('a')
    transferLink.setAttribute('href', '/transfer/')
    transferLink.classList.add('nav-transfer')
    transferLi.appendChild(transferLink)
    const ingestLi = document.createElement('li')
    const ingestLink = document.createElement('a')
    ingestLink.setAttribute('href', '/ingest/')
    ingestLink.classList.add('nav-ingest')
    ingestLi.appendChild(ingestLink)
    nav.appendChild(transferLi)
    nav.appendChild(ingestLi)
    document.body.appendChild(nav)

    const { default: NavCounts } = await import('@/topbar/components/NavCounts.vue')

    const wrapper = mount(NavCounts, {
      attachTo: document.body,
    })
    await wrapper.vm.$nextTick()

    expect(transferLink.querySelector('span')?.textContent).toBe('2')
    expect(ingestLink.querySelector('span')?.textContent).toBe('4')

    wrapper.unmount()
  })

  it('renders nothing when targets are missing', async () => {
    const { default: NavCounts } = await import('@/topbar/components/NavCounts.vue')

    const wrapper = mount(NavCounts, {
      attachTo: document.body,
    })
    await wrapper.vm.$nextTick()
    expect(document.querySelector('a.nav-transfer span')).toBeNull()
    expect(document.querySelector('a.nav-ingest span')).toBeNull()

    wrapper.unmount()
  })
})

import { beforeAll, beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { init } from './index'

let fixtureRoot: HTMLDivElement

const rect = (overrides: Partial<DOMRect> = {}): DOMRect => {
  return {
    x: overrides.x ?? 0,
    y: overrides.y ?? 0,
    width: overrides.width ?? 0,
    height: overrides.height ?? 0,
    top: overrides.top ?? 0,
    right: overrides.right ?? 0,
    bottom: overrides.bottom ?? 0,
    left: overrides.left ?? 0,
    toJSON: () => ({}),
  } as DOMRect
}

const renderTarget = (attrs = ''): HTMLElement => {
  fixtureRoot.innerHTML = `<a data-toggle="popover" href="#" ${attrs}>Target</a>`
  return fixtureRoot.querySelector('[data-toggle="popover"]') as HTMLElement
}

const mouse = (element: Element, type: string): boolean => {
  return element.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true }))
}

describe('popover feature', () => {
  beforeAll(() => {
    document.body.innerHTML = ''
    fixtureRoot = document.createElement('div')
    fixtureRoot.id = 'popover-test-fixture'
    document.body.appendChild(fixtureRoot)
  })

  beforeEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
    fixtureRoot.innerHTML = ''
    document.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('shows a shared popover with title and sanitized text content on hover', () => {
    const target = renderTarget('title="Location" data-content="Path %hidden% value"')

    init()
    mouse(target, 'mouseenter')

    const popover = document.querySelector('.popover') as HTMLElement
    const title = popover.querySelector('.popover-title') as HTMLElement
    const content = popover.querySelector('.popover-content') as HTMLElement

    expect(popover.style.display).toBe('block')
    expect(popover.classList.contains('in')).toBe(true)
    expect(title.textContent).toBe('Location')
    expect(content.textContent).toBe('Path  value')
    expect(target.getAttribute('title')).toBeNull()
    expect(target.getAttribute('data-original-title')).toBe('Location')
  })

  it('prevents navigation for hash-only popover links', () => {
    const target = renderTarget('title="Location" data-content="x"')

    init()

    expect(mouse(target, 'click')).toBe(false)
  })

  it('hides after the leave timeout', () => {
    vi.useFakeTimers()
    const target = renderTarget('title="Location" data-content="x"')

    init()
    mouse(target, 'mouseenter')

    const popover = document.querySelector('.popover') as HTMLElement
    expect(popover.style.display).toBe('block')

    mouse(target, 'mouseleave')
    vi.advanceTimersByTime(49)
    expect(popover.style.display).toBe('block')

    vi.advanceTimersByTime(1)
    expect(popover.style.display).toBe('none')
  })

  it('hides on outside click after being shown', () => {
    const target = renderTarget('title="Location" data-content="x"')

    init()
    mouse(target, 'focus')

    const popover = document.querySelector('.popover') as HTMLElement
    expect(popover.style.display).toBe('block')

    mouse(document.body, 'click')
    expect(popover.style.display).toBe('none')
  })

  it('stays hidden when both title and content are empty', () => {
    const target = renderTarget('')

    init()
    mouse(target, 'mouseenter')

    const popover = document.querySelector('.popover') as HTMLElement | null
    expect(popover?.style.display ?? 'none').toBe('none')
  })

  it('flips placement to bottom when there is not enough space above', () => {
    Object.defineProperty(document.documentElement, 'clientWidth', {
      configurable: true,
      value: 240,
    })
    Object.defineProperty(window, 'pageXOffset', {
      configurable: true,
      value: 0,
    })
    Object.defineProperty(window, 'pageYOffset', {
      configurable: true,
      value: 10,
    })

    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function (this: HTMLElement) {
      if (this.getAttribute('data-toggle') === 'popover') {
        return rect({ left: 60, top: 5, width: 40, height: 20, right: 100, bottom: 25 })
      }
      if (this.classList.contains('popover')) {
        return rect({ left: 0, top: 0, width: 120, height: 60, right: 120, bottom: 60 })
      }
      return rect()
    })

    const target = renderTarget('title="Location" data-content="x"')

    init()
    mouse(target, 'mouseenter')

    const popover = document.querySelector('.popover') as HTMLElement
    expect(popover.classList.contains('bottom')).toBe(true)
    expect(popover.classList.contains('top')).toBe(false)
    expect(popover.style.top).toBe('35px')
  })
})

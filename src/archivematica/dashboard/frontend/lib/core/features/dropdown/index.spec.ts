import { beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { init } from './index'

const buildFixture = () => {
  document.body.innerHTML = `
    <div class="dropdown" id="user-menu">
      <a class="dropdown-toggle" data-toggle="dropdown" href="#" aria-expanded="false">User</a>
      <ul class="dropdown-menu" role="menu">
        <li><a href="#profile">Profile</a></li>
        <li class="disabled"><a href="#disabled">Disabled</a></li>
        <li><a href="#settings">Settings</a></li>
        <li>
          <form>
            <button type="button" id="logout-button">Log out</button>
          </form>
        </li>
      </ul>
    </div>
  `

  const root = document.getElementById('user-menu') as HTMLElement
  const toggle = root.querySelector('[data-toggle="dropdown"]') as HTMLElement
  const links = Array.from(root.querySelectorAll<HTMLAnchorElement>('.dropdown-menu a'))
  const logoutButton = document.getElementById('logout-button') as HTMLButtonElement

  for (const link of links) {
    Object.defineProperty(link, 'offsetParent', {
      configurable: true,
      get: () => document.body,
    })
  }
  Object.defineProperty(logoutButton, 'offsetParent', {
    configurable: true,
    get: () => document.body,
  })

  return { root, toggle, links, logoutButton }
}

const click = (element: Element): boolean => {
  return element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }))
}

const keydown = (element: Element, key: string): boolean => {
  return element.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }))
}

describe('dropdown feature', () => {
  beforeAll(() => {
    init()
  })

  beforeEach(() => {
    document.body.innerHTML = ''
  })

  it('opens and closes on toggle click', () => {
    const { root, toggle } = buildFixture()

    expect(click(toggle)).toBe(false)
    expect(root.classList.contains('open')).toBe(true)
    expect(toggle.getAttribute('aria-expanded')).toBe('true')

    expect(click(toggle)).toBe(false)
    expect(root.classList.contains('open')).toBe(false)
    expect(toggle.getAttribute('aria-expanded')).toBe('false')
  })

  it('keeps the dropdown open for clicks inside a nested form', () => {
    const { root, toggle, logoutButton } = buildFixture()

    click(toggle)
    expect(root.classList.contains('open')).toBe(true)

    expect(click(logoutButton)).toBe(true)
    expect(root.classList.contains('open')).toBe(true)
  })

  it('closes when clicking outside the dropdown', () => {
    const { root, toggle } = buildFixture()

    click(toggle)
    click(document.body)
    expect(root.classList.contains('open')).toBe(false)
  })

  it('opens with ArrowDown and focuses the first visible menu item', () => {
    const { root, toggle, links } = buildFixture()

    expect(keydown(toggle, 'ArrowDown')).toBe(false)
    expect(root.classList.contains('open')).toBe(true)
    expect(document.activeElement).toBe(links[0])
  })

  it('closes with Escape and returns focus to the toggle', () => {
    const { root, toggle, links } = buildFixture()

    click(toggle)
    links[2]?.focus()
    expect(document.activeElement).toBe(links[2])

    expect(keydown(links[2] as HTMLAnchorElement, 'Escape')).toBe(false)
    expect(root.classList.contains('open')).toBe(false)
    expect(document.activeElement).toBe(toggle)
  })

  it('moves arrow-key focus across non-link menu controls', () => {
    const { toggle, links, logoutButton } = buildFixture()

    click(toggle)
    links[2]?.focus()
    expect(document.activeElement).toBe(links[2])

    expect(keydown(links[2] as HTMLAnchorElement, 'ArrowDown')).toBe(false)
    expect(document.activeElement).toBe(logoutButton)

    expect(keydown(logoutButton, 'ArrowUp')).toBe(false)
    expect(document.activeElement).toBe(links[2])
  })

  it('opens only once on Space keydown for the toggle', () => {
    const { root, toggle } = buildFixture()

    expect(keydown(toggle, ' ')).toBe(false)
    expect(root.classList.contains('open')).toBe(true)

    expect(keydown(toggle, ' ')).toBe(false)
    expect(root.classList.contains('open')).toBe(true)
  })

  it('does not swallow Space on native form controls inside an open dropdown', () => {
    const { root, toggle, logoutButton } = buildFixture()

    click(toggle)
    logoutButton.focus()

    expect(keydown(logoutButton, ' ')).toBe(true)
    expect(root.classList.contains('open')).toBe(true)
  })

  it('ignores disabled toggles', () => {
    const { root, toggle } = buildFixture()
    toggle.setAttribute('disabled', 'disabled')

    expect(click(toggle)).toBe(true)
    expect(root.classList.contains('open')).toBe(false)
  })
})

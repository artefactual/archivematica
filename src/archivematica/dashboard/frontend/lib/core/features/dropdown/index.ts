const TOGGLE_SELECTOR = '[data-toggle="dropdown"]'
const MENU_ITEM_SELECTOR = [
  '.dropdown-menu li:not(.disabled) a',
  '.dropdown-menu li:not(.disabled) button',
  '.dropdown-menu li:not(.disabled) input:not([type="hidden"])',
  '.dropdown-menu li:not(.disabled) select',
  '.dropdown-menu li:not(.disabled) textarea',
  '.dropdown-menu li:not(.disabled) [role="menuitem"]',
].join(', ')
const OPEN_CLASS = 'open'

const isDisabled = (element: HTMLElement): boolean => {
  return element.classList.contains('disabled') || element.hasAttribute('disabled')
}

const resolveDropdownRoot = (toggle: HTMLElement): HTMLElement | null => {
  const dataTarget = toggle.getAttribute('data-target')
  const href = toggle.getAttribute('href')
  const selector = dataTarget?.startsWith('#')
    ? dataTarget
    : href?.startsWith('#')
      ? href
      : null

  if (selector && selector !== '#') {
    const target = document.querySelector<HTMLElement>(selector)
    if (target) return target
  }

  return toggle.closest<HTMLElement>('.dropdown')
}

const getToggleForRoot = (root: HTMLElement): HTMLElement | null => {
  return root.querySelector<HTMLElement>(TOGGLE_SELECTOR)
}

const closeDropdown = (root: HTMLElement): void => {
  if (!root.classList.contains(OPEN_CLASS)) return

  const toggle = getToggleForRoot(root)
  root.classList.remove(OPEN_CLASS)
  toggle?.setAttribute('aria-expanded', 'false')
}

const closeAllDropdowns = (exceptRoot?: HTMLElement): void => {
  document.querySelectorAll<HTMLElement>('.dropdown.open').forEach((root) => {
    if (exceptRoot && root === exceptRoot) return
    closeDropdown(root)
  })
}

const focusNextMenuItem = (root: HTMLElement, direction: 1 | -1): void => {
  const items = Array.from(
    root.querySelectorAll<HTMLElement>(
      MENU_ITEM_SELECTOR,
    ),
  ).filter(item => item.offsetParent !== null && !isDisabled(item))

  if (!items.length) return

  const activeElement = document.activeElement
  const currentIndex = items.findIndex(item => item === activeElement)
  const nextIndex
    = currentIndex === -1
      ? direction === 1
        ? 0
        : items.length - 1
      : Math.min(items.length - 1, Math.max(0, currentIndex + direction))

  items[nextIndex]?.focus()
}

const openDropdown = (root: HTMLElement, toggle: HTMLElement): void => {
  root.classList.add(OPEN_CLASS)
  toggle.setAttribute('aria-expanded', 'true')
  toggle.focus()
}

const onDocumentClick = (event: MouseEvent): void => {
  if (event.button === 2) return

  const target = event.target
  if (!(target instanceof Element)) {
    closeAllDropdowns()
    return
  }

  const toggle = target.closest<HTMLElement>(TOGGLE_SELECTOR)
  if (toggle) {
    if (isDisabled(toggle)) return
    const root = resolveDropdownRoot(toggle)
    if (!root) return

    const isOpen = root.classList.contains(OPEN_CLASS)
    closeAllDropdowns()

    event.preventDefault()
    if (!isOpen) {
      openDropdown(root, toggle)
    }
    return
  }

  const openRoot = target.closest<HTMLElement>('.dropdown.open')
  if (!openRoot) {
    closeAllDropdowns()
    return
  }

  if (
    /^(INPUT|TEXTAREA)$/i.test((target as HTMLElement).tagName)
    && openRoot.contains(target)
  ) {
    return
  }

  if (target.closest('.dropdown form') && openRoot.contains(target)) {
    return
  }

  closeAllDropdowns()
}

const onDocumentKeydown = (event: KeyboardEvent): void => {
  const target = event.target
  if (!(target instanceof Element)) return

  const toggle = target.closest<HTMLElement>(TOGGLE_SELECTOR)
  const menu = target.closest<HTMLElement>('.dropdown-menu')
  const root = (toggle && resolveDropdownRoot(toggle)) ?? menu?.closest<HTMLElement>('.dropdown')
  if (!root) return

  if (/^(INPUT|TEXTAREA)$/i.test((target as HTMLElement).tagName)) return

  const key = event.key
  if (!['ArrowUp', 'ArrowDown', 'Escape', ' ', 'Spacebar'].includes(key)) return

  const rootToggle = getToggleForRoot(root)
  if (!rootToggle || isDisabled(rootToggle)) return

  const isSpaceKey = key === ' ' || key === 'Spacebar'
  const isSpaceOnToggle = isSpaceKey && target === rootToggle
  const menuItemLink = target.closest<HTMLAnchorElement>('.dropdown-menu a')

  // Let native controls inside dropdown forms (e.g. logout buttons) keep their
  // default Space key behavior.
  if (isSpaceKey && !isSpaceOnToggle && !menuItemLink) return

  event.preventDefault()
  event.stopPropagation()

  const isOpen = root.classList.contains(OPEN_CLASS)
  if (isSpaceOnToggle) {
    if (!isOpen) {
      openDropdown(root, rootToggle)
    }
    return
  }

  if (!isOpen && key !== 'Escape') {
    openDropdown(root, rootToggle)
  }

  if (key === 'Escape') {
    if (isOpen) {
      closeDropdown(root)
      rootToggle.focus()
    }
    return
  }

  if (key === 'ArrowDown') {
    focusNextMenuItem(root, 1)
    return
  }

  if (key === 'ArrowUp') {
    focusNextMenuItem(root, -1)
    return
  }
}

let initialized = false

export const init = (): void => {
  if (initialized) return
  initialized = true

  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onDocumentKeydown)
}

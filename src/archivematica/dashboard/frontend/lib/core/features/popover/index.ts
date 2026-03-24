const TARGET_SELECTOR = '[data-toggle="popover"]'
const TOP_CLASS = 'top'
const BOTTOM_CLASS = 'bottom'
const VISIBLE_CLASS = 'in'

type PopoverTarget = HTMLElement

let popoverEl: HTMLDivElement | null = null
let popoverTitleEl: HTMLHeadingElement | null = null
let popoverContentEl: HTMLDivElement | null = null
let activeTarget: PopoverTarget | null = null
let hideTimer: number | null = null
let initialized = false

const getPopoverElements = (): {
  popover: HTMLDivElement
  title: HTMLHeadingElement
  content: HTMLDivElement
} => {
  if (popoverEl && popoverTitleEl && popoverContentEl) {
    return { popover: popoverEl, title: popoverTitleEl, content: popoverContentEl }
  }

  const popover = document.createElement('div')
  popover.className = `popover fade ${TOP_CLASS}`
  popover.setAttribute('role', 'tooltip')
  popover.style.display = 'none'

  const arrow = document.createElement('div')
  arrow.className = 'arrow'
  popover.appendChild(arrow)

  const title = document.createElement('h3')
  title.className = 'popover-title'
  popover.appendChild(title)

  const content = document.createElement('div')
  content.className = 'popover-content'
  popover.appendChild(content)

  document.body.appendChild(popover)

  popoverEl = popover
  popoverTitleEl = title
  popoverContentEl = content
  return { popover, title, content }
}

const clearHideTimer = (): void => {
  if (hideTimer === null) return
  window.clearTimeout(hideTimer)
  hideTimer = null
}

const getSanitizedPopoverContent = (target: PopoverTarget): string => {
  const raw = target.getAttribute('data-content') ?? ''
  return raw.replace(/%[^%]*%/g, '')
}

const getPopoverTitle = (target: PopoverTarget): string => {
  return target.getAttribute('data-original-title')
    ?? target.getAttribute('title')
    ?? ''
}

const positionPopover = (target: PopoverTarget): void => {
  const popover = popoverEl
  if (!popover) return

  const targetRect = target.getBoundingClientRect()
  const popRect = popover.getBoundingClientRect()

  const scrollX = window.pageXOffset
  const scrollY = window.pageYOffset
  const viewportWidth = document.documentElement.clientWidth

  const targetCenterX = targetRect.left + targetRect.width / 2
  let left = scrollX + targetCenterX - popRect.width / 2

  const minLeft = scrollX + 8
  const maxLeft = scrollX + viewportWidth - popRect.width - 8
  left = Math.min(Math.max(left, minLeft), Math.max(minLeft, maxLeft))

  const topCandidate = scrollY + targetRect.top - popRect.height
  const shouldUseBottom = topCandidate < scrollY

  popover.classList.remove(TOP_CLASS, BOTTOM_CLASS)
  if (shouldUseBottom) {
    popover.classList.add(BOTTOM_CLASS)
    popover.style.top = `${scrollY + targetRect.bottom}px`
  } else {
    popover.classList.add(TOP_CLASS)
    popover.style.top = `${topCandidate}px`
  }
  popover.style.left = `${left}px`
}

const hidePopoverNow = (): void => {
  clearHideTimer()
  activeTarget = null

  if (!popoverEl) return
  popoverEl.classList.remove(VISIBLE_CLASS)
  popoverEl.style.display = 'none'
}

const scheduleHidePopover = (): void => {
  clearHideTimer()
  hideTimer = window.setTimeout(() => {
    hidePopoverNow()
  }, 50)
}

const showPopover = (target: PopoverTarget): void => {
  clearHideTimer()
  activeTarget = target

  const contentText = getSanitizedPopoverContent(target)
  const titleText = getPopoverTitle(target)
  if (!contentText && !titleText) {
    hidePopoverNow()
    return
  }

  const { popover, title, content } = getPopoverElements()

  title.textContent = titleText
  title.style.display = titleText ? '' : 'none'
  content.textContent = contentText

  popover.style.display = 'block'
  popover.classList.remove(VISIBLE_CLASS)
  positionPopover(target)
  popover.classList.add(VISIBLE_CLASS)
}

const onPointerEnter = (event: Event): void => {
  const target = event.currentTarget
  if (!(target instanceof HTMLElement)) return
  showPopover(target)
}

const onPointerLeave = (): void => {
  scheduleHidePopover()
}

const onFocus = (event: FocusEvent): void => {
  const target = event.currentTarget
  if (!(target instanceof HTMLElement)) return
  showPopover(target)
}

const onBlur = (): void => {
  scheduleHidePopover()
}

const onClick = (event: MouseEvent): void => {
  const target = event.currentTarget
  if (!(target instanceof HTMLElement)) return
  if (target.matches('a[href="#"]')) {
    event.preventDefault()
  }
}

const onDocumentScrollOrResize = (): void => {
  if (!activeTarget || !popoverEl || popoverEl.style.display === 'none') return
  positionPopover(activeTarget)
}

const onDocumentClick = (event: MouseEvent): void => {
  const target = event.target
  if (!(target instanceof Element)) return

  if (target.closest(TARGET_SELECTOR)) return
  if (popoverEl && target.closest('.popover') === popoverEl) return
  hidePopoverNow()
}

const prepareNativeTitle = (element: HTMLElement): void => {
  const title = element.getAttribute('title')
  if (!title) return
  element.setAttribute('data-original-title', title)
  element.removeAttribute('title')
}

const bindTarget = (element: HTMLElement): void => {
  if (element.dataset.amPopoverBound === 'true') return
  element.dataset.amPopoverBound = 'true'

  prepareNativeTitle(element)
  element.addEventListener('mouseenter', onPointerEnter)
  element.addEventListener('mouseleave', onPointerLeave)
  element.addEventListener('focus', onFocus)
  element.addEventListener('blur', onBlur)
  element.addEventListener('click', onClick)
}

export const init = (): void => {
  document.querySelectorAll<HTMLElement>(TARGET_SELECTOR).forEach(bindTarget)

  if (initialized) return
  initialized = true

  document.addEventListener('click', onDocumentClick)
  window.addEventListener('scroll', onDocumentScrollOrResize, true)
  window.addEventListener('resize', onDocumentScrollOrResize)
}

type TabRoot = ParentNode & {
  querySelector<E extends Element = Element>(selectors: string): E | null
  querySelectorAll<E extends Element = Element>(selectors: string): NodeListOf<E>
}

const TAB_SELECTOR = 'a[href^="#"], [data-target^="#"]'

const findTabLink = (
  tabContainer: HTMLElement,
  root: TabRoot,
  selector: string,
): HTMLAnchorElement | null => {
  const tabLink = tabContainer.querySelector<HTMLAnchorElement>(
    `a[href="${selector}"], [data-target="${selector}"]`,
  )
  if (!tabLink || !getTabPane(tabLink, root)) return null
  return tabLink
}

const getLinkTargetSelector = (tabLink: HTMLElement): string | null => {
  const dataTarget = tabLink.getAttribute('data-target')
  if (dataTarget?.startsWith('#')) {
    return dataTarget
  }
  const href = tabLink.getAttribute('href')
  if (href?.startsWith('#')) {
    return href
  }
  return null
}

const isTabLink = (element: Element): element is HTMLAnchorElement => {
  if (!(element instanceof HTMLAnchorElement)) return false
  return element.matches(TAB_SELECTOR)
}

const getTabPane = (tabLink: HTMLElement, root: TabRoot): HTMLElement | null => {
  const selector = getLinkTargetSelector(tabLink)
  if (!selector) return null
  return root.querySelector<HTMLElement>(selector)
}

const getTabItem = (tabLink: HTMLElement): HTMLElement => {
  return tabLink.closest('li') ?? tabLink
}

const getTabContentRoot = (tabPane: HTMLElement): HTMLElement => {
  return tabPane.closest('.tab-content') ?? tabPane.parentElement ?? tabPane
}

const hideActiveTab = (root: TabRoot, nextTabLink: HTMLElement): void => {
  const nextTabItem = getTabItem(nextTabLink)
  const tabList = nextTabItem.parentElement
  if (tabList) {
    const currentTab = tabList.querySelector<HTMLElement>('.active')
    currentTab?.classList.remove('active')
    currentTab?.querySelectorAll<HTMLElement>('.active').forEach((element) => {
      element.classList.remove('active')
    })
  }

  const nextPane = getTabPane(nextTabLink, root)
  if (!nextPane) return

  const tabContent = getTabContentRoot(nextPane)
  const currentPane = tabContent.querySelector<HTMLElement>('.tab-pane.active')
  if (currentPane) {
    currentPane.classList.remove('active', 'in')
  }
}

const showTab = (
  root: TabRoot,
  tabLink: HTMLElement,
): boolean => {
  const targetPane = getTabPane(tabLink, root)
  if (!targetPane) return false

  const tabItem = getTabItem(tabLink)
  if (tabItem.classList.contains('active')) return false

  hideActiveTab(root, tabLink)

  tabItem.classList.add('active')
  targetPane.classList.add('active')
  if (targetPane.classList.contains('fade')) {
    // Triggering layout here allows CSS fade transitions to animate.
    void targetPane.offsetWidth
    targetPane.classList.add('in')
  }

  return true
}

const resolveInitialSelection = (
  tabContainer: HTMLElement,
  root: TabRoot,
): HTMLAnchorElement | null => {
  const activeTabValue = tabContainer.getAttribute('data-active-tab')
  if (activeTabValue) {
    const normalized = activeTabValue.startsWith('#') ? activeTabValue : `#tab-${activeTabValue}`
    const activeLink = findTabLink(tabContainer, root, normalized)
    if (activeLink) return activeLink
  }

  const hash = window.location.hash
  if (hash.startsWith('#')) {
    const hashLink = findTabLink(tabContainer, root, hash)
    if (hashLink) return hashLink
  }

  return null
}

const addTabClickHandler = (tabContainer: HTMLElement, root: TabRoot): void => {
  tabContainer.addEventListener('click', (event) => {
    const eventTarget = event.target
    if (!(eventTarget instanceof Element)) return

    const tabLink = eventTarget.closest('a')
    if (!tabLink || !isTabLink(tabLink)) return

    if (!getTabPane(tabLink, root)) return
    event.preventDefault()
    showTab(root, tabLink)
  })
}

export type TabsController = Readonly<{
  activate: (tabSelector: string) => boolean
}>

export const initTabs = (
  tabContainer: HTMLElement,
  root: TabRoot = document,
): TabsController => {
  addTabClickHandler(tabContainer, root)

  const selectedLink = resolveInitialSelection(tabContainer, root)
  if (selectedLink) {
    showTab(root, selectedLink)
  }

  return {
    activate: (tabSelector: string): boolean => {
      const tabLink = tabContainer.querySelector<HTMLAnchorElement>(tabSelector)
      if (!tabLink || !getTabPane(tabLink, root)) return false
      return showTab(root, tabLink)
    },
  }
}

export const initTabsInDocument = (root: Document = document): TabsController[] => {
  return Array.from(
    root.querySelectorAll<HTMLElement>('.am-tabs-pane .nav-tabs, .am-tabs-pane .nav-pills, .tabs'),
  ).map(container => initTabs(container, root))
}

export const init = (): void => {
  initTabsInDocument()
}

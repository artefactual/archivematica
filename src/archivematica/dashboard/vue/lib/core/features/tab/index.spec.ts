import { describe, expect, it, beforeEach } from 'vitest'
import { initTabs, initTabsInDocument } from './index'

const buildFixture = () => {
  document.body.innerHTML = `
    <section class="am-tabs-pane">
      <ul class="nav nav-tabs tabs" data-active-tab="reingest">
        <li class="active"><a href="#tab-upload-dip" role="tab">Upload DIP</a></li>
        <li><a href="#tab-reingest" role="tab">Re-ingest</a></li>
        <li><a href="#tab-delete" role="tab">Delete</a></li>
      </ul>
      <div class="tab-content">
        <div class="tab-pane active" id="tab-upload-dip">Upload pane</div>
        <div class="tab-pane" id="tab-reingest">Reingest pane</div>
        <div class="tab-pane" id="tab-delete">Delete pane</div>
      </div>
    </section>
  `
}

describe('tab feature', () => {
  beforeEach(() => {
    window.location.hash = ''
    buildFixture()
  })

  it('activates the tab from data-active-tab on initialization', () => {
    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    initTabs(tabs as HTMLElement)

    expect(document.querySelector('a[href="#tab-reingest"]')?.parentElement?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-reingest')?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-upload-dip')?.classList.contains('active')).toBe(false)
  })

  it('activates the tab from location hash when data-active-tab is not set', () => {
    document.body.innerHTML = `
      <section class="am-tabs-pane">
        <ul class="nav nav-tabs tabs">
          <li class="active"><a href="#tab-upload-dip" role="tab">Upload DIP</a></li>
          <li><a href="#tab-reingest" role="tab">Re-ingest</a></li>
          <li><a href="#tab-delete" role="tab">Delete</a></li>
        </ul>
        <div class="tab-content">
          <div class="tab-pane active" id="tab-upload-dip">Upload pane</div>
          <div class="tab-pane" id="tab-reingest">Reingest pane</div>
          <div class="tab-pane" id="tab-delete">Delete pane</div>
        </div>
      </section>
    `
    window.location.hash = '#tab-delete'

    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    initTabs(tabs as HTMLElement)

    expect(document.querySelector('a[href="#tab-delete"]')?.parentElement?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-delete')?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-upload-dip')?.classList.contains('active')).toBe(false)
  })

  it('switches tabs on click', () => {
    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    initTabs(tabs as HTMLElement)

    const deleteLink = document.querySelector('a[href="#tab-delete"]') as HTMLAnchorElement
    deleteLink.click()

    expect(deleteLink.parentElement?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-delete')?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-reingest')?.classList.contains('active')).toBe(false)
  })

  it('supports imperative activation through the controller', () => {
    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    const controller = initTabs(tabs as HTMLElement)
    const changed = controller.activate('a[href="#tab-delete"]')

    expect(changed).toBe(true)
    expect(document.querySelector('a[href="#tab-delete"]')?.parentElement?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-delete')?.classList.contains('active')).toBe(true)
  })

  it('returns false for invalid or already active tab selections', () => {
    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    const controller = initTabs(tabs as HTMLElement)

    expect(controller.activate('a[href="#does-not-exist"]')).toBe(false)
    expect(controller.activate('a[href="#tab-reingest"]')).toBe(false)
  })

  it('supports data-target tab links', () => {
    document.body.innerHTML = `
      <section class="am-tabs-pane">
        <ul class="nav nav-tabs tabs">
          <li class="active"><a href="#tab-one">One</a></li>
          <li><a href="/ignored" data-target="#tab-two">Two</a></li>
        </ul>
        <div class="tab-content">
          <div class="tab-pane active" id="tab-one">One pane</div>
          <div class="tab-pane" id="tab-two">Two pane</div>
        </div>
      </section>
    `

    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    initTabs(tabs as HTMLElement)

    const secondLink = document.querySelector('a[data-target="#tab-two"]') as HTMLAnchorElement
    secondLink.click()

    expect(secondLink.parentElement?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-two')?.classList.contains('active')).toBe(true)
    expect(document.getElementById('tab-one')?.classList.contains('active')).toBe(false)
  })

  it('adds the Bootstrap fade "in" class when activating fade panes', () => {
    document.getElementById('tab-delete')?.classList.add('fade')

    const tabs = document.querySelector('.tabs')
    expect(tabs).not.toBeNull()
    initTabs(tabs as HTMLElement)

    const deleteLink = document.querySelector('a[href="#tab-delete"]') as HTMLAnchorElement
    deleteLink.click()

    expect(document.getElementById('tab-delete')?.classList.contains('in')).toBe(true)
  })

  it('discovers and initializes tab containers in document', () => {
    const controllers = initTabsInDocument()
    expect(controllers).toHaveLength(1)
    expect(document.querySelector('a[href="#tab-reingest"]')?.parentElement?.classList.contains('active')).toBe(true)
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18nMock } from '@/shared/i18n'
import App from './App.vue'
import type { MatcherBootstrapData, MatcherInitialMatch } from './types'

const { mockCreateArchivesSpacePair, mockDeleteArchivesSpacePair } = vi.hoisted(() => ({
  mockCreateArchivesSpacePair: vi.fn(),
  mockDeleteArchivesSpacePair: vi.fn(),
}))

vi.mock('@/shared/http', () => ({
  createArchivesSpacePair: mockCreateArchivesSpacePair,
  deleteArchivesSpacePair: mockDeleteArchivesSpacePair,
}))

const labels: MatcherBootstrapData['labels'] = {
  filterObjects: 'Filter objects',
  filterResources: 'Filter resources',
  pair: 'Pair',
  pairSelectedObjects: 'Pair selected objects',
  restartMatching: 'Restart matching',
  reviewMatches: 'Review matches',
  objects: 'Objects',
  resources: 'Resources',
  pairs: 'Pairs',
  selectAll: 'Select all',
  file: 'File',
  level: 'Level',
  title: 'Title',
  identifier: 'Identifier',
  dates: 'Dates',
  selectedResource: 'Selected resource',
  targetResource: 'Target resource',
  noneSelected: 'None',
  selectedObjects: 'Selected objects',
  deleteMatch: 'Delete match',
  noResourceSelected: 'No resource selected.',
  noObjectsSelected: 'No objects selected.',
  duplicateMatch: 'Already paired.',
  pairRequestFailed: 'Could not save pairing.',
  deleteRequestFailed: 'Could not delete pairing.',
  noPairsYet: 'No pairs yet.',
}

const makeProps = (initialMatches: MatcherInitialMatch[] = []): MatcherBootstrapData => ({
  dipUuid: 'dip-1',
  objectPaths: [
    { uuid: 'obj-1', path: 'folder/a.txt' },
    { uuid: 'obj-2', path: 'folder/b.txt' },
  ],
  resourceData: {
    id: 'resource-root',
    title: 'Resource root',
    identifier: 'R1',
    dates: '2000-2001',
    levelOfDescription: 'collection',
    children: [
      {
        id: 'component-1',
        title: 'Series 1',
        identifier: 'S1',
        dates: '2001',
        levelOfDescription: 'series',
        children: [],
      },
    ],
  },
  initialMatches,
  urls: {
    match: '/ingest/dip-1/upload/as/match/',
    review: '/ingest/dip-1/upload/as/review/',
    reset: '/ingest/dip-1/upload/as/reset/',
  },
  labels,
})

const mountMatcher = (initialMatches: MatcherInitialMatch[] = []) => {
  return mount(App, {
    props: makeProps(initialMatches),
    attachTo: document.body,
    global: {
      plugins: [createI18nMock()],
    },
  })
}

describe('ArchivesSpace matcher', () => {
  beforeEach(() => {
    mockCreateArchivesSpacePair.mockReset()
    mockDeleteArchivesSpacePair.mockReset()
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('keeps the Pair action disabled until both a resource and objects are selected', async () => {
    const wrapper = mountMatcher()
    const pairButton = wrapper.find('.as-matcher-toolbar-actions .btn-primary')

    expect(pairButton.attributes('disabled')).toBeDefined()

    await wrapper.find('.as-matcher-resource-row').trigger('click')
    expect(pairButton.attributes('disabled')).toBeDefined()

    await wrapper.find('.as-matcher-object-row input[type=\"checkbox\"]').setValue(true)
    expect(pairButton.attributes('disabled')).toBeUndefined()
    expect(mockCreateArchivesSpacePair).not.toHaveBeenCalled()
  })

  it('pairs selected objects to a selected resource and persists each match', async () => {
    mockCreateArchivesSpacePair.mockResolvedValue('created')

    const wrapper = mountMatcher()

    await wrapper.find('.as-matcher-resource-row').trigger('click')
    const firstCheckbox = wrapper.find('.as-matcher-object-row input[type="checkbox"]')
    await firstCheckbox.setValue(true)
    await wrapper.find('.as-matcher-toolbar-actions .btn-primary').trigger('click')
    await flushPromises()

    expect(mockCreateArchivesSpacePair).toHaveBeenCalledTimes(1)
    expect(mockCreateArchivesSpacePair).toHaveBeenCalledWith({
      dipUuid: 'dip-1',
      resourceId: 'resource-root',
      fileUuid: 'obj-1',
    })

    const pairRows = wrapper.findAll('tr.atk-matcher-match-item')
    expect(pairRows).toHaveLength(1)
    expect(pairRows[0]?.text()).toContain('folder/a.txt')

    const objectInputs = wrapper.findAll('.as-matcher-object-row input[type="checkbox"]')
    expect(objectInputs[0]?.attributes('disabled')).toBeDefined()
  })

  it('deletes an existing match and removes it from the pairs table', async () => {
    mockDeleteArchivesSpacePair.mockResolvedValue(undefined)

    const wrapper = mountMatcher([
      {
        resource_id: 'resource-root',
        file_uuid: 'obj-1',
        resource: {
          id: 'resource-root',
          title: 'Resource root',
          identifier: 'R1',
          dates: '2000-2001',
          levelOfDescription: 'collection',
          children: [],
        },
      },
    ])

    expect(wrapper.findAll('tr.atk-matcher-match-item')).toHaveLength(1)

    await wrapper.find('.as-matcher-actions-col button').trigger('click')
    await flushPromises()

    expect(mockDeleteArchivesSpacePair).toHaveBeenCalledTimes(1)
    expect(mockDeleteArchivesSpacePair).toHaveBeenCalledWith({
      dipUuid: 'dip-1',
      resourceId: 'resource-root',
      fileUuid: 'obj-1',
    })

    expect(wrapper.findAll('tr.atk-matcher-match-item')).toHaveLength(0)
    expect(wrapper.text()).toContain('No pairs yet.')
  })

  it('renders when ArchivesSpace returns children as false', () => {
    const wrapper = mount(App, {
      props: {
        ...makeProps(),
        resourceData: {
          id: 'resource-root',
          title: 'Resource root',
          identifier: 'R1',
          dates: '2000-2001',
          levelOfDescription: 'collection',
          children: false,
        },
      },
      global: {
        plugins: [createI18nMock()],
      },
    })

    expect(wrapper.find('.as-matcher').exists()).toBe(true)
    expect(wrapper.findAll('.as-matcher-resource-row')).toHaveLength(1)
  })
})

import { describe, expect, it } from 'vitest'
import { parseRowsFromParams, rowsToUrlParams } from './useQueryRows'

describe('parseRowsFromParams', () => {
  it('hydrates multiple rows from repeated URL params', () => {
    const params = new URLSearchParams(
      'query=first&field=&fieldName=&type=term&op=and&query=second&field=AIPUUID&fieldName=&type=string',
    )

    const rows = parseRowsFromParams(params)

    expect(rows).toHaveLength(2)
    expect(rows[0]).toMatchObject({
      op: '',
      query: 'first',
      field: '',
      fieldName: '',
      type: 'term',
    })
    expect(rows[1]).toMatchObject({
      op: 'and',
      query: 'second',
      field: 'AIPUUID',
      fieldName: '',
      type: 'string',
    })
    expect(rows[0]?.id).toContain('search-row-')
    expect(rows[1]?.id).toContain('search-row-')
  })
})

describe('rowsToUrlParams', () => {
  it('serializes rows with op excluded for the first row', () => {
    const params = rowsToUrlParams([
      { id: 'search-row-1', op: '', query: 'one', field: '', fieldName: '', type: 'term' },
      { id: 'search-row-2', op: 'or', query: 'two', field: 'FILEUUID', fieldName: '', type: 'term' },
    ])

    expect(params.getAll('op')).toEqual(['or'])
    expect(params.getAll('query')).toEqual(['one', 'two'])
  })
})

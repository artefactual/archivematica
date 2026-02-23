import { describe, expect, it } from 'vitest'
import {
  getFprFormatDetailUrl,
  getFprIdCommandCreateUrl,
  getFprFormatVersionEditUrl,
} from './fpr'

describe('fpr routes', () => {
  it('builds simple detail/edit routes', () => {
    expect(getFprFormatDetailUrl('pdf')).toContain('/fpr/format/pdf/')
    expect(getFprFormatVersionEditUrl('pdf', '1-7')).toContain('/fpr/format/pdf/1-7/edit/')
  })

  it('builds create routes with optional parent query', () => {
    expect(getFprIdCommandCreateUrl()).toContain('/fpr/idcommand/create/')
    expect(getFprIdCommandCreateUrl('tool-1')).toContain('/fpr/idcommand/create/?parent=tool-1')
  })
})

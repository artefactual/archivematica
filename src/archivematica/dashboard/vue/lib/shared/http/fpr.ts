import { createUrl } from './client'

export const getFprFormatCreateUrl = (): string => createUrl('/fpr/format/create/')
export const getFprFormatDetailUrl = (slug: string): string => createUrl(`/fpr/format/${slug}/`)
export const getFprFormatEditUrl = (slug: string): string => createUrl(`/fpr/format/${slug}/edit/`)

export const getFprFormatVersionCreateUrl = (formatSlug: string): string =>
  createUrl(`/fpr/format/${formatSlug}/create/`)
export const getFprFormatVersionDetailUrl = (formatSlug: string, slug: string): string =>
  createUrl(`/fpr/format/${formatSlug}/${slug}/`)
export const getFprFormatVersionEditUrl = (formatSlug: string, slug: string): string =>
  createUrl(`/fpr/format/${formatSlug}/${slug}/edit/`)
export const getFprFormatVersionDeleteUrl = (formatSlug: string, slug: string): string =>
  createUrl(`/fpr/format/${formatSlug}/${slug}/delete/`)

export const getFprFormatGroupCreateUrl = (): string => createUrl('/fpr/formatgroup/create/')
export const getFprFormatGroupEditUrl = (slug: string): string => createUrl(`/fpr/formatgroup/${slug}/`)
export const getFprFormatGroupDeleteUrl = (slug: string): string => createUrl(`/fpr/formatgroup/delete/${slug}/`)

export const getFprIdToolCreateUrl = (): string => createUrl('/fpr/idtool/create/')
export const getFprIdToolDetailUrl = (slug: string): string => createUrl(`/fpr/idtool/${slug}/`)
export const getFprIdToolEditUrl = (slug: string): string => createUrl(`/fpr/idtool/${slug}/edit/`)

export const getFprFpToolCreateUrl = (): string => createUrl('/fpr/fptool/create/')
export const getFprFpToolDetailUrl = (slug: string): string => createUrl(`/fpr/fptool/${slug}/`)
export const getFprFpToolEditUrl = (slug: string): string => createUrl(`/fpr/fptool/${slug}/edit/`)

export const getFprIdRuleCreateUrl = (): string => createUrl('/fpr/idrule/create/')
export const getFprIdRuleDetailUrl = (uuid: string): string => createUrl(`/fpr/idrule/${uuid}/`)
export const getFprIdRuleEditUrl = (uuid: string): string => createUrl(`/fpr/idrule/${uuid}/edit/`)
export const getFprIdRuleDeleteUrl = (uuid: string): string => createUrl(`/fpr/idrule/${uuid}/delete/`)

export const getFprIdCommandCreateUrl = (parentUuid?: string): string =>
  createUrl('/fpr/idcommand/create/', {
    query: parentUuid ? { parent: parentUuid } : undefined,
  })
export const getFprIdCommandDetailUrl = (uuid: string): string => createUrl(`/fpr/idcommand/${uuid}/`)
export const getFprIdCommandEditUrl = (uuid: string): string => createUrl(`/fpr/idcommand/${uuid}/edit/`)
export const getFprIdCommandDeleteUrl = (uuid: string): string => createUrl(`/fpr/idcommand/${uuid}/delete/`)

export const getFprFpRuleCreateUrl = (): string => createUrl('/fpr/fprule/create/')
export const getFprFpRuleDetailUrl = (uuid: string): string => createUrl(`/fpr/fprule/${uuid}/`)
export const getFprFpRuleEditUrl = (uuid: string): string => createUrl(`/fpr/fprule/${uuid}/edit/`)
export const getFprFpRuleDeleteUrl = (uuid: string): string => createUrl(`/fpr/fprule/${uuid}/delete/`)

export const getFprFpCommandCreateUrl = (parentUuid?: string): string =>
  createUrl('/fpr/fpcommand/create/', {
    query: parentUuid ? { parent: parentUuid } : undefined,
  })
export const getFprFpCommandDetailUrl = (uuid: string): string => createUrl(`/fpr/fpcommand/${uuid}/`)
export const getFprFpCommandEditUrl = (uuid: string): string => createUrl(`/fpr/fpcommand/${uuid}/edit/`)
export const getFprFpCommandDeleteUrl = (uuid: string): string => createUrl(`/fpr/fpcommand/${uuid}/delete/`)

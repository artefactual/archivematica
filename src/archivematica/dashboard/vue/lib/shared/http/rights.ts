import { createHttpClient } from './client'

export type RightsFormdataType
  = | 'rightsnote'
    | 'rightsrestriction'
    | 'licensenote'
    | 'statutenote'
    | 'copyrightnote'
    | 'copyrightdocumentationidentifier'
    | 'statutedocumentationidentifier'
    | 'licensedocumentationidentifier'
    | 'otherrightsdocumentationidentifier'
    | 'otherrightsnote'

// Endpoint types actively used by the current rights editor rewrite.
export const RIGHTS_EDITOR_FORMDATA_TYPES = {
  copyrightDocumentationIdentifier: 'copyrightdocumentationidentifier',
  copyrightNote: 'copyrightnote',
  statuteDocumentationIdentifier: 'statutedocumentationidentifier',
  statuteNote: 'statutenote',
  licenseDocumentationIdentifier: 'licensedocumentationidentifier',
  licenseNote: 'licensenote',
  otherRightsDocumentationIdentifier: 'otherrightsdocumentationidentifier',
  otherRightsNote: 'otherrightsnote',
  rightsRestriction: 'rightsrestriction',
  rightsNote: 'rightsnote',
} as const

export type RightsEditorFormdataType
  = typeof RIGHTS_EDITOR_FORMDATA_TYPES[keyof typeof RIGHTS_EDITOR_FORMDATA_TYPES]

export type RightsFormdataValues = Record<string, string>
type RightsFormdataPostValues = Record<string, string | number | null | undefined>

export type RightsFormdataRecord = {
  id: number
  values: RightsFormdataValues
}

export type RightsFormdataResponse = {
  results?: RightsFormdataRecord[]
  message?: string
  new_id?: number
}

const client = createHttpClient()

const toFormdataUrl = (type: RightsFormdataType, parentId: string | number): string =>
  `/formdata/${type}/${parentId}/`

const toDeleteUrl = (
  type: RightsFormdataType,
  parentId: string | number,
  recordId: string | number,
): string => `/formdata/${type}/${parentId}/${recordId}/`

const toBody = (values: RightsFormdataPostValues): URLSearchParams => {
  const body = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    body.set(key, String(value))
  })
  return body
}

export const listRightsFormdata = async (
  type: RightsFormdataType,
  parentId: string | number,
): Promise<RightsFormdataResponse> => {
  return client.getJson<RightsFormdataResponse>(toFormdataUrl(type, parentId), {
    strictJson: true,
  })
}

export const saveRightsFormdata = async (
  type: RightsFormdataType,
  parentId: string | number,
  values: RightsFormdataValues,
  id?: string | number,
): Promise<RightsFormdataResponse> => {
  return client.requestJson<RightsFormdataResponse>(toFormdataUrl(type, parentId), {
    method: 'POST',
    body: toBody({ ...values, ...(id !== undefined ? { id } : {}) }),
    strictJson: true,
  })
}

export const deleteRightsFormdata = async (
  type: RightsFormdataType,
  parentId: string | number,
  id: string | number,
): Promise<RightsFormdataResponse> => {
  return client.requestJson<RightsFormdataResponse>(toDeleteUrl(type, parentId, id), {
    method: 'DELETE',
    body: toBody({ id }),
    strictJson: true,
  })
}

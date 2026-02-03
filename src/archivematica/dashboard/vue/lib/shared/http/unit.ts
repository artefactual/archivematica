import { createHttpClient } from './client'
import { HttpError } from './client'
import { createUrl } from './client'

export type UnitType = 'transfer' | 'ingest'

export type UnitDeleteResponse = { removed: boolean | string[] }

const client = createHttpClient()

const parseDeleteResponse = (data: unknown): UnitDeleteResponse => {
  if (!data || typeof data !== 'object' || !('removed' in data)) {
    throw new Error('Expected "removed" field in delete response.')
  }
  const value = (data as { removed: unknown }).removed
  if (typeof value === 'boolean') {
    return { removed: value }
  }
  if (Array.isArray(value) && value.every(item => typeof item === 'string')) {
    return { removed: value }
  }
  throw new Error('Unexpected "removed" field type in delete response.')
}

const tryParseConflictResponse = (err: unknown): UnitDeleteResponse | null => {
  if (!(err instanceof HttpError)) return null
  if (err.status !== 409) return null

  const body = err.bodyJson
  if (body && typeof body === 'object' && 'removed' in body) {
    const value = (body as { removed: unknown }).removed
    if (typeof value === 'boolean') {
      return { removed: value }
    }
  }
  return null
}

export const deleteUnit = async (unitType: UnitType, unitUuid: string): Promise<UnitDeleteResponse> => {
  try {
    const data = await client.requestJson<unknown>(`/${unitType}/${unitUuid}/delete/`, {
      method: 'DELETE',
      strictJson: true,
    })
    return parseDeleteResponse(data)
  } catch (err) {
    const parsed = tryParseConflictResponse(err)
    if (parsed) return parsed
    throw err
  }
}

export const deleteCompletedUnits = async (unitType: UnitType): Promise<UnitDeleteResponse> => {
  const data = await client.requestJson<unknown>(`/${unitType}/delete/`, {
    method: 'DELETE',
    strictJson: true,
  })
  return parseDeleteResponse(data)
}

export const getUnitDetailUrl = (unitType: UnitType, unitUuid: string): string => {
  return createUrl(`/${unitType}/${unitUuid}/`)
}

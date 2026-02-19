import { loadArchivalStorageState, saveArchivalStorageState } from '@/shared/http'
import type { ModeColumn } from '../types'

const getDefaultVisibility = (columns: ModeColumn[]): Record<string, boolean> => {
  const visibility: Record<string, boolean> = {}
  columns.forEach((column) => {
    visibility[column.id] = column.defaultVisible
  })
  return visibility
}

export const loadColumnVisibility = async (
  tableName: string,
  columns: ModeColumn[],
): Promise<Record<string, boolean>> => {
  try {
    const state = await loadArchivalStorageState(tableName)
    const stateColumns = state.columns
    if (!stateColumns || stateColumns.length === 0) {
      return getDefaultVisibility(columns)
    }

    const visibility: Record<string, boolean> = {}
    columns.forEach((column, index) => {
      visibility[column.id] = stateColumns[index]?.visible ?? column.defaultVisible
    })

    return visibility
  } catch {
    return getDefaultVisibility(columns)
  }
}

export const saveColumnVisibility = async (
  tableName: string,
  columns: ModeColumn[],
  visibility: Record<string, boolean>,
): Promise<void> => {
  const payload = {
    columns: columns.map(column => ({ visible: visibility[column.id] ?? true })),
  }

  await saveArchivalStorageState(tableName, payload)
}

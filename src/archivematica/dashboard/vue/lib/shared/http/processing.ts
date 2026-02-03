export type ProcessingChoiceMap = Record<string, string>

export type ProcessingJob = {
  uuid: string
  type: string
  microservicegroup: string
  currentstep: number
  currentstep_label?: string
  timestamp: number
  choices?: ProcessingChoiceMap
  link_id?: string
  filename?: string
}

export type ProcessingUnit = {
  uuid: string
  directory: string
  timestamp: number
  active?: boolean
  access_system_id?: string | null
  jobs: ProcessingJob[]
}

export type ProcessingStatusObjects = ProcessingUnit[] | Record<string, never>

export type ProcessingStatusesResponse = {
  objects: ProcessingStatusObjects
  mcp: boolean
}

export type ProcessingChoiceMap = Record<string, string>

export const PROCESSING_UNIT_STATE = {
  waitingForProcessing: 'waiting_for_processing',
} as const

export type ProcessingUnitState
  = typeof PROCESSING_UNIT_STATE[keyof typeof PROCESSING_UNIT_STATE]

export type ProcessingJob = {
  key?: string
  uuid?: string
  type: string
  microservicegroup: string
  currentstep: number
  currentstep_label?: string
  timestamp: number
  produces_tasks: boolean
  choices?: ProcessingChoiceMap
  link_id?: string
  filename?: string
  count?: number
  first_timestamp?: number
}

export type ProcessingUnitStatus = {
  currentstep: number
  type: string
  microservicegroup: string
}

export type ProcessingUnit = {
  uuid: string
  directory: string
  timestamp: number
  active?: boolean
  access_system_id?: string | null
  processing_state?: ProcessingUnitState
  started_at?: number
  status?: ProcessingUnitStatus | null
  has_awaiting_decision?: boolean
  awaiting_job_uuids?: string[]
  jobs: ProcessingJob[]
}

export type ProcessingUnitSummary = Omit<ProcessingUnit, 'jobs'> & {
  awaiting_job_uuids: string[]
}

export type ProcessingJobGroup = {
  name: string
  jobs: ProcessingJob[]
}

export type ProcessingUnitSummariesResponse = {
  results: ProcessingUnitSummary[]
}

export type ProcessingJobGroupsResponse = {
  results: ProcessingJobGroup[]
}

export type ProcessingStatusObjects = ProcessingUnit[] | Record<string, never>

export type ProcessingStatusesResponse = {
  objects: ProcessingStatusObjects
  mcp: boolean
}

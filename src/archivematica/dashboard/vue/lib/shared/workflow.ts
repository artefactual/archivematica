// Processing monitor workflow semantics for the Vue monitor implementation.
//
// This module is the single source of truth for monitor-specific workflow
// rules that are not obvious from API payload structure alone. It centralizes
// the stable identifiers and rule tables used to derive status behavior and
// ingest-specific decisions.
//
// Public API is intentionally small and concrete. It exports identifier
// constants, rule definitions, and resolver helpers. Resolvers return semantic
// decisions (for example, "effective status", "preview type", or "special
// ingest choice behavior") and do not build URLs. Callers should use shared
// `http` helpers for navigation and endpoint details.

// Chain-link UUID constants used by ingest workflow matching.
const CHAIN_LINK_UUID = {
  approveNormalization: 'de909a42-c5b5-46e1-9985-c031b50e9d30',
  chooseConfigForArchivesSpaceDipUpload: 'a0db8294-f02a-4f49-a557-b1310a715ffc',
  uploadDipToArchivesSpace: '3572f844-5e69-4000-a24b-4e32d3487f82',
  uploadDipToAtom: '0fe9842f-9519-4067-a691-8a363132ae24',
  storeAip: '2d32235c-02d4-4686-88a6-96f4d6c7b1c3',
  moveToUploadedDipsDirectory: '2e31580d-1678-474b-83e5-a53d97d150f6',
} as const

// Union type for all known chain-link UUID values.
type ChainLinkUuid = (typeof CHAIN_LINK_UUID)[keyof typeof CHAIN_LINK_UUID]

// Known workflow job-type labels required by monitor rules.
const JOB_TYPE = {
  assignFileUuidsAndChecksums: 'Assign file UUIDs and checksums',
  moveToRejectedDirectory: 'Move to the rejected directory',
} as const

// Union type for known workflow job labels.
type KnownJobType = (typeof JOB_TYPE)[keyof typeof JOB_TYPE]

// Known microservice-group labels required by monitor rules.
const MICROSERVICE_GROUP = {
  rejectSip: 'Reject SIP',
  failedTransfer: 'Failed transfer',
} as const

// Union type for known microservice-group labels.
type KnownMicroserviceGroup
  = (typeof MICROSERVICE_GROUP)[keyof typeof MICROSERVICE_GROUP]

// Canonical workflow status codes used by monitor logic.
const STATUS_CODE_BY_NAME = {
  STATUS_UNKNOWN: 0,
  STATUS_AWAITING_DECISION: 1,
  STATUS_COMPLETED_SUCCESSFULLY: 2,
  STATUS_EXECUTING_COMMANDS: 3,
  STATUS_FAILED: 4,
  STATUS_REJECTED: 5,
} as const

// Union of status code names.
type MonitorStatusName = keyof typeof STATUS_CODE_BY_NAME

// Union of numeric status code values.
type MonitorStatusCode = (typeof STATUS_CODE_BY_NAME)[MonitorStatusName]

// Icon filenames used by monitor status rendering.
type StatusIconFile
  = | 'accept.png'
    | 'arrow_refresh.png'
    | 'bell.png'
    | 'cancel.png'
    | 'control_stop_blue.png'

// Status-to-icon lookup used by monitor row icon rendering.
const STATUS_ICON_BY_CODE: Readonly<Record<MonitorStatusCode, StatusIconFile>> = {
  [STATUS_CODE_BY_NAME.STATUS_UNKNOWN]: 'bell.png',
  [STATUS_CODE_BY_NAME.STATUS_AWAITING_DECISION]: 'bell.png',
  [STATUS_CODE_BY_NAME.STATUS_COMPLETED_SUCCESSFULLY]: 'accept.png',
  [STATUS_CODE_BY_NAME.STATUS_EXECUTING_COMMANDS]: 'arrow_refresh.png',
  [STATUS_CODE_BY_NAME.STATUS_FAILED]: 'cancel.png',
  [STATUS_CODE_BY_NAME.STATUS_REJECTED]: 'control_stop_blue.png',
}

// Status-to-background-color lookup used by job-row rendering.
const STATUS_COLOR_BY_CODE: Readonly<Record<MonitorStatusCode, string>> = {
  [STATUS_CODE_BY_NAME.STATUS_UNKNOWN]: '#d8f2dc',
  [STATUS_CODE_BY_NAME.STATUS_AWAITING_DECISION]: '#ffffff',
  [STATUS_CODE_BY_NAME.STATUS_COMPLETED_SUCCESSFULLY]: '#d8f2dc',
  [STATUS_CODE_BY_NAME.STATUS_EXECUTING_COMMANDS]: '#fedda7',
  [STATUS_CODE_BY_NAME.STATUS_FAILED]: '#f2d8d8',
  [STATUS_CODE_BY_NAME.STATUS_REJECTED]: '#f2d8d8',
}

// Minimal payload required to resolve status semantics.
type StatusProbe = {
  currentstep: number
  jobType?: string | null
  microserviceGroup?: string | null
}

// Declarative rule describing a status override condition.
type StatusOverrideRule = {
  id: string
  match: {
    jobType?: KnownJobType
    microserviceGroup?: KnownMicroserviceGroup
  }
  overrideStatus: MonitorStatusCode
}

const hasValue = (value: string | null | undefined): value is string =>
  typeof value === 'string' && value.length > 0

const hasText = (value: string | null | undefined): value is string =>
  hasValue(value) && value.trim().length > 0

const stringMatches = (
  value: string | null | undefined,
  expected: string | undefined,
): boolean => {
  if (!expected) return true
  return hasValue(value) && value === expected
}

const statusOverrideRuleMatches = (
  rule: StatusOverrideRule,
  probe: StatusProbe,
): boolean => {
  if (!stringMatches(probe.jobType, rule.match.jobType)) return false
  if (!stringMatches(probe.microserviceGroup, rule.match.microserviceGroup)) return false
  return true
}

// Ordered status override rules for rejected/failed edge cases.
const STATUS_OVERRIDE_RULES: readonly StatusOverrideRule[] = [
  {
    id: 'status.override.rejected.via_group',
    match: { microserviceGroup: MICROSERVICE_GROUP.rejectSip },
    overrideStatus: STATUS_CODE_BY_NAME.STATUS_REJECTED,
  },
  {
    id: 'status.override.rejected.via_job_type',
    match: { jobType: JOB_TYPE.moveToRejectedDirectory },
    overrideStatus: STATUS_CODE_BY_NAME.STATUS_REJECTED,
  },
  {
    id: 'status.override.failed.via_group',
    match: { microserviceGroup: MICROSERVICE_GROUP.failedTransfer },
    overrideStatus: STATUS_CODE_BY_NAME.STATUS_FAILED,
  },
] as const

// Resolves the effective status after applying override rules.
const resolveEffectiveStatus = (probe: StatusProbe): number => {
  let status = probe.currentstep
  for (const rule of STATUS_OVERRIDE_RULES) {
    if (statusOverrideRuleMatches(rule, probe)) {
      status = rule.overrideStatus
    }
  }
  return status
}

// Returns true when a status code is "awaiting decision".
const isAwaitingDecisionStatusCode = (statusCode: number): boolean =>
  statusCode === STATUS_CODE_BY_NAME.STATUS_AWAITING_DECISION

// Returns true when a job probe resolves to "awaiting decision".
const isAwaitingDecisionProbe = (probe: StatusProbe): boolean =>
  isAwaitingDecisionStatusCode(resolveEffectiveStatus(probe))

// Resolves a job-row background color from a raw status code.
const getStatusColorForCode = (statusCode: number): string =>
  STATUS_COLOR_BY_CODE[statusCode as MonitorStatusCode]
  ?? STATUS_COLOR_BY_CODE[STATUS_CODE_BY_NAME.STATUS_UNKNOWN]

// Resolves a job-row background color from a job probe.
const getStatusColorForJob = (probe: StatusProbe): string =>
  getStatusColorForCode(resolveEffectiveStatus(probe))

// Resolves an icon filename from a raw status code.
const getStatusIconForCode = (statusCode: number): StatusIconFile =>
  STATUS_ICON_BY_CODE[statusCode as MonitorStatusCode]
  ?? STATUS_ICON_BY_CODE[STATUS_CODE_BY_NAME.STATUS_COMPLETED_SUCCESSFULLY]

// Resolves an icon filename from a job probe.
const getStatusIconForJob = (probe: StatusProbe): StatusIconFile =>
  getStatusIconForCode(resolveEffectiveStatus(probe))

// Job type treated as the ingest-start marker in the start-time column.
const INGEST_START_TIME_MARKER_JOB_TYPE = JOB_TYPE.assignFileUuidsAndChecksums

// Predicate helper for ingest start-time marker detection.
const isIngestStartTimeMarkerJob = (jobType: string | null | undefined): boolean =>
  jobType === INGEST_START_TIME_MARKER_JOB_TYPE

// Supported ingest preview types for review-link behavior.
type IngestPreviewType = 'aip' | 'normalization' | 'dip'

// Declarative rule for when/how to expose ingest review links.
type ReviewLinkRule = {
  id: string
  linkId: ChainLinkUuid
  previewType: IngestPreviewType
  requiresAwaitingDecision: boolean
}

// Rules mapping link IDs to ingest preview behavior.
const REVIEW_LINK_RULES: readonly ReviewLinkRule[] = [
  {
    id: 'ingest.review_link.aip',
    linkId: CHAIN_LINK_UUID.storeAip,
    previewType: 'aip',
    requiresAwaitingDecision: true,
  },
  {
    id: 'ingest.review_link.normalization',
    linkId: CHAIN_LINK_UUID.approveNormalization,
    previewType: 'normalization',
    requiresAwaitingDecision: true,
  },
  {
    id: 'ingest.review_link.dip',
    linkId: CHAIN_LINK_UUID.moveToUploadedDipsDirectory,
    previewType: 'dip',
    requiresAwaitingDecision: false,
  },
] as const

// Runtime payload required to resolve ingest review-link behavior.
type ReviewLinkProbe = {
  linkId?: string | null
  currentstep: number
}

// Resolved ingest review-link decision for UI rendering.
type ReviewLinkResolution = {
  ruleId: string
  previewType: IngestPreviewType
}

// Resolves ingest review-link behavior for a single job.
const resolveIngestReviewLink = (
  probe: ReviewLinkProbe,
): ReviewLinkResolution | null => {
  if (!hasValue(probe.linkId)) return null

  const rule = REVIEW_LINK_RULES.find(candidate => candidate.linkId === probe.linkId)
  if (!rule) return null

  if (
    rule.requiresAwaitingDecision
    && !isAwaitingDecisionStatusCode(probe.currentstep)
  ) {
    return null
  }

  return {
    ruleId: rule.id,
    previewType: rule.previewType,
  }
}

// Ingest inline actions exposed from link IDs.
type IngestInlineActionKind = 'open_normalization_report' | 'open_as_mapping'

// Declarative rule for ingest inline actions.
type IngestInlineActionRule = {
  id: string
  linkId: ChainLinkUuid
  action: IngestInlineActionKind
}

// Rules mapping link IDs to ingest inline actions.
const INGEST_INLINE_ACTION_RULES: readonly IngestInlineActionRule[] = [
  {
    id: 'ingest.inline_action.normalization_report',
    linkId: CHAIN_LINK_UUID.approveNormalization,
    action: 'open_normalization_report',
  },
  {
    id: 'ingest.inline_action.archivesspace_mapping',
    linkId: CHAIN_LINK_UUID.chooseConfigForArchivesSpaceDipUpload,
    action: 'open_as_mapping',
  },
] as const

// Resolved ingest inline action entry for rendering.
type IngestInlineActionResolution = {
  ruleId: string
  action: IngestInlineActionKind
  openIn: 'new_tab'
}

// Resolves inline actions for a given link ID.
const resolveIngestInlineActions = (
  linkId: string | null | undefined,
): readonly IngestInlineActionResolution[] => {
  if (!hasValue(linkId)) return []

  return INGEST_INLINE_ACTION_RULES
    .filter(rule => rule.linkId === linkId)
    .map(rule => ({
      ruleId: rule.id,
      action: rule.action,
      openIn: 'new_tab' as const,
    }))
}

// Declarative rule for ingest choice handling.
type IngestChoiceRule = {
  id: string
  chainId: ChainLinkUuid
  behavior: 'redirect_to_as_mapping_page' | 'require_atom_target'
}

// Rules mapping selected chain IDs to ingest choice behaviors.
const INGEST_CHOICE_RULES: readonly IngestChoiceRule[] = [
  {
    id: 'ingest.choice.redirect_to_as_mapping_page',
    chainId: CHAIN_LINK_UUID.uploadDipToArchivesSpace,
    behavior: 'redirect_to_as_mapping_page',
  },
  {
    id: 'ingest.choice.require_atom_target',
    chainId: CHAIN_LINK_UUID.uploadDipToAtom,
    behavior: 'require_atom_target',
  },
] as const

// Runtime payload required to resolve ingest choice behavior.
type IngestChoiceProbe = {
  selectedChainId?: string | null
  accessSystemId?: string | null
}

// Resolved behavior for ingest choice submission.
type IngestChoiceResolution
  = | {
    kind: 'execute_immediately'
  }
  | {
    kind: 'redirect_to_as_mapping_page'
    ruleId: string
  }
  | {
    kind: 'require_atom_target'
    hasStoredTarget: boolean
    ruleId: string
  }

// Resolves ingest choice behavior (execute, redirect, or request target).
const resolveIngestChoiceBehavior = (
  probe: IngestChoiceProbe,
): IngestChoiceResolution => {
  const chainId = probe.selectedChainId
  if (!hasValue(chainId)) return { kind: 'execute_immediately' }

  const rule = INGEST_CHOICE_RULES.find(candidate => candidate.chainId === chainId)
  if (!rule) return { kind: 'execute_immediately' }

  if (rule.behavior === 'redirect_to_as_mapping_page') {
    return {
      kind: 'redirect_to_as_mapping_page',
      ruleId: rule.id,
    }
  }

  return {
    kind: 'require_atom_target',
    hasStoredTarget: hasText(probe.accessSystemId),
    ruleId: rule.id,
  }
}

export {
  STATUS_CODE_BY_NAME,
  isAwaitingDecisionProbe,
  getStatusColorForJob,
  getStatusIconForJob,
  isIngestStartTimeMarkerJob,
  resolveIngestReviewLink,
  resolveIngestInlineActions,
  resolveIngestChoiceBehavior,
}

export type {
  StatusProbe,
  ReviewLinkProbe,
  ReviewLinkResolution,
  IngestInlineActionResolution,
  IngestChoiceProbe,
  IngestChoiceResolution,
}

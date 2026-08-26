<script setup lang="ts">
import { useProcessingMonitor } from '@/monitor/composables'
import type { MonitorUnitType } from '@/monitor/composables'
import type { MonitorConfig } from '@/monitor/composables'
import { PROCESSING_UNIT_STATE } from '@/shared/http/processing'
import type { ProcessingJob, ProcessingUnit } from '@/shared/http/processing'
import {
  getUploadTarget,
  setUploadTarget,
  deleteCompletedUnits,
  deleteUnit,
  executeChoice,
  getIngestUploadAsUrl,
  getJobTasksUrl,
  getUnitDetailUrl,
  getUnitJobHistoryUrl,
  getIngestJobGroups,
  getTransferJobGroups,
} from '@/shared/http'
import type { UnitType } from '@/shared/http/unit'
import {
  isAwaitingDecisionProbe,
  resolveIngestChoiceBehavior,
  STATUS_CODE_BY_NAME,
} from '@/shared/workflow'
import { SilkDeleteIcon } from '@/shared/icons'
import ProcessMonitorConfirmDialog from './ProcessMonitorConfirmDialog.vue'
import ProcessMonitorUploadTargetDialog from './ProcessMonitorUploadTargetDialog.vue'
import ProcessMonitorUnit from './ProcessMonitorUnit.vue'
import { useBreakpoints } from '@vueuse/core'
import { useI18n } from 'vue-i18n'
import { computed, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  unitType: MonitorUnitType
  config: MonitorConfig
}>()

const { t } = useI18n()

const {
  units,
  loading,
  error,
  refresh,
  refreshVersion,
  requestSoonerPoll,
} = useProcessingMonitor(props.unitType, props.config)

// List of expanded units by UUID.
const expandedUnitUuids = ref<Record<string, boolean>>({})

// List of expanded job group keys by "unitUuid::groupName".
const expandedGroupKeys = ref<Record<string, boolean>>({})

// Keep mutations tied to the unit independently of refreshed Job objects.
const executingChoiceUnitUuids = ref<Record<string, string>>({})
const executingChoiceJobUuids = computed<Record<string, boolean>>(() =>
  Object.fromEntries(Object.keys(executingChoiceUnitUuids.value).map(uuid => [uuid, true])),
)
const resolvedChoiceJobUuids = ref<Record<string, string>>({})
let disposed = false
onUnmounted(() => {
  disposed = true
})

const unitHasExecutingChoice = (unitUuid: string): boolean =>
  Object.values(executingChoiceUnitUuids.value).includes(unitUuid)

const selectedChoicesByJobUuid = ref<Record<string, string>>({})

const jobIsAwaitingDecision = (job: ProcessingJob): boolean =>
  isAwaitingDecisionProbe({
    currentstep: job.currentstep,
    jobType: job.type,
    microserviceGroup: job.microservicegroup,
  })

const markChoiceResolved = (job: ProcessingJob): void => {
  if (jobIsAwaitingDecision(job)) {
    job.currentstep = STATUS_CODE_BY_NAME.STATUS_EXECUTING_COMMANDS
    job.currentstep_label = undefined
  }
  job.choices = undefined
}

const jobHasCurrentDecision = (unit: ProcessingUnit, job: ProcessingJob): boolean =>
  !!job.uuid
  && !resolvedChoiceJobUuids.value[job.uuid]
  && (unit.awaiting_job_uuids?.includes(job.uuid) ?? unit.has_awaiting_decision === undefined)

const isUnitExpandable = (unit: ProcessingUnit): boolean =>
  unit.processing_state !== PROCESSING_UNIT_STATE.waitingForProcessing

const isUnitExpanded = (unit: ProcessingUnit): boolean =>
  isUnitExpandable(unit) && expandedUnitUuids.value[unit.uuid] === true

const unitGroupRequestGenerations = ref<Record<string, number>>({})
const pendingUnitGroupReloadUuids = ref<Record<string, boolean>>({})

const invalidateUnitJobGroupsRequest = (unitUuid: string): void => {
  unitGroupRequestGenerations.value[unitUuid]
    = (unitGroupRequestGenerations.value[unitUuid] ?? 0) + 1
  delete pendingUnitGroupReloadUuids.value[unitUuid]
}

const toggleUnit = (unit: ProcessingUnit): void => {
  if (!isUnitExpandable(unit)) return
  const expanding = !isUnitExpanded(unit)
  for (const unitUuid of Object.keys(expandedUnitUuids.value)) {
    if (expandedUnitUuids.value[unitUuid] === true) {
      expandedUnitUuids.value[unitUuid] = false
      invalidateUnitJobGroupsRequest(unitUuid)
    }
  }
  expandedUnitUuids.value[unit.uuid] = expanding
  // Legacy embedded payloads already include Jobs. Summaries declare
  // has_awaiting_decision and need the per-unit lazy request.
  if (expanding && unit.has_awaiting_decision !== undefined) {
    void loadUnitJobGroups(unit.uuid, true)
  }
}

type JobGroup = {
  name: string
  jobs: ProcessingJob[]
}

const groupJobs = (jobs: ProcessingJob[]): JobGroup[] => {
  const groups = new Map<string, ProcessingJob[]>()
  for (const job of jobs) {
    const groupName = job.microservicegroup || ''
    if (!groups.has(groupName)) {
      groups.set(groupName, [])
    }
    const groupJobs = groups.get(groupName)
    if (groupJobs) {
      groupJobs.push(job)
    }
  }
  return Array.from(groups.entries()).map(([name, group]) => ({ name, jobs: group }))
}

const groupedJobsByUnitUuid = computed<Record<string, JobGroup[]>>(() => {
  return Object.fromEntries(units.value.map(unit => [unit.uuid, groupJobs(unit.jobs.map(job =>
    // Preserve raw details: a response may arrive before the summary that
    // confirms its new decision. History remains usable in either ordering.
    job.choices && !jobHasCurrentDecision(unit, job) ? { ...job, choices: undefined } : job,
  ))]))
})

const loadingUnitGroupUuids = ref<Record<string, boolean>>({})
const unitGroupErrorUuids = ref<Record<string, boolean>>({})

const loadUnitJobGroups = async (unitUuid: string, forceReload = false): Promise<void> => {
  if (disposed || unitHasExecutingChoice(unitUuid)) return
  if (loadingUnitGroupUuids.value[unitUuid]) {
    // Ordinary polling reuses the request already in progress. Reopening a
    // unit needs a fresh request after its former generation completes.
    if (forceReload) pendingUnitGroupReloadUuids.value[unitUuid] = true
    return
  }
  const requestGeneration = unitGroupRequestGenerations.value[unitUuid] ?? 0
  delete pendingUnitGroupReloadUuids.value[unitUuid]
  loadingUnitGroupUuids.value[unitUuid] = true
  try {
    const response = props.unitType === 'Transfer'
      ? await getTransferJobGroups(unitUuid)
      : await getIngestJobGroups(unitUuid)
    if (
      disposed
      || (unitGroupRequestGenerations.value[unitUuid] ?? 0) !== requestGeneration
    ) {
      return
    }
    delete unitGroupErrorUuids.value[unitUuid]
    const unit = units.value.find(candidate => candidate.uuid === unitUuid)
    if (unit) {
      unit.jobs = response.results.flatMap(group => group.jobs)
      // A successful choice supersedes even a subsequently fetched snapshot
      // while MCPServer is still persisting that Job's new status.
      for (const job of unit.jobs) {
        if (job.uuid && resolvedChoiceJobUuids.value[job.uuid]) {
          markChoiceResolved(job)
        }
      }
      for (const group of response.results) {
        const groupKey = `${unitUuid}::${group.name}`
        if (
          !(groupKey in expandedGroupKeys.value)
          && group.jobs.some(jobIsAwaitingDecision)
        ) {
          expandedGroupKeys.value[groupKey] = true
        }
        for (const job of group.jobs) {
          if (job.uuid && job.choices && jobHasCurrentDecision(unit, job) && !(job.uuid in selectedChoicesByJobUuid.value)) {
            selectedChoicesByJobUuid.value[job.uuid] = ''
          }
        }
      }
    }
  } catch {
    if (
      disposed
      || (unitGroupRequestGenerations.value[unitUuid] ?? 0) !== requestGeneration
    ) {
      return
    }
    // Keep the unit summary usable and retry on the next monitor poll.
    unitGroupErrorUuids.value[unitUuid] = true
  } finally {
    delete loadingUnitGroupUuids.value[unitUuid]
    const shouldReload = pendingUnitGroupReloadUuids.value[unitUuid] === true
      && !disposed
      && !unitHasExecutingChoice(unitUuid)
      && units.value.some(candidate => candidate.uuid === unitUuid && isUnitExpanded(candidate))
    delete pendingUnitGroupReloadUuids.value[unitUuid]
    if (shouldReload) {
      void loadUnitJobGroups(unitUuid)
    }
  }
}

const getUnitGroups = (unitUuid: string): JobGroup[] => {
  return groupedJobsByUnitUuid.value[unitUuid] ?? []
}

const getGroupKey = (unitUuid: string, groupName: string): string => {
  return `${unitUuid}::${groupName}`
}

const groupHasAwaitingDecision = (jobs: ProcessingJob[]): boolean => {
  return jobs.some(jobIsAwaitingDecision)
}

const isGroupExpanded = (unitUuid: string, groupName: string, jobs: ProcessingJob[]): boolean => {
  const key = getGroupKey(unitUuid, groupName)
  if (key in expandedGroupKeys.value) {
    return expandedGroupKeys.value[key] === true
  }
  return groupHasAwaitingDecision(jobs)
}

const toggleGroup = (unitUuid: string, groupName: string, jobs: ProcessingJob[]): void => {
  const key = getGroupKey(unitUuid, groupName)
  expandedGroupKeys.value[key] = !isGroupExpanded(unitUuid, groupName, jobs)
}

const isJobExecutingChoice = (jobUuid: string): boolean => {
  return executingChoiceJobUuids.value[jobUuid] !== undefined
}

const setSelectedJobChoice = (jobUuid: string, choice: string): void => {
  selectedChoicesByJobUuid.value[jobUuid] = choice
}

type ToggleGroupPayload = {
  unitUuid: string
  groupName: string
  jobs: ProcessingJob[]
}

type JobChoicePayload = {
  job: ProcessingJob
  choice: string
  unitUuid: string
}

type SelectedJobChoicePayload = {
  jobUuid: string
  choice: string
}

type AtomUploadPendingChoice = {
  job: ProcessingJob & { uuid: string }
  choice: string
  unitUuid: string
}

const breakpoints = useBreakpoints({
  bp1020: 1020,
  bp1200: 1200,
})
const isWlte1020 = breakpoints.smaller('bp1020')
const isWlte1200 = breakpoints.between('bp1020', 'bp1200')
const sipContainerClasses = computed(() => ({
  'w-lte-1020': isWlte1020.value,
  'w-lte-1200': isWlte1200.value,
}))

const unitPendingRemoval = ref<ProcessingUnit | null>(null)
const removeUnitPending = ref(false)
const removeAllDialogOpen = ref(false)
const removeAllPending = ref(false)

const uploadTargetDialogOpen = ref(false)
const uploadTargetDialogLoading = ref(false)
const uploadTargetDialogSubmitting = ref(false)
const uploadTargetDialogError = ref<string | null>(null)
const uploadTargetValue = ref('')
const uploadTargetPendingChoice = ref<AtomUploadPendingChoice | null>(null)

type RemoveAllMessageKeys = {
  noCompletedToRemove: string
  failedRemoveAllCompleted: string
}

// Metadata about monitor unit types that differs between Transfer and SIP.
const monitorUnitMeta = {
  Transfer: {
    apiUnitType: 'transfer',
    removeAllMessageKeys: {
      noCompletedToRemove: 'monitor.noCompletedToRemoveTransfer',
      failedRemoveAllCompleted: 'monitor.failedRemoveAllCompletedTransfer',
    },
  },
  SIP: {
    apiUnitType: 'ingest',
    removeAllMessageKeys: {
      noCompletedToRemove: 'monitor.noCompletedToRemoveSip',
      failedRemoveAllCompleted: 'monitor.failedRemoveAllCompletedSip',
    },
  },
} as const satisfies Record<
  MonitorUnitType,
  {
    // The unit type as used by some server endpoints, e.g.: `/${unitType}/${unitUuid}/`.
    apiUnitType: UnitType
    removeAllMessageKeys: RemoveAllMessageKeys
  }
>

watch(units, (nextUnits) => {
  const nextUnitUuids = new Set(nextUnits.map(unit => unit.uuid))
  for (const unitUuid of Object.keys(expandedUnitUuids.value)) {
    if (!nextUnitUuids.has(unitUuid)) {
      delete expandedUnitUuids.value[unitUuid]
      invalidateUnitJobGroupsRequest(unitUuid)
      delete unitGroupErrorUuids.value[unitUuid]
    }
  }

  const validGroupKeys = new Set(
    nextUnits.flatMap(unit => getUnitGroups(unit.uuid).map(group => getGroupKey(unit.uuid, group.name))),
  )
  for (const key of Object.keys(expandedGroupKeys.value)) {
    if (!validGroupKeys.has(key)) {
      delete expandedGroupKeys.value[key]
    }
  }

  const validJobUuids = new Set(
    nextUnits.flatMap(unit => unit.jobs.flatMap(job => job.uuid ? [job.uuid] : [])),
  )
  for (const [jobUuid, unitUuid] of Object.entries(resolvedChoiceJobUuids.value)) {
    if (!nextUnitUuids.has(unitUuid)) {
      delete resolvedChoiceJobUuids.value[jobUuid]
    }
  }
  for (const jobUuid of Object.keys(selectedChoicesByJobUuid.value)) {
    if (!validJobUuids.has(jobUuid)) {
      delete selectedChoicesByJobUuid.value[jobUuid]
    }
  }

  for (const unit of nextUnits) {
    if (!isUnitExpandable(unit)) {
      if (
        expandedUnitUuids.value[unit.uuid] === true
        || loadingUnitGroupUuids.value[unit.uuid] === true
      ) {
        invalidateUnitJobGroupsRequest(unit.uuid)
      }
      expandedUnitUuids.value[unit.uuid] = false
      delete unitGroupErrorUuids.value[unit.uuid]
    }
    const groups = getUnitGroups(unit.uuid)
    for (const group of groups) {
      const groupKey = getGroupKey(unit.uuid, group.name)
      if (!(groupKey in expandedGroupKeys.value) && groupHasAwaitingDecision(group.jobs)) {
        // Auto-opened groups stay open until user toggles them.
        expandedGroupKeys.value[groupKey] = true
      }
    }

    for (const job of unit.jobs) {
      if (job.uuid && resolvedChoiceJobUuids.value[job.uuid]) {
        markChoiceResolved(job)
      }
      if (job.uuid && job.choices && jobHasCurrentDecision(unit, job) && !(job.uuid in selectedChoicesByJobUuid.value)) {
        selectedChoicesByJobUuid.value[job.uuid] = ''
      }
      if (job.uuid && (!job.choices || !jobHasCurrentDecision(unit, job)) && job.uuid in selectedChoicesByJobUuid.value) {
        delete selectedChoicesByJobUuid.value[job.uuid]
      }
    }
  }
})

watch(refreshVersion, () => {
  for (const unit of units.value) {
    if (
      isUnitExpanded(unit)
      && unit.has_awaiting_decision !== undefined
    ) {
      void loadUnitJobGroups(unit.uuid)
    }
  }
})

const getApiUnitType = (): UnitType => monitorUnitMeta[props.unitType].apiUnitType
const getRemoveAllMessageKeys = (): RemoveAllMessageKeys => monitorUnitMeta[props.unitType].removeAllMessageKeys

const showTasks = (jobUuid: string): void => {
  window.open(getJobTasksUrl(jobUuid), 'output')
}

const showJobHistory = (payload: { unitUuid: string, linkId: string }): void => {
  window.open(getUnitJobHistoryUrl(getApiUnitType(), payload.unitUuid, payload.linkId), 'output')
}

const openPanel = (unitUuid: string): void => {
  window.location.href = getUnitDetailUrl(getApiUnitType(), unitUuid)
}

const getUnitAccessSystemId = (unitUuid: string): string | null => {
  const unit = units.value.find(candidate => candidate.uuid === unitUuid)
  return unit?.access_system_id ?? null
}

const getUnitByUuid = (unitUuid: string): ProcessingUnit | undefined => {
  return units.value.find(candidate => candidate.uuid === unitUuid)
}

const getCurrentDecisionJob = (unitUuid: string, jobUuid: string, choice: string): ProcessingJob | undefined => {
  if (disposed || isJobExecutingChoice(jobUuid)) return
  const unit = getUnitByUuid(unitUuid)
  const job = unit?.jobs.find(candidate => candidate.uuid === jobUuid)
  if (unit && job && jobHasCurrentDecision(unit, job) && Object.prototype.hasOwnProperty.call(job.choices ?? {}, choice)) {
    return job
  }
}

const executeMcpChoice = async (
  job: ProcessingJob,
  choice: string,
  unitUuid: string,
): Promise<boolean> => {
  if (!job.uuid || !getCurrentDecisionJob(unitUuid, job.uuid, choice)) return false
  const jobUuid = job.uuid
  executingChoiceUnitUuids.value[jobUuid] = unitUuid
  invalidateUnitJobGroupsRequest(unitUuid)
  try {
    await executeChoice({ uuid: jobUuid, choice })
    resolvedChoiceJobUuids.value[jobUuid] = unitUuid
    markChoiceResolved(job)
    // A summary may have replaced the object captured when the choice started.
    const currentJob = getUnitByUuid(unitUuid)?.jobs.find(candidate => candidate.uuid === jobUuid)
    if (currentJob) markChoiceResolved(currentJob)
    delete selectedChoicesByJobUuid.value[jobUuid]
    return true
  } catch {
    selectedChoicesByJobUuid.value[jobUuid] = ''
    return false
  } finally {
    delete executingChoiceUnitUuids.value[jobUuid]
    requestSoonerPoll()
    if (units.value.some(unit =>
      unit.uuid === unitUuid && isUnitExpanded(unit) && unit.has_awaiting_decision !== undefined,
    )) {
      void loadUnitJobGroups(unitUuid, true)
    }
  }
}

const executeAtomUploadChoice = async (
  payload: AtomUploadPendingChoice,
  target: string,
  options?: { preserveSelectionOnFailure?: boolean },
): Promise<boolean> => {
  if (!getCurrentDecisionJob(payload.unitUuid, payload.job.uuid, payload.choice)) return false
  try {
    const response = await setUploadTarget(payload.unitUuid, target)
    if (!response.ready) {
      if (options?.preserveSelectionOnFailure !== true) {
        selectedChoicesByJobUuid.value[payload.job.uuid] = ''
      }
      return false
    }

    const unit = getUnitByUuid(payload.unitUuid)
    if (unit) {
      unit.access_system_id = target
    }

    return await executeMcpChoice(payload.job, payload.choice, payload.unitUuid)
  } catch {
    if (options?.preserveSelectionOnFailure !== true) {
      selectedChoicesByJobUuid.value[payload.job.uuid] = ''
    }
    return false
  }
}

const closeUploadTargetDialog = (resetChoice: boolean): void => {
  if (resetChoice && uploadTargetPendingChoice.value) {
    selectedChoicesByJobUuid.value[uploadTargetPendingChoice.value.job.uuid] = ''
  }
  uploadTargetDialogOpen.value = false
  uploadTargetDialogLoading.value = false
  uploadTargetDialogSubmitting.value = false
  uploadTargetDialogError.value = null
  uploadTargetValue.value = ''
  uploadTargetPendingChoice.value = null
}

const openUploadTargetDialog = async (payload: AtomUploadPendingChoice): Promise<void> => {
  uploadTargetPendingChoice.value = payload
  uploadTargetDialogOpen.value = true
  uploadTargetDialogLoading.value = true
  uploadTargetDialogSubmitting.value = false
  uploadTargetDialogError.value = null
  uploadTargetValue.value = ''

  try {
    const response = await getUploadTarget(payload.unitUuid)
    if (response.target) {
      uploadTargetValue.value = response.target
    }
  } catch {
    // Legacy behavior tolerates prefill failures and still lets user submit.
  } finally {
    uploadTargetDialogLoading.value = false
  }
}

const onUploadTargetDialogOpenChange = (open: boolean): void => {
  if (open) {
    uploadTargetDialogOpen.value = true
    return
  }

  if (uploadTargetDialogSubmitting.value) {
    return
  }

  closeUploadTargetDialog(true)
}

const submitUploadTargetDialog = async (): Promise<void> => {
  if (!uploadTargetPendingChoice.value || uploadTargetDialogSubmitting.value) {
    return
  }

  const target = uploadTargetValue.value.trim()
  if (!target) {
    uploadTargetDialogError.value = t('monitor.uploadTargetRequired')
    return
  }

  const payload = uploadTargetPendingChoice.value
  uploadTargetDialogSubmitting.value = true
  uploadTargetDialogError.value = null

  const success = await executeAtomUploadChoice(payload, target, {
    preserveSelectionOnFailure: false,
  })
  if (success) {
    closeUploadTargetDialog(false)
    return
  }

  uploadTargetDialogSubmitting.value = false
  uploadTargetDialogError.value = t('monitor.uploadTargetFailed')
}

const executeJobChoice = async (
  job: ProcessingJob,
  choice: string,
  unitUuid: string,
): Promise<void> => {
  if (!job.uuid || !choice) {
    return
  }
  const currentJob = getCurrentDecisionJob(unitUuid, job.uuid, choice)
  if (!currentJob) return
  job = currentJob

  if (props.unitType === 'SIP') {
    const accessSystemId = getUnitAccessSystemId(unitUuid)
    const behavior = resolveIngestChoiceBehavior({
      selectedChainId: choice,
      accessSystemId,
    })

    if (behavior.kind === 'redirect_to_as_mapping_page') {
      window.location.assign(getIngestUploadAsUrl(unitUuid))
      return
    }

    if (behavior.kind === 'require_atom_target') {
      const payload: AtomUploadPendingChoice = {
        job: job as ProcessingJob & { uuid: string },
        choice,
        unitUuid,
      }
      if (behavior.hasStoredTarget && accessSystemId) {
        const success = await executeAtomUploadChoice(payload, accessSystemId, {
          preserveSelectionOnFailure: true,
        })
        if (!success) {
          window.alert(t('monitor.uploadTargetFailed'))
        }
        return
      }

      await openUploadTargetDialog(payload)
      return
    }
  }

  await executeMcpChoice(job, choice, unitUuid)
}

const onToggleGroup = (payload: ToggleGroupPayload): void => {
  toggleGroup(payload.unitUuid, payload.groupName, payload.jobs)
}

const onSetSelectedJobChoice = (payload: SelectedJobChoicePayload): void => {
  setSelectedJobChoice(payload.jobUuid, payload.choice)
}

const onExecuteJobChoice = (payload: JobChoicePayload): void => {
  void executeJobChoice(payload.job, payload.choice, payload.unitUuid)
}

const requestRemoveUnit = (unit: ProcessingUnit): void => {
  if (unit.active) {
    window.alert(
      props.unitType === 'Transfer'
        ? t('monitor.activeTransfersBlocked')
        : t('monitor.activeSipsBlocked'),
    )
    return
  }

  unitPendingRemoval.value = unit
}

const confirmRemoveUnit = async (): Promise<void> => {
  if (!unitPendingRemoval.value || removeUnitPending.value) {
    return
  }

  removeUnitPending.value = true
  try {
    await deleteUnit(getApiUnitType(), unitPendingRemoval.value.uuid)
    await new Promise(resolve => window.setTimeout(resolve, 250))
    await refresh()
    requestSoonerPoll()
    unitPendingRemoval.value = null
  } catch {
    window.alert(t('monitor.failedRemoveUnit'))
  } finally {
    removeUnitPending.value = false
  }
}

const requestRemoveAllUnits = (): void => {
  removeAllDialogOpen.value = true
}

const confirmRemoveAllUnits = async (): Promise<void> => {
  if (removeAllPending.value) {
    return
  }

  removeAllPending.value = true
  try {
    const response = await deleteCompletedUnits(getApiUnitType())
    const removed = response.removed
    const messageKeys = getRemoveAllMessageKeys()
    if (!Array.isArray(removed) || removed.length === 0) {
      window.alert(t(messageKeys.noCompletedToRemove))
    }
    await refresh()
    requestSoonerPoll()
    removeAllDialogOpen.value = false
  } catch {
    window.alert(t(getRemoveAllMessageKeys().failedRemoveAllCompleted))
  } finally {
    removeAllPending.value = false
  }
}

const removeUnitDescription = computed(() => {
  if (props.unitType === 'Transfer') {
    return t('monitor.removeUnitConfirmTransfer')
  }
  return t('monitor.removeUnitConfirmSip')
})

const removeUnitTitle = computed(() => {
  if (props.unitType === 'SIP') {
    return t('monitor.removeUnitTitleSip')
  }
  return t('monitor.remove')
})

const removeUnitDetails = computed(() => {
  if (!unitPendingRemoval.value) {
    return []
  }
  return [
    t('monitor.directoryWithValue', { value: unitPendingRemoval.value.directory }),
    t('monitor.uuidWithValue', { value: unitPendingRemoval.value.uuid }),
  ]
})

const removeAllDescription = computed(() => {
  if (props.unitType === 'Transfer') {
    return t('monitor.removeAllConfirmTransfer')
  }
  return t('monitor.removeAllConfirmSip')
})

const onRemoveUnitDialogOpenChange = (open: boolean): void => {
  if (!open && !removeUnitPending.value) {
    unitPendingRemoval.value = null
  }
}

const onRemoveAllDialogOpenChange = (open: boolean): void => {
  removeAllDialogOpen.value = open
}

const onUploadTargetValueChange = (value: string): void => {
  uploadTargetValue.value = value
}

const headerLabelKeysByUnitType = {
  Transfer: {
    directory: 'monitor.transfer',
    timestamp: 'monitor.transferStartTime',
  },
  SIP: {
    directory: 'monitor.submissionInformationPackage',
    timestamp: 'monitor.ingestStartTime',
  },
} as const satisfies Record<
  MonitorUnitType,
  {
    directory: string
    timestamp: string
  }
>

const headerLabels = computed(() => {
  const keys = headerLabelKeysByUnitType[props.unitType]
  return {
    directory: t(keys.directory),
    timestamp: t(keys.timestamp),
  }
})

const removeAllTitle = computed(() => t('monitor.removeAllCompleted'))
</script>

<template>
  <div
    id="sip-container"
    :class="sipContainerClasses"
  >
    <div id="sip-header">
      <div id="sip-header-directory">
        {{ headerLabels.directory }}
      </div>
      <div id="sip-header-uuid">
        {{ t('monitor.uuid') }}
      </div>
      <div id="sip-header-timestamp">
        {{ headerLabels.timestamp }}
      </div>
      <div class="monitor-header-actions">
        <a
          class="monitor-remove-all"
          href="#"
          :title="removeAllTitle"
          @click.prevent="requestRemoveAllUnits()"
        >
          <SilkDeleteIcon
            class="monitor-header-action-icon"
            aria-hidden="true"
            size="16"
            alt=""
          />
          <span aria-hidden="true">&nbsp;</span>
        </a>
      </div>
    </div>
    <div id="sip-body">
      <p
        v-if="loading"
        id="sip-loading"
      >
        {{ t('misc.loading') }}
      </p>
      <p
        v-else-if="error"
        id="sip-error"
      >
        {{ error }}
      </p>
      <div
        v-else
        id="sip-units"
      >
        <ProcessMonitorUnit
          v-for="unit in units"
          :key="unit.uuid"
          :unit="unit"
          :is-expandable="isUnitExpandable(unit)"
          :is-expanded="isUnitExpanded(unit)"
          :is-loading-job-groups="loadingUnitGroupUuids[unit.uuid] === true"
          :has-job-groups-error="unitGroupErrorUuids[unit.uuid] === true"
          :unit-groups="getUnitGroups(unit.uuid)"
          :expanded-group-keys="expandedGroupKeys"
          :executing-choice-job-uuids="executingChoiceJobUuids"
          :selected-choices-by-job-uuid="selectedChoicesByJobUuid"
          :microservices-help="config.microservices_help"
          :job-statuses="config.job_statuses"
          @toggle-unit="toggleUnit"
          @open-panel="openPanel"
          @remove-unit="requestRemoveUnit"
          @toggle-group="onToggleGroup"
          @show-tasks="showTasks"
          @show-job-history="showJobHistory"
          @set-selected-job-choice="onSetSelectedJobChoice"
          @execute-job-choice="onExecuteJobChoice"
        />
      </div>
    </div>
    <ProcessMonitorConfirmDialog
      :open="unitPendingRemoval !== null"
      :title="removeUnitTitle"
      :description="removeUnitDescription"
      :details="removeUnitDetails"
      :confirm-label="t('monitor.confirm')"
      :cancel-label="t('monitor.cancel')"
      :pending="removeUnitPending"
      @update:open="onRemoveUnitDialogOpenChange"
      @confirm="confirmRemoveUnit"
    />
    <ProcessMonitorConfirmDialog
      :open="removeAllDialogOpen"
      :title="t('monitor.removeAllCompleted')"
      :description="removeAllDescription"
      :confirm-label="t('monitor.confirm')"
      :cancel-label="t('monitor.cancel')"
      :pending="removeAllPending"
      @update:open="onRemoveAllDialogOpenChange"
      @confirm="confirmRemoveAllUnits"
    />
    <ProcessMonitorUploadTargetDialog
      :open="uploadTargetDialogOpen"
      :title="t('monitor.uploadDip')"
      :description="t('monitor.uploadDipPrompt')"
      :details="t('monitor.uploadDipAtomTargetHint')"
      :target="uploadTargetValue"
      :target-label="t('monitor.identifier')"
      :submit-label="t('monitor.upload')"
      :cancel-label="t('monitor.cancel')"
      :loading="uploadTargetDialogLoading"
      :submitting="uploadTargetDialogSubmitting"
      :error="uploadTargetDialogError"
      @update:open="onUploadTargetDialogOpenChange"
      @update:target="onUploadTargetValueChange"
      @submit="submitUploadTargetDialog"
      @cancel="closeUploadTargetDialog(true)"
    />
  </div>
</template>

<style scoped>
.monitor-header-actions > a > span {
  width: 1.2em;
  display: inline-block;
}

.monitor-header-actions > .monitor-remove-all {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}

.monitor-header-actions > .monitor-remove-all:hover,
.monitor-header-actions > .monitor-remove-all:focus {
  text-decoration: none;
}

.monitor-header-action-icon {
  display: block;
}
</style>

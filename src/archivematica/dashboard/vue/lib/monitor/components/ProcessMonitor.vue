<script setup lang="ts">
import { useProcessingMonitor } from '@/monitor/composables'
import type { MonitorUnitType } from '@/monitor/composables'
import type { MonitorConfig } from '@/monitor/composables'
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
} from '@/shared/http'
import type { UnitType } from '@/shared/http/unit'
import {
  isAwaitingDecisionProbe,
  resolveIngestChoiceBehavior,
  STATUS_CODE_BY_NAME,
} from '@/shared/workflow'
import { icons } from '@/shared/assets/icons'
import ProcessMonitorConfirmDialog from './ProcessMonitorConfirmDialog.vue'
import ProcessMonitorUploadTargetDialog from './ProcessMonitorUploadTargetDialog.vue'
import ProcessMonitorUnit from './ProcessMonitorUnit.vue'
import { useBreakpoints } from '@vueuse/core'
import { useI18n } from 'vue-i18n'
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  unitType: MonitorUnitType
  config: MonitorConfig
}>()

const { t } = useI18n()

const { units, loading, error, refresh } = useProcessingMonitor(props.unitType, props.config)

// List of expanded units by UUID.
const expandedUnitUuids = ref<Record<string, boolean>>({})

// List of expanded job group keys by "unitUuid::groupName".
const expandedGroupKeys = ref<Record<string, boolean>>({})

const executingChoiceJobUuids = ref<Record<string, boolean>>({})
const selectedChoicesByJobUuid = ref<Record<string, string>>({})

const jobIsAwaitingDecision = (job: ProcessingJob): boolean =>
  isAwaitingDecisionProbe({
    currentstep: job.currentstep,
    jobType: job.type,
    microserviceGroup: job.microservicegroup,
  })

const unitHasAwaitingDecision = (unit: ProcessingUnit): boolean => {
  return unit.jobs.some(jobIsAwaitingDecision)
}

const isUnitExpanded = (unit: ProcessingUnit): boolean => {
  const stored = expandedUnitUuids.value[unit.uuid]
  if (stored !== undefined) {
    return stored === true
  }
  return true
}

const toggleUnit = (unit: ProcessingUnit): void => {
  expandedUnitUuids.value[unit.uuid] = !isUnitExpanded(unit)
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
  return Object.fromEntries(units.value.map(unit => [unit.uuid, groupJobs(unit.jobs)]))
})

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
  return executingChoiceJobUuids.value[jobUuid] === true
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
  job: ProcessingJob
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

  const validJobUuids = new Set(nextUnits.flatMap(unit => unit.jobs.map(job => job.uuid)))
  for (const jobUuid of Object.keys(executingChoiceJobUuids.value)) {
    if (!validJobUuids.has(jobUuid)) {
      delete executingChoiceJobUuids.value[jobUuid]
    }
  }
  for (const jobUuid of Object.keys(selectedChoicesByJobUuid.value)) {
    if (!validJobUuids.has(jobUuid)) {
      delete selectedChoicesByJobUuid.value[jobUuid]
    }
  }

  for (const unit of nextUnits) {
    if (!(unit.uuid in expandedUnitUuids.value) && unitHasAwaitingDecision(unit)) {
      // Auto-opened units stay open until user toggles them.
      expandedUnitUuids.value[unit.uuid] = true
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
      if (job.choices && !(job.uuid in selectedChoicesByJobUuid.value)) {
        selectedChoicesByJobUuid.value[job.uuid] = ''
      }
      if (!job.choices && job.uuid in selectedChoicesByJobUuid.value) {
        delete selectedChoicesByJobUuid.value[job.uuid]
      }
    }
  }
})

const getApiUnitType = (): UnitType => monitorUnitMeta[props.unitType].apiUnitType
const getRemoveAllMessageKeys = (): RemoveAllMessageKeys => monitorUnitMeta[props.unitType].removeAllMessageKeys

const showTasks = (jobUuid: string): void => {
  window.open(getJobTasksUrl(jobUuid), 'output')
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

const executeMcpChoice = async (job: ProcessingJob, choice: string): Promise<void> => {
  executingChoiceJobUuids.value[job.uuid] = true
  try {
    await executeChoice({
      uuid: job.uuid,
      choice,
    })
    job.currentstep = STATUS_CODE_BY_NAME.STATUS_EXECUTING_COMMANDS
    job.currentstep_label = undefined
    job.choices = undefined
    delete selectedChoicesByJobUuid.value[job.uuid]
  } catch {
    selectedChoicesByJobUuid.value[job.uuid] = ''
  } finally {
    delete executingChoiceJobUuids.value[job.uuid]
  }
}

const executeAtomUploadChoice = async (
  payload: AtomUploadPendingChoice,
  target: string,
  options?: { preserveSelectionOnFailure?: boolean },
): Promise<boolean> => {
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

    await executeMcpChoice(payload.job, payload.choice)
    return true
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
  if (!choice || isJobExecutingChoice(job.uuid)) {
    return
  }

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
      const payload: AtomUploadPendingChoice = { job, choice, unitUuid }
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

  await executeMcpChoice(job, choice)
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
const iconDeleteBackground = `url("${icons.delete}")`
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
        ><span aria-hidden="true">&nbsp;</span></a>
      </div>
    </div>
    <div id="sip-body">
      <p
        v-if="loading"
        id="sip-loading"
      >
        {{ t('monitor.loading') }}
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
          :is-expanded="isUnitExpanded(unit)"
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
  background-image: v-bind(iconDeleteBackground);
  background-repeat: no-repeat;
  background-position: center left;
}
</style>

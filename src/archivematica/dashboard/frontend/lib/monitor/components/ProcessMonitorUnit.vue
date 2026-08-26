<script setup lang="ts">
import { formatDateTime } from '@/shared/date'
import { PROCESSING_UNIT_STATE } from '@/shared/http/processing'
import type { ProcessingJob, ProcessingUnit } from '@/shared/http/processing'
import {
  getStatusIconForJob,
  isIngestStartTimeMarkerJob,
} from '@/shared/workflow'
import {
  SilkAcceptIcon,
  SilkArrowRefreshIcon,
  SilkBellIcon,
  SilkDeleteIcon,
  SilkCancelIcon,
  SilkHourglassIcon,
  SilkTableEditIcon,
} from '@/shared/icons'
import ProcessMonitorGroup from './ProcessMonitorGroup.vue'
import { useI18n } from 'vue-i18n'

type JobGroup = {
  name: string
  jobs: ProcessingJob[]
}

const props = defineProps<{
  unit: ProcessingUnit
  isExpandable: boolean
  isExpanded: boolean
  isLoadingJobGroups: boolean
  hasJobGroupsError: boolean
  unitGroups: JobGroup[]
  expandedGroupKeys: Record<string, boolean>
  executingChoiceJobUuids: Record<string, boolean>
  selectedChoicesByJobUuid: Record<string, string>
  microservicesHelp: Record<string, string>
  jobStatuses: Record<string, string>
}>()

const emit = defineEmits<{
  (event: 'toggle-unit', unit: ProcessingUnit): void
  (event: 'open-panel', unitUuid: string): void
  (event: 'remove-unit', unit: ProcessingUnit): void
  (event: 'toggle-group', payload: { unitUuid: string, groupName: string, jobs: ProcessingJob[] }): void
  (event: 'show-tasks', jobUuid: string): void
  (event: 'show-job-history', payload: { unitUuid: string, linkId: string }): void
  (event: 'set-selected-job-choice', payload: { jobUuid: string, choice: string }): void
  (event: 'execute-job-choice', payload: { job: ProcessingJob, choice: string, unitUuid: string }): void
}>()

const { t } = useI18n()

const toggleUnit = (): void => {
  if (props.isExpandable) {
    emit('toggle-unit', props.unit)
  }
}

const statusIconByName = {
  'accept': SilkAcceptIcon,
  'arrow-refresh': SilkArrowRefreshIcon,
  'bell': SilkBellIcon,
  'cancel': SilkCancelIcon,
  'hourglass': SilkHourglassIcon,
} as const

const getStatusIconName = (unit: ProcessingUnit): keyof typeof statusIconByName => {
  if (unit.has_awaiting_decision === true) return 'bell'
  const job = unit.status ?? unit.jobs[0]
  if (!job && unit.processing_state === PROCESSING_UNIT_STATE.waitingForProcessing) {
    return 'hourglass'
  }
  if (!job) return 'accept'
  const iconName = getStatusIconForJob({
    currentstep: job.currentstep,
    jobType: job.type,
    microserviceGroup: job.microservicegroup,
  })
  return iconName in statusIconByName
    ? iconName as keyof typeof statusIconByName
    : 'accept'
}

const statusCodeByIconName = {
  'accept': 2,
  'arrow-refresh': 3,
  'bell': 1,
  'cancel': 4,
} as const

const getStatusLabel = (unit: ProcessingUnit): string => {
  const iconName = getStatusIconName(unit)
  if (iconName === 'hourglass') {
    return t('monitor.waitingForProcessing')
  }
  const statusCode = statusCodeByIconName[iconName]
  return props.jobStatuses[String(statusCode)] ?? String(statusCode)
}

const getIngestStartTime = (unit: ProcessingUnit): string => {
  if (typeof unit.started_at === 'number') {
    return formatDateTime(unit.started_at)
  }
  const jobs = Array.isArray(unit.jobs) ? unit.jobs : []
  const startJob
    = jobs.find(job => isIngestStartTimeMarkerJob(job.type))
      ?? (jobs.length > 0 ? jobs[jobs.length - 1] : undefined)
  if (!startJob) return ''
  return formatDateTime(startJob.timestamp)
}

</script>

<template>
  <div
    class="sip"
    :class="{
      'sip-expandable': isExpandable,
      'sip-selected': isExpanded,
      'sip-expanded': isExpanded,
    }"
  >
    <div
      :id="`sip-row-${unit.uuid}`"
      class="sip-row"
      @click="toggleUnit"
    >
      <div class="sip-detail-icon-status">
        <component
          :is="statusIconByName[getStatusIconName(unit)]"
          :class="[
            'monitor-status-icon',
            `monitor-status-icon-${getStatusIconName(unit)}`,
          ]"
          aria-hidden="true"
          size="16"
          alt=""
        />
        <span class="sr-only monitor-status-label">{{ getStatusLabel(unit) }}</span>
      </div>
      <div
        class="sip-detail-directory"
        :role="isExpandable ? 'button' : undefined"
        :tabindex="isExpandable ? 0 : undefined"
        :aria-expanded="isExpandable ? isExpanded : undefined"
        :aria-controls="isExpandable ? `sip-jobs-${unit.uuid}` : undefined"
        @keydown.enter.stop.prevent="toggleUnit"
        @keydown.space.stop.prevent="toggleUnit"
      >
        {{ unit.directory }}
        <abbr :title="unit.uuid">{{ t('monitor.uuid') }}</abbr>
      </div>
      <div class="sip-detail-uuid">
        {{ unit.uuid }}
      </div>
      <div class="sip-detail-timestamp">
        {{ getIngestStartTime(unit) }}
      </div>
      <div class="sip-detail-actions">
        <a
          class="btn_show_metadata"
          href="#"
          :title="t('monitor.metadata')"
          @click.stop.prevent="emit('open-panel', unit.uuid)"
        >
          <SilkTableEditIcon
            class="monitor-action-icon"
            aria-hidden="true"
            size="16"
            alt=""
          />
          <span>{{ t('monitor.metadata') }}</span>
        </a>
        <a
          v-if="unit.processing_state !== PROCESSING_UNIT_STATE.waitingForProcessing"
          class="btn_remove_sip"
          href="#"
          :title="t('monitor.remove')"
          @click.stop.prevent="emit('remove-unit', unit)"
        >
          <SilkDeleteIcon
            class="monitor-action-icon"
            aria-hidden="true"
            size="16"
            alt=""
          />
          <span>{{ t('monitor.remove') }}</span>
        </a>
      </div>
    </div>
    <Transition name="sip-jobs-slide">
      <div
        v-if="isExpanded"
        :id="`sip-jobs-${unit.uuid}`"
        class="sip-detail-job-container"
        :class="{ 'sip-detail-job-container-expanded': isExpanded }"
        :aria-busy="isLoadingJobGroups"
      >
        <p
          v-if="isLoadingJobGroups && unitGroups.length === 0"
          class="monitor-job-groups-loading"
          role="status"
        >
          {{ t('misc.loading') }}
        </p>
        <div
          v-if="hasJobGroupsError"
          class="alert alert-warning monitor-job-groups-warning"
          role="alert"
        >
          {{ t('monitor.jobGroupsLoadFailed') }}
        </div>
        <ProcessMonitorGroup
          v-for="group in unitGroups"
          :key="group.name"
          :unit-uuid="unit.uuid"
          :group="group"
          :expanded-group-keys="expandedGroupKeys"
          :executing-choice-job-uuids="executingChoiceJobUuids"
          :selected-choices-by-job-uuid="selectedChoicesByJobUuid"
          :microservices-help="microservicesHelp"
          :job-statuses="jobStatuses"
          @toggle-group="emit('toggle-group', $event)"
          @show-tasks="emit('show-tasks', $event)"
          @show-job-history="emit('show-job-history', $event)"
          @set-selected-job-choice="emit('set-selected-job-choice', $event)"
          @execute-job-choice="emit('execute-job-choice', $event)"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.sip {
  width: 100%;
  clear: both;
  float: left;
  border: 1px solid White;
}

.sip-expanded {
  margin-bottom: 10px;
}

.sip-expandable:hover,
.sip-selected {
  border-color: #bbb;
  background-color: #eee;
}

.sip-new {
  background-color: #fedda7;
}

.sip-removing {
  background-color: #f7cdcd;
  border-color: #bbb;
}

.sip-expandable .sip-row {
  cursor: pointer;
}

.sip-row > div {
  float: left;
}

.sip-row:after {
  clear: both;
  content: "";
  display: table;
}

.sip-detail-icon-status {
  width: 26px;
  padding: 4px 0;
  text-align: center;
}

.sip-detail-directory {
  float: left;
  width: 300px;
  padding: 4px 0;
  display: table-cell;
  white-space: nowrap;
}

.sip-detail-directory:focus {
  outline: none;
}

.sip-detail-directory:focus-visible {
  outline: 1px dotted #333;
  outline-offset: 1px;
}

.sip-detail-uuid {
  float: left;
  width: 310px;
  padding: 5px 0 3px;
  font-family: "Courier New", Courier, "Lucida Console", monospace;
}

.sip-detail-timestamp {
  float: left;
  width: 180px;
  padding: 4px 0;
}

.sip-detail-actions {
  float: left;
}

.sip-detail-directory > abbr {
  display: none;
  border: 1px dotted #999;
  padding: 1px 4px;
  margin-left: 8px;
}

.sip-detail-directory > abbr:hover {
  background-color: #fff;
}

.sip-detail-actions > a {
  visibility: hidden;
  float: left;
  display: flex;
  align-items: center;
  height: 26px;
  width: 16px;
  margin-right: 4px;
  text-decoration: none;
}

.sip-detail-actions > a:hover,
.sip-detail-actions > a:focus {
  text-decoration: none;
}

.sip-detail-actions > a > span {
  display: none;
}

.monitor-action-icon {
  display: block;
}

.sip-removing .sip-detail-actions > a,
.sip:hover .sip-detail-actions > a,
.sip:focus-within .sip-detail-actions > a,
.sip-selected .sip-detail-actions > a {
  visibility: visible;
}

/* Queued rows have no focusable expander. Keep Metadata in the tab order
   while revealing it only when the row is hovered or contains focus. */
.sip:not(.sip-expandable) .btn_show_metadata {
  visibility: visible;
  opacity: 0;
  pointer-events: none;
}

.sip:hover .btn_show_metadata,
.sip:focus-within .btn_show_metadata {
  opacity: 1;
  pointer-events: auto;
}

.btn_show_metadata:focus-visible {
  outline: 1px dotted #333;
  outline-offset: 1px;
}

.sip-detail-job-container {
  clear: both;
  display: none;
}

.sip-jobs-slide-enter-active,
.sip-jobs-slide-leave-active {
  transition: max-height 0.25s ease;
  overflow: hidden;
}

.sip-detail-job-container-expanded {
  display: block;
}

.monitor-job-groups-warning {
  margin: 0;
  padding: 6px 10px;
}

.monitor-job-groups-loading {
  margin: 5px;
}

.sip-jobs-slide-enter-from,
.sip-jobs-slide-leave-to {
  max-height: 0;
}

.sip-jobs-slide-enter-to,
.sip-jobs-slide-leave-from {
  max-height: 1000px;
}
</style>

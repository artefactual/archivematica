<script setup lang="ts">
import { formatDateTime } from '@/shared/date'
import type { ProcessingJob, ProcessingUnit } from '@/shared/http/processing'
import {
  getStatusIconForJob,
  isIngestStartTimeMarkerJob,
} from '@/shared/workflow'
import { icons } from '@/shared/assets/icons'
import ProcessMonitorGroup from './ProcessMonitorGroup.vue'
import { useI18n } from 'vue-i18n'

type JobGroup = {
  name: string
  jobs: ProcessingJob[]
}

defineProps<{
  unit: ProcessingUnit
  isExpanded: boolean
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
  (event: 'set-selected-job-choice', payload: { jobUuid: string, choice: string }): void
  (event: 'execute-job-choice', payload: { job: ProcessingJob, choice: string, unitUuid: string }): void
}>()

const { t } = useI18n()

const statusIconByFilename = {
  'accept.png': icons.accept,
  'arrow_refresh.png': icons.arrowRefresh,
  'bell.png': icons.bell,
  'cancel.png': icons.cancel,
} as const

const getStatusIcon = (job: ProcessingJob | undefined): string => {
  if (!job) return statusIconByFilename['accept.png']
  const file = getStatusIconForJob({
    currentstep: job.currentstep,
    jobType: job.type,
    microserviceGroup: job.microservicegroup,
  })
  const knownStatusIcon = statusIconByFilename[file as keyof typeof statusIconByFilename]
  return knownStatusIcon ?? `/media/images/${file}`
}

const getIngestStartTime = (unit: ProcessingUnit): string => {
  const jobs = Array.isArray(unit.jobs) ? unit.jobs : []
  const startJob
    = jobs.find(job => isIngestStartTimeMarkerJob(job.type))
      ?? (jobs.length > 0 ? jobs[jobs.length - 1] : undefined)
  if (!startJob) return ''
  return formatDateTime(startJob.timestamp)
}

const iconZoomBackground = `url("${icons.zoom}")`
const iconTableEditBackground = `url("${icons.tableEdit}")`
const iconDeleteBackground = `url("${icons.delete}")`
</script>

<template>
  <div
    class="sip"
    :class="{
      'sip-selected': isExpanded,
      'sip-expanded': isExpanded,
    }"
  >
    <div
      :id="`sip-row-${unit.uuid}`"
      class="sip-row"
    >
      <div class="sip-detail-icon-status">
        <img
          :src="getStatusIcon(unit.jobs[0])"
          alt=""
          aria-hidden="true"
        >
      </div>
      <div
        class="sip-detail-directory"
        @click.stop.prevent="emit('toggle-unit', unit)"
      >
        {{ unit.directory }}
        <abbr :title="unit.uuid">{{ t('monitor.uuid') }}</abbr>
      </div>
      <div
        class="sip-detail-uuid"
        @click.stop.prevent="emit('toggle-unit', unit)"
      >
        {{ unit.uuid }}
      </div>
      <div
        class="sip-detail-timestamp"
        @click.stop.prevent="emit('toggle-unit', unit)"
      >
        {{ getIngestStartTime(unit) }}
      </div>
      <div class="sip-detail-actions">
        <a
          class="btn_show_metadata"
          href="#"
          :title="t('monitor.metadata')"
          @click.stop.prevent="emit('open-panel', unit.uuid)"
        ><span>{{ t('monitor.metadata') }}</span></a>
        <a
          class="btn_remove_sip"
          href="#"
          :title="t('monitor.remove')"
          @click.stop.prevent="emit('remove-unit', unit)"
        ><span>{{ t('monitor.remove') }}</span></a>
      </div>
    </div>
    <Transition name="sip-jobs-slide">
      <div
        v-if="isExpanded"
        class="sip-detail-job-container"
        :class="{ 'sip-detail-job-container-expanded': isExpanded }"
      >
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

.sip:hover,
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

.sip-row {
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
  height: 26px;
  width: 16px;
  margin-right: 4px;
  background-color: transparent;
  background-repeat: no-repeat;
  background-position: center left;
}

.sip-detail-actions > a > span {
  display: none;
}

.btn_show_metadata {
  background-image: v-bind(iconZoomBackground);
}

.sip-selected .btn_show_metadata {
  background-image: v-bind(iconTableEditBackground);
}

.btn_remove_sip {
  background-image: v-bind(iconDeleteBackground);
}

.sip-removing .sip-detail-actions > a,
.sip:hover .sip-detail-actions > a,
.sip-selected .sip-detail-actions > a {
  visibility: visible;
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

.sip-jobs-slide-enter-from,
.sip-jobs-slide-leave-to {
  max-height: 0;
}

.sip-jobs-slide-enter-to,
.sip-jobs-slide-leave-from {
  max-height: 1000px;
}
</style>

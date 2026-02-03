<script setup lang="ts">
import type { ProcessingJob } from '@/shared/http/processing'
import {
  isAwaitingDecisionProbe,
} from '@/shared/workflow'
import ProcessMonitorJob from './ProcessMonitorJob.vue'
import { useI18n } from 'vue-i18n'

type JobGroup = {
  name: string
  jobs: ProcessingJob[]
}

const props = defineProps<{
  unitUuid: string
  group: JobGroup
  expandedGroupKeys: Record<string, boolean>
  executingChoiceJobUuids: Record<string, boolean>
  selectedChoicesByJobUuid: Record<string, string>
  microservicesHelp: Record<string, string>
  jobStatuses: Record<string, string>
}>()

const emit = defineEmits<{
  (event: 'toggle-group', payload: { unitUuid: string, groupName: string, jobs: ProcessingJob[] }): void
  (event: 'show-tasks', jobUuid: string): void
  (event: 'set-selected-job-choice', payload: { jobUuid: string, choice: string }): void
  (event: 'execute-job-choice', payload: { job: ProcessingJob, choice: string, unitUuid: string }): void
}>()

const { t } = useI18n()

const getGroupKey = (unitUuid: string, groupName: string): string => {
  return `${unitUuid}::${groupName}`
}

const jobIsAwaitingDecision = (job: ProcessingJob): boolean =>
  isAwaitingDecisionProbe({
    currentstep: job.currentstep,
    jobType: job.type,
    microserviceGroup: job.microservicegroup,
  })

const groupHasAwaitingDecision = (jobs: ProcessingJob[]): boolean => {
  return jobs.some(jobIsAwaitingDecision)
}

const isGroupExpanded = (): boolean => {
  const key = getGroupKey(props.unitUuid, props.group.name)
  if (key in props.expandedGroupKeys) {
    return props.expandedGroupKeys[key] === true
  }
  return groupHasAwaitingDecision(props.group.jobs)
}

const toggleGroup = (): void => {
  emit('toggle-group', {
    unitUuid: props.unitUuid,
    groupName: props.group.name,
    jobs: props.group.jobs,
  })
}
</script>

<template>
  <div class="microservicegroup">
    <div
      class="microservice-group"
      @click.stop.prevent="toggleGroup()"
    >
      &nbsp;<span class="microservice-group-arrow">{{ isGroupExpanded() ? '▾' : '▸' }}</span>{{ ' ' }}
      <span class="microservice-group-name">
        {{ t('monitor.microservice') }}: {{ group.name }}
      </span>
    </div>
    <div
      v-if="isGroupExpanded()"
      class="job-container"
    >
      <ProcessMonitorJob
        v-for="job in group.jobs"
        :key="job.uuid"
        :job="job"
        :unit-uuid="unitUuid"
        :microservices-help="microservicesHelp"
        :job-statuses="jobStatuses"
        :selected-choice="selectedChoicesByJobUuid[job.uuid] ?? ''"
        :is-executing-choice="executingChoiceJobUuids[job.uuid] === true"
        @show-tasks="emit('show-tasks', $event)"
        @set-selected-job-choice="emit('set-selected-job-choice', $event)"
        @execute-job-choice="emit('execute-job-choice', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.microservice-group {
  cursor: pointer;
  border-top: 1px solid #ddd;
  padding: 2px 0 3px;
}
</style>

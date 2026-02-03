<script setup lang="ts">
import { formatDateTime } from '@/shared/date'
import { getIngestPreviewUrl } from '@/shared/http'
import type { ProcessingJob } from '@/shared/http/processing'
import {
  getStatusColorForJob,
  resolveIngestReviewLink,
} from '@/shared/workflow'
import HelpTooltip from '@/shared/components/HelpTooltip.vue'
import ProcessMonitorJobActions from './ProcessMonitorJobActions.vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  job: ProcessingJob
  unitUuid: string
  selectedChoice: string
  isExecutingChoice: boolean
  microservicesHelp: Record<string, string>
  jobStatuses: Record<string, string>
}>()

const emit = defineEmits<{
  (event: 'show-tasks', jobUuid: string): void
  (event: 'set-selected-job-choice', payload: { jobUuid: string, choice: string }): void
  (event: 'execute-job-choice', payload: { job: ProcessingJob, choice: string, unitUuid: string }): void
}>()

const { t } = useI18n()

const reviewUrl = computed(() => {
  const review = resolveIngestReviewLink({
    linkId: props.job.link_id,
    currentstep: props.job.currentstep,
  })
  if (!review) return null
  return getIngestPreviewUrl(review.previewType, props.job.uuid)
})

const jobStatusColor = computed(() => {
  return getStatusColorForJob({
    currentstep: props.job.currentstep,
    jobType: props.job.type,
    microserviceGroup: props.job.microservicegroup,
  })
})
const jobStatusClass = computed(() => {
  const color = jobStatusColor.value.toLowerCase()
  if (color === '#ffffff') return 'job-status-awaiting'
  if (color === '#fedda7') return 'job-status-executing'
  if (color === '#f2d8d8') return 'job-status-failed'
  return 'job-status-success'
})

const currentstepLabel = computed<string | number>(() => {
  if (props.job.currentstep_label) {
    return props.job.currentstep_label
  }
  return props.jobStatuses[String(props.job.currentstep)] ?? props.job.currentstep
})

const microserviceHelp = computed(() => {
  return props.microservicesHelp[props.job.type] ?? ''
})
</script>

<template>
  <div
    class="job"
    :class="jobStatusClass"
  >
    <div class="job-detail-microservice">
      <span class="job-type-label">{{ t('monitor.job') }}</span>
      {{ ' ' }}
      <span :title="job.uuid">
        {{ job.type }}
        <template v-if="reviewUrl">
          {{ ' ' }}
          <a
            class="btn btn-default btn-xs"
            :href="reviewUrl"
            target="_blank"
            rel="noopener"
            @click.stop
          >
            {{ t('monitor.review') }}
          </a>
        </template>
      </span>
      <template v-if="microserviceHelp">
        {{ ' ' }}
        <HelpTooltip :content="microserviceHelp" />
      </template>
    </div>

    <div
      class="job-detail-currentstep"
      :data-currentstep="job.currentstep"
    >
      <span :title="`${formatDateTime(job.timestamp)} / ${job.timestamp}`">
        {{ currentstepLabel }}
      </span>
    </div>

    <ProcessMonitorJobActions
      :job="job"
      :unit-uuid="unitUuid"
      :selected-choice="selectedChoice"
      :is-executing-choice="isExecutingChoice"
      @show-tasks="emit('show-tasks', $event)"
      @set-selected-job-choice="emit('set-selected-job-choice', $event)"
      @execute-job-choice="emit('execute-job-choice', $event)"
    />
  </div>
</template>

<style scoped>
.job {
  border-top: 1px solid #999;
  clear: both;
  float: left;
  width: 100%;
}

.job-status-awaiting {
  background-color: #ffffff;
}

.job-status-success {
  background-color: #d8f2dc;
}

.job-status-executing {
  background-color: #fedda7;
}

.job-status-failed {
  background-color: #f2d8d8;
}

.job:last-child {
  border-bottom: 1px solid #999;
}

.job > div {
  padding: 2px 5px;
  float: left;
  line-height: 18px;
}

.job-detail-microservice {
  width: 630px;
  border-right: 1px dotted #bbb;
}

.job-detail-microservice > .job-type-label {
  margin-left: 20px;
}

.job-detail-microservice > .job-type-label:after {
  content: ':';
}

.job-detail-currentstep {
  width: 180px;
  border-right: 1px dotted #bbb;
}
</style>

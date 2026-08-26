<script setup lang="ts">
import {
  getIngestNormalizationReportUrl,
  getIngestUploadAsUrl,
} from '@/shared/http'
import {
  SilkCogIcon,
  SilkTableEditIcon,
} from '@/shared/icons'
import type { ProcessingJob } from '@/shared/http/processing'
import { resolveIngestInlineActions } from '@/shared/workflow'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  job: ProcessingJob
  unitUuid: string
  selectedChoice: string
  isExecutingChoice: boolean
}>()

const emit = defineEmits<{
  (event: 'show-tasks', jobUuid: string): void
  (event: 'show-job-history', payload: { unitUuid: string, linkId: string }): void
  (event: 'set-selected-job-choice', payload: { jobUuid: string, choice: string }): void
  (event: 'execute-job-choice', payload: { job: ProcessingJob, choice: string, unitUuid: string }): void
}>()

const { t } = useI18n()

const hasJobHistory = computed(() => (props.job.count ?? 1) > 1 && !!props.job.link_id)

type InlineActionLink = {
  key: string
  className: 'btn_normalization_report' | 'btn_as_upload'
  title: string
  href: string
}

const inlineActionLinks = computed<InlineActionLink[]>(() => {
  const actions = resolveIngestInlineActions(props.job.link_id)
  return actions.flatMap((action): InlineActionLink[] => {
    if (action.action === 'open_normalization_report') {
      return [{
        key: action.ruleId,
        className: 'btn_normalization_report',
        title: t('monitor.report'),
        href: getIngestNormalizationReportUrl(props.unitUuid),
      }]
    }
    if (action.action === 'open_as_mapping') {
      return [{
        key: action.ruleId,
        className: 'btn_as_upload',
        title: t('monitor.matchDipObjectsToResources'),
        href: getIngestUploadAsUrl(props.unitUuid),
      }]
    }
    return []
  })
})

const onJobChoiceChange = (event: Event): void => {
  if (!props.job.uuid) return
  const target = event.target as HTMLSelectElement | null
  const choice = target?.value ?? ''
  emit('set-selected-job-choice', { jobUuid: props.job.uuid, choice })
  emit('execute-job-choice', { job: props.job, choice, unitUuid: props.unitUuid })
}

const showTasks = (): void => {
  if (hasJobHistory.value && props.job.link_id) {
    emit('show-job-history', { unitUuid: props.unitUuid, linkId: props.job.link_id })
  } else if (props.job.uuid) {
    emit('show-tasks', props.job.uuid)
  }
}

</script>

<template>
  <div class="job-detail-actions">
    <!-- Allow showing tasks. -->
    <a
      v-if="job.uuid && job.produces_tasks"
      class="btn_show_tasks"
      href="#"
      :title="t(hasJobHistory ? 'monitor.jobHistory' : 'monitor.tasks')"
      :aria-label="t(hasJobHistory ? 'monitor.jobHistory' : 'monitor.tasks')"
      @click.stop.prevent="showTasks()"
    >
      <SilkCogIcon
        class="monitor-job-action-icon"
        aria-hidden="true"
        size="16"
        alt=""
      />
      <span>{{ t(hasJobHistory ? 'monitor.jobHistory' : 'monitor.tasks') }}</span>
    </a>

    <!-- Other inline actions. -->
    <a
      v-for="inlineAction in inlineActionLinks"
      :key="inlineAction.key"
      :class="inlineAction.className"
      :href="inlineAction.href"
      :title="inlineAction.title"
      target="_blank"
      rel="noopener"
      @click.stop
    >
      <SilkTableEditIcon
        class="monitor-job-action-icon"
        aria-hidden="true"
        size="16"
        alt=""
      />
      <span>{{ inlineAction.title }}</span>
    </a>

    <!-- Allow executing job choices. -->
    <select
      v-if="job.uuid && job.choices"
      :value="selectedChoice"
      :disabled="isExecutingChoice"
      @change.stop.prevent="onJobChoiceChange($event)"
      @click.stop
    >
      <option value="">
        {{ t('monitor.actions') }}
      </option>
      <option
        v-for="(label, code) in job.choices"
        :key="code"
        :value="code"
      >
        - {{ label }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.job-detail-actions > a {
  float: left;
  display: flex;
  align-items: center;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  text-decoration: none;
}

.job-detail-actions > a:hover,
.job-detail-actions > a:focus {
  text-decoration: none;
}

.job-detail-actions > a > span {
  display: none;
}

.job-detail-actions > select {
  width: 80px;
  height: auto;
  line-height: normal;
  padding: 0;
  font-size: 13px;
  margin-left: 8px;
  border: 1px solid #999;
}

.monitor-job-action-icon {
  display: block;
}
</style>

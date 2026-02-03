<script setup lang="ts">
import {
  getIngestNormalizationReportUrl,
  getIngestUploadAsUrl,
} from '@/shared/http'
import { icons } from '@/shared/assets/icons'
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
  (event: 'set-selected-job-choice', payload: { jobUuid: string, choice: string }): void
  (event: 'execute-job-choice', payload: { job: ProcessingJob, choice: string, unitUuid: string }): void
}>()

const { t } = useI18n()

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
  const target = event.target as HTMLSelectElement | null
  const choice = target?.value ?? ''
  emit('set-selected-job-choice', { jobUuid: props.job.uuid, choice })
  emit('execute-job-choice', { job: props.job, choice, unitUuid: props.unitUuid })
}

const iconCogBackground = `url("${icons.cog}")`
const iconTableEditBackground = `url("${icons.tableEdit}")`
</script>

<template>
  <div class="job-detail-actions">
    <!-- Allow showing tasks. -->
    <a
      v-if="job.produces_tasks"
      class="btn_show_tasks"
      href="#"
      :title="t('monitor.tasks')"
      @click.stop.prevent="emit('show-tasks', job.uuid)"
    >
      <span>{{ t('monitor.tasks') }}</span>
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
      <span>{{ inlineAction.title }}</span>
    </a>

    <!-- Allow executing job choices. -->
    <select
      v-if="job.choices"
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
  display: block;
  float: left;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  background-color: transparent;
  background-repeat: no-repeat;
  background-position: center left;
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

.job-detail-actions > .btn_show_tasks {
  background-image: v-bind(iconCogBackground);
}

.job-detail-actions > .btn_normalization_report {
  background-image: v-bind(iconTableEditBackground);
}

.job-detail-actions > .btn_as_upload {
  background-image: v-bind(iconTableEditBackground);
}
</style>

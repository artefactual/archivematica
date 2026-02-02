<script setup lang="ts">
import { useI18n } from 'vue-i18n'

defineProps<{
  submitting: boolean
  message: string | null
  status: 'success' | 'danger' | null
}>()

const emit = defineEmits<{
  dismiss: []
}>()

const { t } = useI18n()
</script>

<template>
  <!-- Activity indicator. -->
  <div
    v-if="submitting"
    class="activity-indicator"
  >
    <i
      class="fa fa-spinner fa-spin"
      aria-hidden="true"
    />
  </div>

  <!-- Alert message. -->
  <div
    v-else-if="message"
    class="alert alert-dismissible"
    :class="status === 'success' ? 'alert-success' : 'alert-danger'"
    role="alert"
    aria-live="polite"
  >
    <button
      type="button"
      class="close"
      :aria-label="t('metadata.close')"
      @click="emit('dismiss')"
    >
      <span aria-hidden="true">×</span>
    </button>
    {{ message }}
  </div>
</template>

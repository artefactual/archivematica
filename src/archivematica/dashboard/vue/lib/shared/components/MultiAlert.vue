<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

export interface Alert {
  id: string
  message: string
  type: 'success' | 'warning' | 'danger' | 'info'
  showSpinner?: boolean
}

defineProps<{
  alerts: Alert[]
}>()

defineEmits<{
  dismiss: [id: string]
}>()
</script>

<template>
  <div
    class="multi-alert"
    role="region"
    :aria-label="t('alerts.notifications')"
  >
    <div
      v-for="alert in alerts"
      :key="alert.id"
      :class="['alert', `alert-${alert.type}`]"
      role="alert"
      :aria-live="alert.type === 'danger' ? 'assertive' : 'polite'"
      tabindex="0"
    >
      <button
        type="button"
        class="close"
        :aria-label="t('alerts.dismissAlert', { type: alert.type, message: alert.message })"
        @click="$emit('dismiss', alert.id)"
        @keydown.enter="$emit('dismiss', alert.id)"
        @keydown.space.prevent="$emit('dismiss', alert.id)"
      >
        <span aria-hidden="true">&times;</span>
      </button>
      {{ alert.message }}
      <span
        v-if="alert.showSpinner"
        role="status"
        :aria-label="t('alerts.loadingIndicator')"
      >
        <i
          class="fa fa-spinner fa-spin"
          aria-hidden="true"
        />
      </span>
    </div>
  </div>
</template>

<style scoped>
.multi-alert {
  width: 950px;
}

.alert {
  position: relative;
  padding: 12px 15px;
  margin-bottom: 10px;
  border: 1px solid transparent;
  border-radius: 4px;
}

.alert:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}

.close {
  position: absolute;
  top: 8px;
  right: 12px;
  padding: 0;
  background: none;
  border: none;
  font-size: 20px;
  font-weight: bold;
  line-height: 1;
  cursor: pointer;
  color: inherit;
}

.close:hover,
.close:focus {
  opacity: 0.7;
  outline: 2px solid #007cba;
  outline-offset: 1px;
  border-radius: 2px;
}

.alert-success {
  color: #3c763d;
  background-color: #dff0d8;
  border-color: #d6e9c6;
}

.alert-info {
  color: #31708f;
  background-color: #d9edf7;
  border-color: #bce8f1;
}

.alert-warning {
  color: #8a6d3b;
  background-color: #fcf8e3;
  border-color: #faebcc;
}

.alert-danger {
  color: #a94442;
  background-color: #f2dede;
  border-color: #ebccd1;
}
</style>

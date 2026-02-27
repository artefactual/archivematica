<script setup lang="ts">
import type { AlertMessage } from '../types'

defineProps<{
  alerts: AlertMessage[]
}>()

defineEmits<{
  dismiss: [id: number]
}>()
</script>

<template>
  <div
    v-if="alerts.length"
    class="as-matcher-alerts"
    role="region"
    aria-label="Matcher notifications"
  >
    <div
      v-for="alert in alerts"
      :key="alert.id"
      :class="['alert', `alert-${alert.type}`]"
      role="alert"
    >
      <button
        type="button"
        class="close"
        aria-label="Dismiss"
        @click="$emit('dismiss', alert.id)"
      >
        <span aria-hidden="true">&times;</span>
      </button>
      {{ alert.message }}
    </div>
  </div>
</template>

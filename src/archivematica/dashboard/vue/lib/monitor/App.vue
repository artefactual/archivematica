<script setup lang="ts">
import { ProcessMonitor } from '@/monitor/components'
import type { MonitorConfig, MonitorUnitType } from '@/monitor/composables'

defineProps<{
  unitType: MonitorUnitType
  config: MonitorConfig
}>()
</script>

<template>
  <ProcessMonitor
    :unit-type="unitType"
    :config="config"
  />
</template>

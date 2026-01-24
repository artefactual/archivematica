<script setup lang="ts">
import ConnectionStatus from '@/topbar/components/ConnectionStatus.vue'
import NavCounts from '@/topbar/components/NavCounts.vue'
import { useStatus } from '@/topbar/composables/useStatus'

useStatus()
</script>

<template>
  <ConnectionStatus />
  <NavCounts />
</template>

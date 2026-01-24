<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useStatus } from '@/topbar/composables/useStatus'

const { state } = useStatus()

const transferSelector = 'a.nav-transfer'
const ingestSelector = 'a.nav-ingest'

const hasTransferTarget = ref(false)
const hasIngestTarget = ref(false)

const transferCount = computed(() => state.counts.transfer)
const ingestCount = computed(() => state.counts.sip + state.counts.dip)

onMounted(() => {
  hasTransferTarget.value = Boolean(document.querySelector(transferSelector))
  hasIngestTarget.value = Boolean(document.querySelector(ingestSelector))
})
</script>

<template>
  <Teleport
    v-if="hasTransferTarget"
    :to="transferSelector"
  >
    <span
      v-if="transferCount > 0"
      class="nav-count"
    >{{ transferCount }}</span>
  </Teleport>

  <Teleport
    v-if="hasIngestTarget"
    :to="ingestSelector"
  >
    <span
      v-if="ingestCount > 0"
      class="nav-count"
    >{{ ingestCount }}</span>
  </Teleport>
</template>

<style scoped>
.nav-count {
  position: absolute;
  top: 2px;
  right: -6px;
  border-radius: 999px;
  background-color: red;
  color: white;
  font-weight: bold;
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  z-index: 10;
}
</style>

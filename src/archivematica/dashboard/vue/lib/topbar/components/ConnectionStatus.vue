<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStatus } from '@/topbar/composables/useStatus'

const { t } = useI18n()
const { state } = useStatus()

const hasTarget = ref(false)

const connectionMessage = computed(() => {
  if (state.loading) {
    return t('topbar.loading')
  }
  if (state.connected === null) {
    return t('topbar.initializing')
  }
  if (state.connected) {
    return t('topbar.connected')
  }
  if (state.error) {
    return t('topbar.errorConnecting')
  }
  return t('topbar.disconnected')
})

const connectionIconClass = computed(() => {
  if (state.loading) return 'status-icon-loading'
  if (state.connected === null) return 'status-icon-initializing'
  return state.connected ? 'status-icon-connected' : 'status-icon-disconnected'
})

const connectionTitle = computed(() => {
  if (state.connected === false) {
    return t('topbar.disconnected')
  }
  return connectionMessage.value
})

onMounted(() => {
  hasTarget.value = Boolean(document.querySelector('#connection-status'))
})
</script>

<template>
  <Teleport
    v-if="hasTarget"
    to="#connection-status"
  >
    <div id="status-bullet">
      <span>{{ connectionMessage }}</span>
      <i
        class="fa fa-circle status-icon"
        :class="connectionIconClass"
        :title="connectionTitle"
      />
    </div>
  </Teleport>
</template>

<style scoped>
.status-icon {
  margin-left: 6px;
  font-size: 0.5em;
  vertical-align: middle;
  position: relative;
  top: -1px;
}

.status-icon-loading {
  color: #f0ad4e;
}

.status-icon-connected {
  color: #5cb85c;
}

.status-icon-disconnected,
.status-icon-initializing {
  color: #d9534f;
}
</style>

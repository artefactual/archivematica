<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ref } from 'vue'
import TreeView from '@/browser/components/TreeView.vue'
import type { SourceLocation, FileNode, TreeSelection } from '@/shared/models'

const { t } = useI18n()

const treeViewRef = ref<InstanceType<typeof TreeView>>()

// Expose method to focus the tree view for external callers.
const focusTreeView = () => {
  if (treeViewRef.value) {
    treeViewRef.value.focusTree()
  }
}

defineExpose({
  focusTreeView,
})

defineProps<{
  currentLocation: string
  enabledLocations: SourceLocation[]
  loading: boolean
  apiError: string | null
  fileNodes: FileNode[]
  selectedPath: string
  canAddSelectedPath: boolean
  transferType: string
  expandedPaths: string[]
}>()

const emit = defineEmits<{
  'update:currentLocation': [value: string]
  'select': [selection: TreeSelection]
  'expand': [node: FileNode]
  'toggle': [path: string]
  'add': []
}>()

const handleLocationSelect = (event: Event) => {
  const target = event.target as HTMLSelectElement | null
  if (target) {
    emit('update:currentLocation', target.value)
  }
}
</script>

<template>
  <div id="transfer_browse_tree">
    <!-- Source Location Selector -->
    <label
      for="source-location-select"
      class="sr-only"
    >{{ t('fileBrowser.sourceLocation') }}</label>
    <select
      id="source-location-select"
      class="form-control"
      :value="currentLocation"
      aria-describedby="location-help"
      @change="handleLocationSelect"
    >
      <option
        v-for="location in enabledLocations"
        :key="location.uuid"
        :value="location.uuid"
      >
        {{ location.description }}
      </option>
    </select>
    <span
      id="location-help"
      class="sr-only"
    >{{ t('fileBrowser.locationHelp') }}</span>

    <!-- Tree Container -->
    <div
      v-if="currentLocation"
      class="well well-sm transfer-tree-container"
      role="region"
      :aria-label="t('fileBrowser.browser')"
      :aria-busy="loading"
    >
      <div
        v-if="apiError"
        class="alert alert-danger"
        role="alert"
        aria-live="assertive"
      >
        {{ apiError }}
      </div>
      <div
        v-else
        class="tree-classic"
      >
        <TreeView
          ref="treeViewRef"
          :nodes="fileNodes"
          :selected-path="selectedPath"
          :transfer-type="transferType"
          :expanded-paths="expandedPaths"
          @select="$emit('select', $event)"
          @expand="$emit('expand', $event)"
          @toggle="$emit('toggle', $event)"
          @add="$emit('add')"
        />
      </div>
    </div>

    <!-- Add Button -->
    <button
      type="button"
      class="btn btn-primary pull-right add-button"
      :disabled="!canAddSelectedPath"
      :aria-disabled="!canAddSelectedPath"
      :aria-label="
        canAddSelectedPath
          ? t('fileBrowser.addToTransfer', { path: selectedPath })
          : t('fileBrowser.selectFileOrFolder')
      "
      @click="$emit('add')"
    >
      {{ t('transfer.add') }}
    </button>
  </div>
</template>

<style scoped>
#transfer_browse_tree {
  width: 950px;
  margin-bottom: 60px;
  margin-top: 10px;
}

.transfer-tree-container {
  margin-top: 10px;
  margin-bottom: 10px;
  overflow: auto;
  max-height: 30em;
}

.add-button {
  margin-top: 15px;
}

/* Screen reader only content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Ensure focus indicators are visible */
select:focus,
button:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}
</style>

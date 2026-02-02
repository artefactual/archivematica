<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PathContainer from '@/shared/components/PathContainer.vue'
import { encodeBase64 } from '@/shared/encoding/base64'
import { copyMetadataFiles } from '@/shared/http'
import { useFilesystemTree, type MetadataTreeNode } from './composables/useFilesystemTree'
import MetadataSourceForm from './components/MetadataSourceForm.vue'
import MetadataPicker from './components/MetadataPicker.vue'
import MetadataSubmitStatus from './components/MetadataSubmitStatus.vue'

const { t } = useI18n()

const props = defineProps<{
  sipUUID: string
  sourceDirectories: Record<string, string>
}>()

// Type for selected metadata paths.
type MetadataPath = {
  id: number
  path: string
  locationPath: string
  type: 'file' | 'directory'
}

// Computed properties for source location selection.
const locationOptions = computed(() => Object.entries(props.sourceDirectories))

// Currently selected location UUID and its path.
const locationUUID = ref(locationOptions.value[0]?.[0] ?? '')

// Computed path for the selected location UUID.
const selectedLocationPath = computed(() => props.sourceDirectories[locationUUID.value] ?? '')

// Filesystem tree state and actions.
const {
  items,
  loading: loadingTree,
  error: treeError,
  loadRoot,
  loadChildren,
  retry,
} = useFilesystemTree()

// Added metadata paths.
const addedPaths = ref<MetadataPath[]>([])

// Next path ID for unique identification.
const nextPathId = ref(1)

// Submission state.
const submitting = ref(false)
const submitMessage = ref<string | null>(null)
const submitStatus = ref<'success' | 'danger' | null>(null)

// Metadata picker visibility and reference.
const pickerVisible = ref(false)
const sourceFormRef = ref<{ focusBrowseButton: () => void } | null>(null)

const pathItems = computed(() =>
  addedPaths.value.map(path => ({ id: String(path.id), path: path.path })),
)

// Retry loading children for a given node.
const retryLoadChildren = (node: MetadataTreeNode) => {
  void retry(node, locationUUID.value)
}

// Open (or reload) the metadata picker.
const openPicker = async () => {
  pickerVisible.value = true
  await loadRoot(locationUUID.value, selectedLocationPath.value)
}

// Close the metadata picker.
const closePicker = () => {
  pickerVisible.value = false
}

const focusBrowseButton = () => {
  sourceFormRef.value?.focusBrowseButton()
}

const dismissSubmitMessage = () => {
  submitMessage.value = null
  submitStatus.value = null
}

const addSelection = (node: MetadataTreeNode) => {
  const decodedPath = node.path ?? node.id
  if (!decodedPath) {
    return
  }
  const trailingSlash = node.kind === 'directory' ? '/' : ''
  const locationPath = `${locationUUID.value}:${decodedPath}${trailingSlash}`

  if (addedPaths.value.some(path => path.locationPath === locationPath)) {
    window.alert(t('metadata.duplicatePath'))
    return
  }

  addedPaths.value.push({
    id: nextPathId.value,
    path: decodedPath,
    locationPath,
    type: node.kind,
  })
  nextPathId.value += 1
}

const removePath = (pathId: string) => {
  const numericPathId = Number.parseInt(pathId, 10)
  if (Number.isNaN(numericPathId)) {
    return
  }
  const target = addedPaths.value.find(entry => entry.id === numericPathId)
  if (!target) return
  const message = t('metadata.removeConfirm', { path: target.path })
  if (!window.confirm(message)) return
  addedPaths.value = addedPaths.value.filter(entry => entry.id !== numericPathId)
}

const handleToggle = (node: MetadataTreeNode) => {
  void loadChildren(node, locationUUID.value)
}

const handleSubmit = async () => {
  if (!addedPaths.value.length) {
    window.alert(t('metadata.selectAtLeastOne'))
    return
  }

  submitting.value = true
  submitMessage.value = null
  submitStatus.value = null
  try {
    const sourcePaths = addedPaths.value.map(entry => encodeBase64(entry.locationPath))
    const response = await copyMetadataFiles(props.sipUUID, sourcePaths)
    if (response?.error) {
      const message
        = typeof response.error === 'string'
          ? response.error
          : response.message || t('metadata.submitFailed')
      submitMessage.value = message
      submitStatus.value = 'danger'
      return
    }
    submitMessage.value = response?.message || t('metadata.submitSuccess')
    submitStatus.value = 'success'
    addedPaths.value = []
  } catch (err) {
    const message = err instanceof Error ? err.message : t('metadata.submitFailed')
    submitMessage.value = message
    submitStatus.value = 'danger'
  } finally {
    submitting.value = false
  }
}

</script>

<template>
  <div class="metadata-editor">
    <!-- Source dropdown and action buttons (browse, add files). -->
    <MetadataSourceForm
      ref="sourceFormRef"
      v-model="locationUUID"
      :location-options="locationOptions"
      :submitting="submitting"
      @browse="openPicker"
      @submit="handleSubmit"
    />

    <!-- Submission status UI. -->
    <MetadataSubmitStatus
      :submitting="submitting"
      :message="submitMessage"
      :status="submitStatus"
      @dismiss="dismissSubmitMessage"
    />

    <!-- List of selected paths. -->
    <PathContainer
      :items="pathItems"
      :remove-label="(path) => t('metadata.removeConfirm', { path })"
      @remove="removePath"
    />

    <MetadataPicker
      :visible="pickerVisible"
      :items="items"
      :loading="loadingTree"
      :error="treeError"
      @close="closePicker"
      @toggle="handleToggle"
      @add="addSelection"
      @retry="retryLoadChildren"
      @escape="focusBrowseButton"
    />
  </div>
</template>

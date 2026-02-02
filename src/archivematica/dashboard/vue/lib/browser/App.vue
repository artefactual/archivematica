<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { MultiAlert, PathContainer } from '@/shared/components'
import type { Alert } from '@/shared/components'
import ProcessingConfigDropdown from './components/ProcessingConfigDropdown.vue'
import TreeViewContainer from './components/TreeViewContainer.vue'
import { useTransferBrowser } from '@/browser/composables/useTransferBrowser'
import type {
  TransferFormData,
  ProcessingConfig,
  TransferComponent,
  FileNode,
} from '@/browser/types'
import type { SourceLocation } from '@/shared/http/transfer'

const { t } = useI18n()

const alerts = ref<Alert[]>([])
const showBrowseTree = ref(false)
const currentLocation = ref('')
const fileNodes = ref<FileNode[]>([])
const expandedPaths = ref<string[]>([])
const transferBrowserContainerRef = ref<InstanceType<typeof TreeViewContainer>>()
const browseButtonRef = ref<HTMLButtonElement>()

const transferFormData = ref<TransferFormData>({
  name: '',
  type: 'standard',
  accession: '',
  accessSystemId: '',
  processingConfig: '',
  autoApprove: true,
})

const processingConfigs = ref<ProcessingConfig[]>([])
const sourceLocations = ref<SourceLocation[]>([])
const transferComponents = ref<TransferComponent[]>([])

const {
  error: apiError,
  loading,
  getProcessingConfigs,
  getSourceLocations,
  browseLocation,
  createTransfer,
  openComponentEditor,
} = useTransferBrowser()

const enabledLocations = computed(() => sourceLocations.value.filter(loc => loc.enabled))

// Button should be disabled if no components OR if name is required but empty.
const isTransferButtonDisabled = computed(() => {
  const hasComponents = transferComponents.value.length > 0
  const needsName = transferFormData.value.type !== 'zipped bag' && transferFormData.value.type !== 'zipfile'
  const hasName = transferFormData.value.name.trim().length > 0

  return !hasComponents || (needsName && !hasName)
})

const isTransferTypeDisabled = computed(() => transferComponents.value.length > 0)

// Ref for the transfer name input element.
const transferNameInputRef = ref<HTMLInputElement>()

onMounted(async () => {
  try {
    const [configs, locations] = await Promise.all([getProcessingConfigs(), getSourceLocations()])

    processingConfigs.value = configs
    sourceLocations.value = locations

    // Default processing config starts at 'default'.
    transferFormData.value.processingConfig = 'default'

    // Auto-select the first enabled location so the file tree starts populated.
    const enabled = locations.filter(loc => loc.enabled)
    if (enabled.length > 0) {
      const preferredLocation = enabled.find(loc => loc.uuid === currentLocation.value) ?? enabled[0]
      if (preferredLocation && currentLocation.value !== preferredLocation.uuid) {
        currentLocation.value = preferredLocation.uuid
      }
      await handleLocationChange()
    }

    // Auto-focus the transfer name field if it's visible.
    nextTick(() => {
      if (transferFormData.value.type !== 'zipped bag' && transferFormData.value.type !== 'zipfile') {
        transferNameInputRef.value?.focus()
      }
    })
  } catch {
    showAlert(t('alerts.loadDataFailed'), 'danger')
  }
})

const toggleBrowseTree = () => {
  showBrowseTree.value = !showBrowseTree.value
}

const focusBrowseButton = () => {
  browseButtonRef.value?.focus()
}

const focusTransferTreeAfterAdd = async () => {
  await nextTick()
  transferBrowserContainerRef.value?.focusTreeView({
    target: 'selected',
  })
}

const handleLocationChange = async () => {
  expandedPaths.value = []
  if (currentLocation.value) {
    await loadRootFiles()
  } else {
    fileNodes.value = []
  }
}

const loadRootFiles = async () => {
  if (!currentLocation.value) return

  try {
    const nodes = await browseLocation(currentLocation.value, '')
    fileNodes.value = nodes
  } catch {
    // Failed to load files from the location.
    showAlert(t('alerts.loadFilesFailed'), 'danger')
  }
}

const handleToggle = (path: string) => {
  const index = expandedPaths.value.indexOf(path)
  if (index > -1) {
    expandedPaths.value = expandedPaths.value.filter(p => p !== path)
  } else {
    expandedPaths.value = [...expandedPaths.value, path]
  }
}

const handleExpand = async (node: FileNode) => {
  if (!currentLocation.value || node.type !== 'directory' || node.children_fetched) {
    return
  }

  // Direct mutation - node is already a reactive object reference.
  node.loading = true

  try {
    const children = await browseLocation(currentLocation.value, node.path)
    node.children = children
    node.children_fetched = true
  } catch {
    showAlert(t('alerts.loadFilesFailed'), 'danger')
    node.children = []
    node.children_fetched = false
  } finally {
    node.loading = false
  }

  // Trigger reactivity for tree structure change.
  fileNodes.value = [...fileNodes.value]
}

const addSelectedPath = (node: FileNode) => {
  if (!currentLocation.value) {
    return
  }

  // Find the current location object to get the base path.
  const currentLocationObj = sourceLocations.value.find(
    loc => loc.uuid === currentLocation.value,
  )
  if (!currentLocationObj) {
    // Current location not found in source locations.
    return
  }

  // Construct the full absolute path by concatenating base path with
  // selected path. Ensure proper path separator between base and relative
  // paths.
  const basePath = currentLocationObj.path.endsWith('/')
    ? currentLocationObj.path
    : `${currentLocationObj.path}/`
  const relativePath = node.path.startsWith('/')
    ? node.path.slice(1)
    : node.path
  const fullPath = basePath + relativePath

  const alreadyAdded = transferComponents.value.some(
    component => component.location === currentLocation.value && component.path === fullPath,
  )
  if (alreadyAdded) {
    return
  }

  const component: TransferComponent = {
    id: Date.now().toString(),
    path: fullPath,
    location: currentLocation.value,
  }
  transferComponents.value.push(component)

  // Restore focus to the tree view after adding.
  void focusTransferTreeAfterAdd()
}

const removeComponent = (id: string) => {
  const target = transferComponents.value.find(c => c.id === id)
  if (!target) {
    return
  }

  const message = t('fileBrowser.removeComponentConfirm', { path: target.path })
  if (!window.confirm(message)) {
    return
  }

  const index = transferComponents.value.findIndex(c => c.id === id)
  if (index !== -1) {
    transferComponents.value.splice(index, 1)
  }
}

const editComponent = async (id: string) => {
  // Find the component to edit in the list.
  const component = transferComponents.value.find(c => c.id === id)
  if (!component) {
    // Component not found in the list.
    return
  }

  try {
    await openComponentEditor(component, transferFormData.value.type)
  } catch {
    showAlert(apiError.value || t('alerts.editComponentFailed'), 'danger')
  }
}

const startTransfer = async (processingConfig: string = 'default') => {
  if (transferComponents.value.length === 0) {
    showAlert(t('alerts.addComponentRequired'), 'warning')
    return
  }

  try {
    // Determine transfer name based on type to keep special-case defaults.
    let transferName = transferFormData.value.name
    if (transferFormData.value.type === 'zipped bag') {
      transferName = 'ZippedBag'
    } else if (transferFormData.value.type === 'zipfile') {
      transferName = 'ZipFile'
    }

    await createTransfer({
      ...transferFormData.value,
      name: transferName,
      processingConfig, // Use the passed processing config.
      components: transferComponents.value,
    })

    // Find the processing config name for display.
    const selectedConfig = processingConfigs.value.find(config => config.pk === processingConfig)
    const configName = selectedConfig ? selectedConfig.name : processingConfig

    showAlert(t('alerts.transferStarted', { name: transferName, config: configName }), 'info')
    resetForm()
  } catch {
    showAlert(apiError.value || t('alerts.transferFailed'), 'danger')
  }
}

const handleLocationChangeEvent = async (location: string) => {
  currentLocation.value = location
  await handleLocationChange()
}

const resetForm = () => {
  transferFormData.value = {
    name: '',
    type: 'standard',
    accession: '',
    accessSystemId: '',
    processingConfig: 'default',
    autoApprove: true,
  }
  transferComponents.value = []
}

const showAlert = (message: string, type: 'success' | 'warning' | 'danger' | 'info', showSpinner = false) => {
  const alert = {
    id: Date.now().toString(),
    message,
    type,
    showSpinner,
  }
  alerts.value.push(alert)

  // Announce to screen readers for accessibility.
  announceToScreenReader(message)
}

const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div')
  announcement.setAttribute('aria-live', 'assertive')
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message
  document.body.appendChild(announcement)

  // Remove after announcement is complete.
  setTimeout(() => {
    document.body.removeChild(announcement)
  }, 1000)
}

const dismissAlert = (id: string) => {
  const index = alerts.value.findIndex(a => a.id === id)
  if (index !== -1) {
    alerts.value.splice(index, 1)
  }
}
</script>

<template>
  <section class="transfer-browser">
    <!-- Skip link for accessibility -->
    <a
      href="#file-browser"
      class="sr-only sr-only-focusable"
    >{{ t('transfer.skipToFileBrowser') }}</a>

    <MultiAlert
      :alerts="alerts"
      @dismiss="dismissAlert"
    />

    <div
      id="transfer-browser-form"
      class="row"
      role="form"
      :aria-label="t('transfer.configurationForm')"
    >
      <!-- Transfer type. -->
      <div class="col-xs-2">
        <label
          for="transfer-type"
          class="sr-only"
        >{{ t('transfer.type') }}</label>
        <select
          id="transfer-type"
          v-model="transferFormData.type"
          class="form-control"
          :disabled="isTransferTypeDisabled"
          :aria-disabled="isTransferTypeDisabled"
          aria-describedby="transfer-type-help"
        >
          <option value="standard">
            {{ t('transferTypes.standard') }}
          </option>
          <option value="zipfile">
            {{ t('transferTypes.zipfile') }}
          </option>
          <option value="unzipped bag">
            {{ t('transferTypes.unzippedBag') }}
          </option>
          <option value="zipped bag">
            {{ t('transferTypes.zippedBag') }}
          </option>
          <option value="dspace">
            {{ t('transferTypes.dspace') }}
          </option>
          <option value="disk image">
            {{ $t('transferTypes.diskImage') }}
          </option>
          <option value="dataverse">
            {{ $t('transferTypes.dataverse') }}
          </option>
        </select>
        <div
          id="transfer-type-help"
          class="help-block"
        >
          {{ $t('transfer.type') }}
        </div>
      </div>

      <!-- Transfer name (hidden for zipped bags and zipfile). -->
      <div
        v-if="transferFormData.type !== 'zipped bag' && transferFormData.type !== 'zipfile'"
        class="col-xs-2"
      >
        <label
          for="transfer-name"
          class="sr-only"
        >{{ $t('transfer.name') }}</label>
        <input
          id="transfer-name"
          ref="transferNameInputRef"
          v-model="transferFormData.name"
          type="text"
          class="form-control"
          :aria-describedby="'transfer-name-help'"
          :aria-required="true"
          required
        >
        <div
          id="transfer-name-help"
          class="help-block"
        >
          {{ $t('transfer.name') }}
        </div>
      </div>

      <!-- Accession. -->
      <div class="col-xs-2">
        <label
          for="transfer-accession"
          class="sr-only"
        >{{ $t('transfer.accession') }}</label>
        <input
          id="transfer-accession"
          v-model="transferFormData.accession"
          type="text"
          class="form-control"
          aria-describedby="transfer-accession-help"
        >
        <div
          id="transfer-accession-help"
          class="help-block"
        >
          {{ $t('transfer.accession') }}
        </div>
      </div>

      <!-- Access System ID. -->
      <div class="col-xs-2">
        <label
          for="transfer-access-system-id"
          class="sr-only"
        >{{ $t('transfer.accessSystemId') }}</label>
        <input
          id="transfer-access-system-id"
          v-model="transferFormData.accessSystemId"
          type="text"
          class="form-control"
          aria-describedby="transfer-access-system-id-help"
        >
        <div
          id="transfer-access-system-id-help"
          class="help-block"
        >
          {{ $t('transfer.accessSystemId') }}
        </div>
      </div>

      <!-- Submission buttons. -->
      <div class="col-xs-4">
        <button
          ref="browseButtonRef"
          type="button"
          :class="['btn', 'btn-browse', showBrowseTree ? 'btn-secondary' : 'btn-default']"
          :aria-label="showBrowseTree ? $t('transfer.hideBrowser') : $t('transfer.showBrowser')"
          :aria-expanded="showBrowseTree"
          @click="toggleBrowseTree"
        >
          {{ $t('transfer.browse') }}
        </button>
        <ProcessingConfigDropdown
          :configs="processingConfigs"
          :disabled="isTransferButtonDisabled"
          :start-label="$t('transfer.startTransfer')"
          :submission-options-label="$t('transfer.submissionOptions')"
          :show-config-options-label="$t('transfer.showConfigOptions')"
          :start-with-config-label="(name) => $t('transfer.startWithConfig', { config: name })"
          @start-default="startTransfer('default')"
          @start-config="startTransfer"
        />
        <div class="checkbox">
          <label for="auto-approve-checkbox">
            <input
              id="auto-approve-checkbox"
              v-model="transferFormData.autoApprove"
              type="checkbox"
              aria-describedby="auto-approve-help"
            >
            {{ $t('transfer.autoApprove') }}
          </label>
          <span
            id="auto-approve-help"
            class="sr-only"
          >{{ $t('transfer.autoApproveHelp') }}</span>
        </div>
      </div>
    </div>

    <PathContainer
      :items="transferComponents"
      :show-edit="transferFormData.type === 'disk image'"
      :edit-label="(path: string) => $t('fileBrowser.editComponent', { path })"
      :remove-label="(path: string) => $t('fileBrowser.removeComponent', { path })"
      @edit="editComponent"
      @remove="removeComponent"
    />

    <section
      v-if="showBrowseTree"
      id="file-browser"
      :aria-label="$t('transfer.fileBrowserSection')"
    >
      <TreeViewContainer
        ref="transferBrowserContainerRef"
        :current-location="currentLocation"
        :enabled-locations="enabledLocations"
        :loading="loading"
        :api-error="apiError"
        :file-nodes="fileNodes"
        :transfer-type="transferFormData.type"
        :expanded-paths="expandedPaths"
        @update:current-location="handleLocationChangeEvent"
        @expand="handleExpand"
        @toggle="handleToggle"
        @add="addSelectedPath"
        @escape="focusBrowseButton"
      />
    </section>
  </section>
</template>

<style scoped>
.transfer-browser {
  width: 950px;
}

.btn-browse {
  margin-right: 10px;
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

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: 4px 6px;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
  background-color: #007cba;
  color: white;
  text-decoration: none;
  border-radius: 3px;
}

/* Ensure focus indicators are visible */
.btn:focus,
select:focus,
input:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}

/* Bootstrap 3 dropdown overrides - minimal changes */
.dropdown-menu.show {
  display: block;
}
</style>

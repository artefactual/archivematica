<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import MultiAlert from '@/browser/components/MultiAlert.vue'
import PathContainer from '@/browser/components/PathContainer.vue'
import TreeViewContainer from '@/browser/components/TreeViewContainer.vue'
import { useTransferAPI } from '@/browser/composables/useTransferAPI'
import type {
  TransferFormData,
  ProcessingConfig,
  SourceLocation,
  TransferComponent,
  Alert,
  FileNode,
  TreeSelection,
} from '@/shared/models'

const { t } = useI18n()

const alerts = ref<Alert[]>([])
const showBrowseTree = ref(false)
const showProcessingDropdown = ref(false)
const currentLocation = ref('')
const selectedPath = ref('')
const canAddSelectedPath = ref(false)
const fileNodesState = reactive<{ nodes: FileNode[] }>({ nodes: [] })
const fileNodes = computed(() => fileNodesState.nodes)
const expandedPaths = ref<string[]>([])
const transferBrowserContainerRef = ref<InstanceType<typeof TreeViewContainer>>()

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

const { error: apiError, loading, getProcessingConfigs, getSourceLocations, browseLocation, createTransfer, openComponentEditor } = useTransferAPI()

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

const toggleProcessingDropdown = () => {
  showProcessingDropdown.value = !showProcessingDropdown.value
  if (showProcessingDropdown.value) {
    currentDropdownIndex.value = -1
    // Don't auto-focus when opened with mouse click.
    // Focus will be set only when using keyboard navigation.
  }
}

// Close dropdown when clicking outside to improve UX.
const closeDropdown = () => {
  showProcessingDropdown.value = false
}

// Handle keyboard navigation for dropdown accessibility.
const currentDropdownIndex = ref(-1)

// Handle keyboard events on the dropdown toggle button.
const handleDropdownButtonKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
    case ' ':
      event.preventDefault()
      toggleProcessingDropdown()
      break
    case 'ArrowDown':
      event.preventDefault()
      if (!showProcessingDropdown.value) {
        showProcessingDropdown.value = true
        currentDropdownIndex.value = -1
        // Focus first item when opening with keyboard.
        nextTick(() => {
          const menuItems = getDropdownItems()
          if (menuItems.length > 0) {
            currentDropdownIndex.value = 0
            const firstItem = menuItems[0]
            firstItem?.focus()
          }
        })
      }
      break
  }
}

const handleDropdownKeyDown = (event: KeyboardEvent) => {
  const menuItems = getDropdownItems()
  if (menuItems.length === 0) {
    return
  }

  switch (event.key) {
    case 'Escape':
      showProcessingDropdown.value = false
      dropdownButtonRef.value?.focus()
      break
    case 'ArrowDown': {
      event.preventDefault()
      currentDropdownIndex.value = Math.min(currentDropdownIndex.value + 1, menuItems.length - 1)
      const nextItem = menuItems[currentDropdownIndex.value]
      nextItem?.focus()
      break
    }
    case 'ArrowUp': {
      event.preventDefault()
      currentDropdownIndex.value = Math.max(currentDropdownIndex.value - 1, 0)
      const previousItem = menuItems[currentDropdownIndex.value]
      previousItem?.focus()
      break
    }
    case 'Home': {
      event.preventDefault()
      currentDropdownIndex.value = 0
      const firstItem = menuItems[0]
      firstItem?.focus()
      break
    }
    case 'End': {
      event.preventDefault()
      currentDropdownIndex.value = menuItems.length - 1
      const lastItem = menuItems[currentDropdownIndex.value]
      lastItem?.focus()
      break
    }
  }
}

// Focus management references for dropdown.
const dropdownButtonRef = ref<HTMLElement>()
const dropdownMenuRef = ref<HTMLElement>()

const getDropdownItems = (): HTMLElement[] => {
  if (!dropdownMenuRef.value) {
    return []
  }
  return Array.from(dropdownMenuRef.value.querySelectorAll<HTMLElement>('a[role="menuitem"]'))
}

// Close dropdown when clicking outside to improve UX.
const handleClickOutside = (event: MouseEvent) => {
  if (dropdownButtonRef.value && dropdownMenuRef.value) {
    const target = event.target as HTMLElement
    if (!dropdownButtonRef.value.contains(target) && !dropdownMenuRef.value.contains(target)) {
      showProcessingDropdown.value = false
    }
  }
}

// Set up click outside listener when component is mounted.
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// Clean up listener when component is unmounted.
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Note: selectProcessingConfig is no longer needed since dropdown items directly start transfers.

const handleLocationChange = async () => {
  selectedPath.value = ''
  canAddSelectedPath.value = false
  expandedPaths.value = []
  if (currentLocation.value) {
    await loadRootFiles()
  } else {
    fileNodesState.nodes = []
  }
}

const loadRootFiles = async () => {
  if (!currentLocation.value) return

  try {
    const nodes = await browseLocation(currentLocation.value, '')
    fileNodesState.nodes = nodes
  } catch {
    // Failed to load files from the location.
    showAlert(t('alerts.loadFilesFailed'), 'danger')
  }
}

const handleFileSelect = (selection: TreeSelection) => {
  selectedPath.value = selection.path
  canAddSelectedPath.value = selection.canAdd
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
  if (!currentLocation.value || node.type !== 'directory') return

  // Check if children already loaded to avoid duplicate requests.
  if (node.children_fetched) {
    return
  }

  // Set loading state on the node to show loading indicator.
  const setLoadingState = (nodes: FileNode[], targetPath: string, loading: boolean): boolean => {
    for (const node of nodes) {
      if (node.path === targetPath) {
        node.loading = loading
        return true
      }
      if (node.children && node.children.length > 0) {
        if (setLoadingState(node.children, targetPath, loading)) {
          return true
        }
      }
    }
    return false
  }

  try {
    setLoadingState(fileNodesState.nodes, node.path, true)
    fileNodesState.nodes = [...fileNodesState.nodes]

    const children = await browseLocation(currentLocation.value, node.path)

    // Find the node in the tree and update it with children.
    const updateNodeInTree = (nodes: FileNode[], targetPath: string, newChildren: FileNode[]): boolean => {
      for (const currentNode of nodes) {
        if (currentNode.path === targetPath) {
          currentNode.children = newChildren
          currentNode.children_fetched = true
          currentNode.loading = false
          return true
        }
        if (currentNode.children && currentNode.children.length > 0) {
          if (updateNodeInTree(currentNode.children, targetPath, newChildren)) {
            return true
          }
        }
      }
      return false
    }

    updateNodeInTree(fileNodesState.nodes, node.path, children)

    // Trigger reactivity by reassigning the array.
    fileNodesState.nodes = [...fileNodesState.nodes]
  } catch {
    // Failed to load directory contents.
    showAlert(t('alerts.loadFilesFailed'), 'danger')
    const updateErrorNode = (nodes: FileNode[], targetPath: string): boolean => {
      for (const currentNode of nodes) {
        if (currentNode.path === targetPath) {
          currentNode.children = []
          currentNode.children_fetched = false
          currentNode.loading = false
          return true
        }
        if (currentNode.children) {
          if (updateErrorNode(currentNode.children, targetPath)) {
            return true
          }
        }
      }
      return false
    }
    updateErrorNode(fileNodesState.nodes, node.path)
    fileNodesState.nodes = [...fileNodesState.nodes]
  }
}

const addSelectedPath = () => {
  if (
    !canAddSelectedPath.value
    || !selectedPath.value
    || !currentLocation.value
  ) {
    return
  }
  const pathToRestore = selectedPath.value

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
  const relativePath = selectedPath.value.startsWith('/')
    ? selectedPath.value.slice(1)
    : selectedPath.value
  const fullPath = basePath + relativePath

  const component: TransferComponent = {
    id: Date.now().toString(),
    path: fullPath,
    location: currentLocation.value,
  }
  transferComponents.value.push(component)

  // Restore focus to the same tree node after adding.
  nextTick(() => {
    selectedPath.value = pathToRestore
    canAddSelectedPath.value = true
    // Focus the tree view so keyboard navigation works.
    if (transferBrowserContainerRef.value) {
      transferBrowserContainerRef.value.focusTreeView()
    }
  })
}

const removeComponent = (id: string) => {
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

    showAlert(t('alerts.transferStarted', { name: transferName, config: configName }), 'success')
    resetForm()
  } catch {
    showAlert(apiError.value || t('alerts.transferFailed'), 'danger')
  }
}

const startTransferAndCloseDropdown = async (processingConfig: string) => {
  await startTransfer(processingConfig)
  closeDropdown()
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
  selectedPath.value = ''
  canAddSelectedPath.value = false
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
  const announcement = `${type === 'danger' ? 'Error' : type === 'warning' ? 'Warning' : type === 'success' ? 'Success' : 'Information'}: ${message}`
  announceToScreenReader(announcement)
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
  <main>
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
          type="button"
          :class="['btn', 'btn-browse', showBrowseTree ? 'btn-secondary' : 'btn-default']"
          :aria-label="showBrowseTree ? $t('transfer.hideBrowser') : $t('transfer.showBrowser')"
          :aria-expanded="showBrowseTree"
          @click="toggleBrowseTree"
        >
          {{ $t('transfer.browse') }}
        </button>
        <div
          class="btn-group dropdown"
          :class="{ open: showProcessingDropdown }"
          role="group"
          :aria-label="$t('transfer.submissionOptions')"
        >
          <button
            type="button"
            class="btn btn-success"
            :disabled="isTransferButtonDisabled"
            :aria-disabled="isTransferButtonDisabled"
            :aria-label="$t('transfer.startWithConfig', { config: 'default' })"
            @click="startTransfer('default')"
          >
            {{ $t('transfer.startTransfer') }}
          </button>
          <button
            ref="dropdownButtonRef"
            type="button"
            class="btn btn-success dropdown-toggle"
            :disabled="isTransferButtonDisabled"
            :aria-disabled="isTransferButtonDisabled"
            :aria-expanded="showProcessingDropdown"
            aria-haspopup="true"
            :aria-label="$t('transfer.showConfigOptions')"
            @click="toggleProcessingDropdown"
            @keydown="handleDropdownButtonKeyDown"
          >
            <span class="caret" />
          </button>
          <ul
            ref="dropdownMenuRef"
            class="dropdown-menu dropdown-menu-right"
            role="menu"
            @keydown="handleDropdownKeyDown"
          >
            <li
              v-for="config in processingConfigs"
              :key="config.pk"
              role="presentation"
            >
              <a
                href="#"
                role="menuitem"
                class="processing-config-choice"
                :aria-label="$t('transfer.startWithConfig', { config: config.name })"
                tabindex="-1"
                @click.prevent="startTransferAndCloseDropdown(config.pk)"
                @keydown.enter.prevent="startTransferAndCloseDropdown(config.pk)"
                @keydown.space.prevent="startTransferAndCloseDropdown(config.pk)"
                @keydown="handleDropdownKeyDown"
              >
                {{ $t('transfer.startWithConfig', { config: config.name }) }}
              </a>
            </li>
          </ul>
        </div>
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
          >Automatically approve this transfer for processing</span>
        </div>
      </div>
    </div>

    <PathContainer
      :components="transferComponents"
      :transfer-type="transferFormData.type"
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
        :selected-path="selectedPath"
        :can-add-selected-path="canAddSelectedPath"
        :transfer-type="transferFormData.type"
        :expanded-paths="expandedPaths"
        @update:current-location="handleLocationChangeEvent"
        @select="handleFileSelect"
        @expand="handleExpand"
        @toggle="handleToggle"
        @add="addSelectedPath"
      />
    </section>
  </main>
</template>

<style scoped>
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

.processing-config-choice {
  display: block;
  color: #333;
  text-decoration: none;
}

.processing-config-choice:hover {
  background-color: #f5f5f5;
  color: #333;
  text-decoration: none;
}
</style>

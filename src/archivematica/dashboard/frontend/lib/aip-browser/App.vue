<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { TreeView } from '@/shared/components'
import type { TreeNode } from '@/shared/components/TreeView.vue'
import { getFilesystemContents, openFilesystemDownload } from '@/shared/http'
import type { DirectoryEntry } from '@/shared/http'
import { useAbortController, useDelayedLoading } from '@/shared/composables'
import { decodeBase64, encodeBase64 } from '@/shared/encoding/base64'
import { useAsyncState } from '@vueuse/core'

const { t } = useI18n()

const props = defineProps<{
  // The initial directory to load.
  directory: string
}>()

// Load a directory and return its contents as TreeNodes.
const fetchDirectory = async (path: string): Promise<TreeNode[]> => {
  if (!path) {
    throw new Error(t('aipBrowser.noDirectoryProvided'))
  }
  const data = await getFilesystemContents(path, { signal: createSignal() })
  const rootLabel = path.split('/').filter(Boolean).pop() || path
  const root: TreeNode = {
    id: path,
    label: rootLabel,
    path,
    children: data.children?.map(child =>
      decodeEntry(child, path),
    ) ?? [],
  }
  return [root]
}

// State for the currently loaded directory contents.
const {
  state: items,
  isLoading,
  error,
  execute,
} = useAsyncState(fetchDirectory, [], {
  immediate: false,
  onError(err) {
    if (err instanceof Error && err.name === 'AbortError') {
      return
    }
  },
})

// Load a directory, aborting any ongoing load.
const load = (path: string) => {
  abort()
  execute(0, path)
}

// Whether to show the loading spinner.
const showSpinner = useDelayedLoading(isLoading, 200)

// Whether loading has finished (successfully or with error).
const isFinished = computed(() => !isLoading.value)
// Controller to abort ongoing fetch requests.
const { createSignal, abort } = useAbortController()

// Join base path and name to form a full path.
const joinPath = (basePath: string, name: string) => {
  if (!basePath) return name
  return `${basePath.replace(/\/$/, '')}/${name}`
}

// Decode a directory entry from the API response into a TreeNode.
const decodeEntry = (entry: DirectoryEntry, currentPath: string): TreeNode => {
  const decodedName = entry.name ? decodeBase64(entry.name) : ''
  const path = joinPath(currentPath, decodedName)
  const children = entry.children?.map(child => decodeEntry(child, path))
  return {
    id: path,
    label: decodedName || path,
    path,
    children,
  }
}

// Handle selection of a tree node.
const handleSelect = (node: TreeNode) => {
  // In this tree, directories carry a `children` array (including empty dirs),
  // while files omit `children`.
  const isFile = node.children === undefined
  if (!isFile || !node.path) return
  const encodedPath = encodeBase64(node.path)
  openFilesystemDownload(encodedPath)
}

// Retry loading the current directory.
const retryLoad = () => {
  load(props.directory)
}

// Human-readable error message.
const errorMessage = computed(() => {
  if (!error.value) return null
  if (error.value instanceof Error) return error.value.message
  return String(error.value)
})

// Load the initial directory on mount.
onMounted(() => {
  load(props.directory)
})

</script>

<template>
  <section :aria-label="t('aipBrowser.ariaLabel')">
    <!-- Loading spinner. -->
    <div
      v-if="showSpinner"
      class="aip-browser-status"
      role="status"
      aria-live="polite"
    >
      <i
        class="fa fa-spinner fa-spin"
        aria-hidden="true"
      />
      <span>{{ t('aipBrowser.loading') }}</span>
    </div>

    <!-- Error retry. -->
    <div
      v-else-if="errorMessage"
      class="alert alert-danger"
      role="alert"
      aria-live="assertive"
    >
      <h4>{{ t('aipBrowser.loadFailed') }}</h4>
      <div><p>{{ errorMessage }}</p></div>
      <button
        type="button"
        class="btn btn-default"
        @click="retryLoad"
      >
        {{ t('aipBrowser.retry') }}
      </button>
    </div>

    <!-- Empty state. -->
    <div
      v-else-if="isFinished && items.length === 0"
      class="aip-browser-status"
    >
      <span>{{ t('aipBrowser.empty') }}</span>
    </div>

    <!-- Treeview. -->
    <TreeView
      :items="items"
      :frame-style="'framed'"
      :auto-focus-on-items-change="true"
      :auto-focus-target="'first'"
      @select="handleSelect"
    >
      <!-- Scoped slot used to customize the icon displayed for each node. -->
      <template #icon="{ node, isExpanded, isFocused }">
        <i
          v-if="node?.children"
          class="fa"
          :class="isExpanded ? 'fa-folder-open' : 'fa-folder'"
        />
        <span
          v-else
          class="tree-node-icon-file"
          :class="{ 'tree-node-icon-focused': isFocused }"
        >
          <i class="fa fa-file tree-node-icon-default" />
          <i class="fa fa-download tree-node-icon-download" />
        </span>
      </template>
    </TreeView>
  </section>
</template>

<style scoped>
.aip-browser-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: #555;
}

section :deep(.tree) {
  --tree-focus-outline: none;
  --tree-focus-outline-offset: 0;
}

.tree-node-icon-download {
  display: none;
  color: #5f6368;
}

/* Toggle file icons to show download icon on hover or focus. */
:deep(.tree-node-file:hover .tree-node-icon-default) { display: none;}
:deep(.tree-node-file:hover .tree-node-icon-download) { display: inline-block; }
:deep(.tree-node-icon-file.tree-node-icon-focused .tree-node-icon-default) { display: none; }
:deep(.tree-node-icon-file.tree-node-icon-focused .tree-node-icon-download) { display: inline-block; }
</style>

import { ref, computed, type Ref } from 'vue'
import { useAsyncState } from '@vueuse/core'
import { useI18n } from 'vue-i18n'
import { encodeBase64, decodeBase64 } from '@/shared/encoding/base64'
import { getFilesystemChildren, type FilesystemBrowseResponse } from '@/shared/http'

export type MetadataTreeNode = {
  readonly id: string
  readonly path: string
  readonly kind: 'file' | 'directory'
  label: string
  display?: string
  children?: MetadataTreeNode[]
  loaded?: boolean
  loadError?: string
}

function joinPath(base: string, name: string): string {
  if (!base) return name
  return `${base.replace(/\/$/, '')}/${name}`
}

function buildDisplayString(properties?: Record<string, unknown>): string | undefined {
  const displayString = properties?.['display_string']
  return typeof displayString === 'string' ? displayString : undefined
}

function buildNodes(response: FilesystemBrowseResponse, parentPath: string): MetadataTreeNode[] {
  const directorySet: Set<string> = new Set(response.directories)
  return response.entries.map((entry): MetadataTreeNode => {
    const decodedName: string = decodeBase64(entry)
    const isDirectory: boolean = directorySet.has(entry)
    const path: string = joinPath(parentPath, decodedName)
    return {
      id: path,
      label: decodedName,
      display: buildDisplayString(response.properties?.[entry]),
      path,
      kind: isDirectory ? 'directory' : 'file',
      children: isDirectory ? [] : undefined,
      loaded: false,
    }
  })
}

function normalizeError(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message
  if (typeof err === 'string') return err
  return fallback
}

export function useFilesystemTree() {
  const { t } = useI18n()

  // Top-level tree nodes; each node may include nested children.
  const items: Ref<MetadataTreeNode[]> = ref([])

  // activeRequestId makes sure we only apply results from the latest load, so
  // stale responses don’t overwrite current tree data.
  const activeRequestId: Ref<number> = ref(0)

  // loadChildrenInternal loads the children of the given node.
  async function loadChildrenInternal(node: MetadataTreeNode, locationUUID: string, requestId?: number): Promise<void> {
    if (node.kind !== 'directory') return
    if (node.loaded) return
    if (requestId != null && requestId !== activeRequestId.value) return
    node.loadError = undefined
    try {
      const response = await getFilesystemChildren(
        locationUUID,
        encodeBase64(node.path),
      )
      if (requestId != null && requestId !== activeRequestId.value) return
      node.children = buildNodes(response, node.path)
      node.loaded = true
    } catch (err: unknown) {
      if (requestId != null && requestId !== activeRequestId.value) return
      node.loadError = normalizeError(err, t('metadata.loadFailed'))
      node.children = []
      node.loaded = false
    }
  }

  // Load the root node using an async state wrapper.
  const {
    isLoading,
    error: rootError,
    execute: executeRootLoad,
  } = useAsyncState(
    async (locationUUID: string, locationPath: string): Promise<void> => {
      const requestId = ++activeRequestId.value
      items.value = []
      if (!locationUUID || !locationPath) {
        throw new Error(t('metadata.noDirectorySelected'))
      }

      const rootNode: MetadataTreeNode = {
        id: locationPath,
        label: locationPath.split('/').filter(Boolean).pop() ?? locationPath,
        path: locationPath,
        kind: 'directory',
        children: [],
        loaded: false,
      }

      items.value = [rootNode]
      await loadChildrenInternal(rootNode, locationUUID, requestId)

      // Ignore stale request completion after a newer root request starts.
      if (requestId !== activeRequestId.value) return

      if (rootNode.loadError != null) {
        items.value = []
        throw new Error(rootNode.loadError)
      }
    },
    undefined,
    {
      immediate: false,
      resetOnExecute: true,
      throwError: false,
    },
  )

  // Load the root node for the given location.
  async function loadRoot(locationUUID: string, locationPath: string): Promise<void> {
    await executeRootLoad(0, locationUUID, locationPath)
  }

  // Load the children of the given node.
  async function loadChildren(node: MetadataTreeNode, locationUUID: string): Promise<void> {
    await loadChildrenInternal(node, locationUUID)
  }

  // Retry loading the children of the given node after a failure.
  async function retry(node: MetadataTreeNode, locationUUID: string): Promise<void> {
    node.loadError = undefined
    node.loaded = false
    await loadChildren(node, locationUUID)
  }

  return {
    items,
    loading: computed((): boolean => isLoading.value),
    error: computed((): string | null => {
      if (rootError.value == null) return null
      return normalizeError(rootError.value, t('metadata.loadFailed'))
    }),
    loadRoot,
    loadChildren,
    retry,
  }
}

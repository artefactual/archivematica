import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { searchArchivalStorage } from '@/shared/http'
import type { SearchResponse } from '../types'

export const useArchivalStorageSearch = () => {
  const { t } = useI18n()

  const pendingRequests = ref(0)
  const loading = computed(() => pendingRequests.value > 0)
  const error = ref<string | null>(null)
  let latestRequestId = 0

  const execute = async (params: URLSearchParams): Promise<SearchResponse> => {
    const requestId = latestRequestId + 1
    latestRequestId = requestId
    pendingRequests.value += 1
    if (requestId === latestRequestId) {
      error.value = null
    }

    try {
      return await searchArchivalStorage(params) as SearchResponse
    } catch (err) {
      if (requestId === latestRequestId) {
        error.value = err instanceof Error ? err.message : t('archivalStorage.searchRequestFailed')
      }
      throw err
    } finally {
      pendingRequests.value = Math.max(pendingRequests.value - 1, 0)
    }
  }

  return {
    loading,
    error,
    execute,
  }
}

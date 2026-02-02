import { onScopeDispose } from 'vue'

// useAbortController provides a way to create and manage an AbortController
// within the lifecycle of a Vue component or composable.
export function useAbortController() {
  let controller: AbortController | null = null

  function createSignal() {
    controller?.abort()
    controller = new AbortController()
    return controller.signal
  }

  function abort() {
    controller?.abort()
    controller = null
  }

  onScopeDispose(abort)

  return { createSignal, abort }
}

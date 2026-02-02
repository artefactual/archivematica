import { readonly, ref, watch, type Ref } from 'vue'
import { useTimeoutFn } from '@vueuse/core'

// useDelayedLoading derives a delayed visibility state from a loading state.
// The visible state becomes true only if loading remains true for longer than
// the specified delay (default: 200ms). This is useful to avoid flickering of
// loading indicators for short loading periods.
export function useDelayedLoading(
  loading: Ref<boolean>,
  delay = 200,
) {
  const visible = ref(false)

  const { start, stop } = useTimeoutFn(() => {
    visible.value = true
  }, delay, { immediate: false })

  watch(loading, (isLoading) => {
    if (isLoading) {
      visible.value = false
      start()
    } else {
      stop()
      visible.value = false
    }
  })

  return readonly(visible)
}

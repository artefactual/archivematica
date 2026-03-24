<script setup lang="ts">
import src from './assets/silk/cog.svg'

defineOptions({
  inheritAttrs: false,
})

withDefaults(defineProps<{
  alt?: string
  size?: number | string
}>(), {
  alt: '',
  size: 16,
})
</script>

<template>
  <img
    v-bind="$attrs"
    class="silk-icon"
    :src="src"
    :alt="alt"
    :width="size"
    :height="size"
    decoding="async"
    draggable="false"
  >
</template>

<style scoped>
.silk-icon {
  display: inline-block;
  flex: none;
  vertical-align: text-bottom;
}
</style>

<script setup lang="ts">
import {
  TooltipArrow,
  TooltipContent,
  TooltipProvider,
  TooltipPortal,
  TooltipRoot,
  TooltipTrigger,
} from 'reka-ui'
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

defineProps<{
  content: string
}>()

const { t } = useI18n()

const open = ref(false)
const anchor = ref({
  x: 0,
  y: 0,
})

const position = computed(() => ({
  getBoundingClientRect: () =>
    ({
      width: 0,
      height: 0,
      left: anchor.value.x,
      right: anchor.value.x,
      top: anchor.value.y,
      bottom: anchor.value.y,
      ...anchor.value,
    } as DOMRect),
}))
</script>

<template>
  <TooltipProvider>
    <i
      class="help-tooltip-trigger fa fa-question-circle"
      :aria-label="t('misc.help')"
      @pointerenter="open = true"
      @pointerleave="open = false"
      @pointermove="(ev) => {
        anchor.x = ev.clientX
        anchor.y = ev.clientY
      }"
    />
    <TooltipRoot :open="open">
      <TooltipTrigger
        :reference="position"
        as-child
      />
      <TooltipPortal>
        <TooltipContent
          side="right"
          :side-offset="12"
          class="help-tooltip-content"
          update-position-strategy="always"
        >
          {{ content }}
          <TooltipArrow class="help-tooltip-arrow" />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>

<style>
.help-tooltip-trigger {
  cursor: help;
}

.help-tooltip-content {
  max-width: 280px;
  border: 1px solid #333;
  border-radius: 4px;
  background: #f7f5d1;
  color: #333;
  box-shadow: 4px 4px 4px #999;
  padding: 2px 5px;
  font-size: 12px;
  line-height: 1.35;
  z-index: 2000;
}

.help-tooltip-arrow {
  fill: #f7f5d1;
  stroke: #333;
}
</style>

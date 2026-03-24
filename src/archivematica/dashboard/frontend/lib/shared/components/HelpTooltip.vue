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
import { SilkInformationIcon } from '@/shared/icons'

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

const updateAnchorPosition = (ev: PointerEvent) => {
  anchor.value.x = ev.clientX
  anchor.value.y = ev.clientY
}
</script>

<template>
  <TooltipProvider>
    <SilkInformationIcon
      class="help-tooltip-trigger"
      :aria-label="t('misc.help')"
      alt=""
      size="16"
      @pointerenter="open = true"
      @pointerleave="open = false"
      @pointermove="updateAnchorPosition"
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
  width: 16px;
  height: 16px;
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

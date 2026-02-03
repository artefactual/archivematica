<script setup lang="ts">
import {
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogRoot,
  AlertDialogTitle,
} from 'reka-ui'

defineProps<{
  open: boolean
  title: string
  description: string
  details?: string[]
  confirmLabel: string
  cancelLabel: string
  pending?: boolean
}>()

const emit = defineEmits<{
  (event: 'update:open', value: boolean): void
  (event: 'confirm'): void
}>()
</script>

<template>
  <AlertDialogRoot
    :open="open"
    @update:open="emit('update:open', $event)"
  >
    <AlertDialogPortal>
      <AlertDialogOverlay class="monitor-dialog-overlay" />
      <AlertDialogContent
        class="modal fade in monitor-modal monitor-modal-visible"
      >
        <div
          class="modal-dialog"
          role="document"
        >
          <div class="modal-content">
            <div class="modal-header">
              <AlertDialogCancel as-child>
                <button
                  type="button"
                  class="close"
                  :disabled="pending === true"
                  aria-label="Close"
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              </AlertDialogCancel>
              <AlertDialogTitle
                as="h4"
                class="modal-title"
              >
                {{ title }}
              </AlertDialogTitle>
            </div>
            <div class="modal-body">
              <AlertDialogDescription as-child>
                <p><strong>{{ description }}</strong></p>
              </AlertDialogDescription>
              <p v-if="details && details.length > 0">
                <template
                  v-for="(line, index) in details"
                  :key="`${index}:${line}`"
                >
                  {{ line }}<br>
                </template>
              </p>
            </div>
            <div class="modal-footer">
              <button
                type="button"
                class="btn btn-primary"
                :disabled="pending === true"
                @click="emit('confirm')"
              >
                {{ confirmLabel }}
              </button>
              <AlertDialogCancel as-child>
                <button
                  type="button"
                  class="btn btn-default"
                  :disabled="pending === true"
                >
                  {{ cancelLabel }}
                </button>
              </AlertDialogCancel>
            </div>
          </div>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>

<style scoped>
.monitor-dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgb(0 0 0 / 45%);
  z-index: 2000;
}

.monitor-modal {
  z-index: 2001;
}

.monitor-modal-visible {
  display: block;
}
</style>

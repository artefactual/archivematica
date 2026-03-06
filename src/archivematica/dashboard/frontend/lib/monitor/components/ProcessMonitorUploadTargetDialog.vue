<script setup lang="ts">
import {
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'

defineProps<{
  open: boolean
  title: string
  description: string
  details?: string
  target: string
  targetLabel: string
  submitLabel: string
  cancelLabel: string
  loading?: boolean
  submitting?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (event: 'update:open', value: boolean): void
  (event: 'update:target', value: string): void
  (event: 'submit'): void
  (event: 'cancel'): void
}>()

const onTargetInput = (event: Event): void => {
  const target = event.target as HTMLInputElement | null
  emit('update:target', target?.value ?? '')
}

const onCancel = (): void => {
  emit('cancel')
  emit('update:open', false)
}
</script>

<template>
  <DialogRoot
    :open="open"
    @update:open="emit('update:open', $event)"
  >
    <DialogPortal>
      <DialogOverlay class="monitor-dialog-overlay" />
      <DialogContent
        class="modal fade in monitor-modal monitor-upload-modal monitor-modal-visible"
      >
        <div
          class="modal-dialog"
          role="document"
        >
          <div class="modal-content">
            <div class="modal-header">
              <button
                type="button"
                class="close"
                :disabled="submitting === true"
                aria-label="Close"
                @click="onCancel()"
              >
                <span aria-hidden="true">&times;</span>
              </button>
              <DialogTitle
                as="h4"
                class="modal-title"
              >
                {{ title }}
              </DialogTitle>
            </div>
            <div class="modal-body">
              <DialogDescription as-child>
                <p>{{ description }}</p>
              </DialogDescription>
              <p v-if="details">
                {{ details }}
              </p>
              <form @submit.prevent="emit('submit')">
                <div class="form-group">
                  <label>
                    {{ targetLabel }}
                  </label>
                  <input
                    class="form-control"
                    type="text"
                    :value="target"
                    :disabled="loading === true || submitting === true"
                    @input="onTargetInput($event)"
                  >
                </div>
                <p
                  v-if="error"
                  class="monitor-dialog-error"
                  role="alert"
                >
                  {{ error }}
                </p>
                <div class="modal-footer monitor-modal-footer">
                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="loading === true || submitting === true"
                  >
                    {{ submitLabel }}
                  </button>
                  <button
                    type="button"
                    class="btn btn-default"
                    :disabled="submitting === true"
                    @click="onCancel()"
                  >
                    {{ cancelLabel }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style scoped>
.monitor-dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgb(0 0 0 / 45%);
  z-index: 2000;
}

.monitor-dialog-error {
  margin: 0;
  color: #b93c3c;
}

.monitor-modal {
  z-index: 2001;
}

.monitor-modal-visible {
  display: block;
}

.monitor-modal-footer {
  margin-top: 16px;
  padding: 0;
  border-top: 0;
}
</style>

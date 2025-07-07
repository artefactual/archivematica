<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { TransferComponent } from '@/shared/models'

const { t } = useI18n()

defineProps<{
  components: TransferComponent[]
  transferType: string
}>()

defineEmits<{
  edit: [id: string]
  remove: [id: string]
}>()
</script>

<template>
  <div id="path_container">
    <div
      v-for="(component, index) in components"
      :id="`transfer-component-path-item-${index + 1}`"
      :key="component.id"
      class="transfer-component-item"
    >
      <span class="transfer_path">{{ component.path }}</span>
      <span class="transfer_path_icons">
        <button
          v-if="transferType === 'disk image'"
          type="button"
          class="transfer_path_edit_btn"
          :aria-label="t('fileBrowser.editComponent', { path: component.path })"
          @click="$emit('edit', component.id)"
        >
          <i
            class="fa fa-edit"
            aria-hidden="true"
          />
        </button>
        <button
          type="button"
          class="transfer_path_delete_btn"
          :aria-label="t('fileBrowser.removeComponent', { path: component.path })"
          @click="$emit('remove', component.id)"
        >
          <i
            class="fa fa-trash"
            aria-hidden="true"
          />
        </button>
      </span>
    </div>
  </div>
</template>

<style scoped>
#path_container {
  width: 950px;
  margin-bottom: 10px;
}

.transfer-component-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.transfer_path {
  flex: 1;
  margin-right: 10px;
  word-break: break-all;
}

.transfer_path_icons {
  display: flex;
  align-items: center;
  gap: 0.5em;
  flex-shrink: 0;
}

.transfer_path_delete_btn,
.transfer_path_edit_btn {
  padding: 4px 6px;
  background: none;
  border: 1px solid transparent;
  border-radius: 3px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
}

.transfer_path_delete_btn:hover,
.transfer_path_edit_btn:hover {
  color: #333;
  background-color: #f5f5f5;
  border-color: #ddd;
}

.transfer_path_delete_btn:focus,
.transfer_path_edit_btn:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}

.transfer_path_delete_btn:hover {
  color: #d9534f;
  border-color: #d9534f;
}

.transfer_path_edit_btn:hover {
  color: #337ab7;
  border-color: #337ab7;
}
</style>

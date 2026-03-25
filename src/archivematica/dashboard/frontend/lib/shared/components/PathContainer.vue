<script setup lang="ts">
type LabelResolver = (path: string) => string

type PathItem = {
  id: string
  path: string
}
const props = withDefaults(defineProps<{
  items: PathItem[]
  showEdit?: boolean
  editLabel?: LabelResolver
  removeLabel: LabelResolver
}>(), {
  showEdit: false,
  editLabel: () => '',
})

const emit = defineEmits<{
  edit: [id: string]
  remove: [id: string]
}>()
</script>

<template>
  <div class="path-container">
    <div
      v-for="(item, index) in items"
      :id="`path-item-${index + 1}`"
      :key="item.id"
      class="path-item"
    >
      <span class="path">{{ item.path }}</span>
      <span class="actions">
        <button
          v-if="showEdit"
          type="button"
          class="edit-btn"
          :aria-label="props.editLabel(item.path)"
          @click="emit('edit', item.id)"
        >
          <i
            class="fa fa-edit"
            aria-hidden="true"
          />
        </button>
        <button
          type="button"
          class="delete-btn"
          :aria-label="props.removeLabel(item.path)"
          @click="emit('remove', item.id)"
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
.path-container {
  width: 950px;
  margin-bottom: 10px;
}

.path-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.path {
  flex: 1;
  margin-right: 10px;
  word-break: break-all;
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.5em;
  flex-shrink: 0;
}

.actions button {
  padding: 4px 6px;
  background: none;
  border: 1px solid transparent;
  border-radius: 3px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
}

.actions button:hover,
.actions button:focus {
  background-color: #f5f5f5;
}

.actions button:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}

.delete-btn:hover,
.delete-btn:focus {
  color: #d9534f;
  border-color: #d9534f;
}

.edit-btn:hover,
.edit-btn:focus {
  color: #337ab7;
  border-color: #337ab7;
}
</style>

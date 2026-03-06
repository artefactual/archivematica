<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// The currently selected location UUID, controlled by the parent component.
const selectedLocationUUID = defineModel<string>({ required: true })

defineProps<{
  // The available source directories.
  locationOptions: ReadonlyArray<[string, string]>
  // Whether the form is currently submitting.
  submitting: boolean
}>()

const emit = defineEmits<{
  browse: []
  submit: []
}>()

// Focus the select element on mount.
const selectRef = ref<HTMLSelectElement | null>(null)
const browseButtonRef = ref<HTMLButtonElement | null>(null)
onMounted(() => {
  nextTick(() => {
    selectRef.value?.focus()
  })
})

const focusBrowseButton = () => {
  browseButtonRef.value?.focus()
}

defineExpose({
  focusBrowseButton,
})
</script>

<template>
  <div class="controls">
    <label
      class="label"
      for="metadata-source-select"
    >
      {{ t('metadata.sourceLocation') }}
    </label>
    <select
      id="metadata-source-select"
      ref="selectRef"
      v-model="selectedLocationUUID"
      class="form-control"
    >
      <option
        v-for="[id, path] in locationOptions"
        :key="id"
        :value="id"
      >
        {{ path }}
      </option>
    </select>
    <button
      ref="browseButtonRef"
      type="button"
      class="btn btn-default"
      :disabled="submitting"
      @click="emit('browse')"
    >
      {{ t('metadata.browse') }}
    </button>
    <button
      type="button"
      class="btn btn-success"
      :disabled="submitting"
      @click="emit('submit')"
    >
      {{ t('metadata.addFiles') }}
    </button>
  </div>
</template>

<style scoped>
.controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.label {
  margin: 0;
}
</style>

<script setup lang="ts">
import { computed } from 'vue'
import type { MatcherLabels } from '../types'
import type { ObjectSelectionRow } from '../types'

const props = defineProps<{
  labels: MatcherLabels
  objectFilter: string
  rows: ObjectSelectionRow[]
  selectedObjectsCount: number
  allVisibleObjectsSelected: boolean
  someVisibleObjectsSelected: boolean
}>()

const emit = defineEmits<{
  'update:objectFilter': [value: string]
  'selectAllChange': [event: Event]
  'objectChange': [event: Event, uuid: string, index: number]
}>()

const objectFilterModel = computed({
  get: () => props.objectFilter,
  set: (value: string) => emit('update:objectFilter', value),
})
</script>

<template>
  <section class="as-matcher-pane panel panel-default">
    <div class="panel-heading as-matcher-pane-heading">
      <h3 class="panel-title">
        {{ labels.objects }}
      </h3>
      <div class="as-matcher-pane-heading-meta">
        <span class="label label-default as-matcher-context-chip">
          {{ labels.selectedObjects }}: {{ selectedObjectsCount }}
        </span>
        <span class="label label-default">{{ rows.length }}</span>
      </div>
    </div>
    <div class="panel-body as-matcher-pane-body">
      <div class="as-matcher-pane-filter">
        <div class="input-group input-group-sm">
          <span
            class="input-group-addon"
            aria-hidden="true"
          >
            <i class="fa fa-search" />
          </span>
          <input
            v-model="objectFilterModel"
            type="text"
            class="form-control"
            :placeholder="labels.filterObjects"
          >
        </div>
      </div>

      <div class="as-matcher-select-all">
        <label>
          <input
            type="checkbox"
            :checked="allVisibleObjectsSelected"
            :indeterminate="someVisibleObjectsSelected"
            @change="$emit('selectAllChange', $event)"
          >
          {{ labels.selectAll }}
        </label>
      </div>

      <div
        class="as-matcher-object-list"
        role="list"
      >
        <div
          v-for="(item, index) in rows"
          :key="item.uuid"
          class="as-matcher-object-row"
          :class="{ 'is-disabled': item.isPaired }"
          role="listitem"
        >
          <label class="as-matcher-object-label">
            <input
              type="checkbox"
              :checked="item.isChecked"
              :disabled="item.isPaired"
              @change="$emit('objectChange', $event, item.uuid, index)"
            >
            <span :title="item.path">{{ item.path }}</span>
          </label>
        </div>
      </div>
    </div>
  </section>
</template>

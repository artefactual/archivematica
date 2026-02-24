<script setup lang="ts">
import { computed } from 'vue'
import type { MatcherLabels, ResourceRow, ResourceSortKey } from '../types'

const props = defineProps<{
  labels: MatcherLabels
  resourceFilter: string
  rows: ResourceRow[]
  selectedResourceId: string | null
  pairedResourceIds: Set<string>
  sortIconClass: (key: ResourceSortKey) => string
}>()

const emit = defineEmits<{
  'update:resourceFilter': [value: string]
  'sort': [key: ResourceSortKey]
  'selectResource': [resourceId: string]
}>()

const resourceFilterModel = computed({
  get: () => props.resourceFilter,
  set: (value: string) => emit('update:resourceFilter', value),
})
</script>

<template>
  <section class="as-matcher-pane panel panel-default">
    <div class="panel-heading as-matcher-pane-heading">
      <h3 class="panel-title">
        {{ labels.resources }}
      </h3>
      <span class="label label-default">{{ rows.length }}</span>
    </div>
    <div class="panel-body as-matcher-pane-body as-matcher-pane-body-tight">
      <div class="as-matcher-pane-filter">
        <div class="input-group input-group-sm">
          <span
            class="input-group-addon"
            aria-hidden="true"
          >
            <i class="fa fa-search" />
          </span>
          <input
            v-model="resourceFilterModel"
            type="text"
            class="form-control"
            :placeholder="labels.filterResources"
          >
        </div>
      </div>
    </div>
    <div class="as-matcher-table-wrap">
      <table class="table table-condensed table-hover as-matcher-table">
        <thead>
          <tr>
            <th>
              <button
                type="button"
                class="as-matcher-sort-btn"
                @click="$emit('sort', 'sortPosition')"
              >
                {{ labels.level }}
                <i
                  :class="sortIconClass('sortPosition')"
                  aria-hidden="true"
                />
              </button>
            </th>
            <th>
              <button
                type="button"
                class="as-matcher-sort-btn"
                @click="$emit('sort', 'title')"
              >
                {{ labels.title }}
                <i
                  :class="sortIconClass('title')"
                  aria-hidden="true"
                />
              </button>
            </th>
            <th>
              <button
                type="button"
                class="as-matcher-sort-btn"
                @click="$emit('sort', 'identifier')"
              >
                {{ labels.identifier }}
                <i
                  :class="sortIconClass('identifier')"
                  aria-hidden="true"
                />
              </button>
            </th>
            <th>
              <button
                type="button"
                class="as-matcher-sort-btn"
                @click="$emit('sort', 'dates')"
              >
                {{ labels.dates }}
                <i
                  :class="sortIconClass('dates')"
                  aria-hidden="true"
                />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.id"
            class="as-matcher-resource-row"
            :class="{
              'is-selected': props.selectedResourceId === row.resourceId,
              'is-paired': props.pairedResourceIds.has(row.resourceId),
            }"
            tabindex="0"
            @click="$emit('selectResource', row.resourceId)"
            @keydown.enter.prevent="$emit('selectResource', row.resourceId)"
            @keydown.space.prevent="$emit('selectResource', row.resourceId)"
          >
            <td>{{ row.levelOfDescription }}</td>
            <td>
              <span
                class="as-matcher-resource-title"
                :style="{ paddingLeft: `${row.depth * 1.15}rem` }"
                :title="row.title"
              >
                <span
                  v-if="row.depth"
                  class="as-matcher-resource-branch"
                  aria-hidden="true"
                >↳</span>
                {{ row.title }}
              </span>
            </td>
            <td>{{ row.identifier }}</td>
            <td>{{ row.dates }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

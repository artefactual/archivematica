<script setup lang="ts">
import type { MatcherLabels } from '../types'
import type { MatchRow } from '../types'

defineProps<{
  labels: MatcherLabels
  pairs: MatchRow[]
  deletingPairIds: Set<number>
}>()

defineEmits<{
  removePair: [pair: MatchRow]
}>()
</script>

<template>
  <section class="as-matcher-pane panel panel-default">
    <div class="panel-heading as-matcher-pane-heading">
      <h3 class="panel-title">
        {{ labels.pairs }}
      </h3>
      <span class="label label-default">{{ pairs.length }}</span>
    </div>
    <div class="as-matcher-table-wrap">
      <table class="table table-condensed table-hover as-matcher-table">
        <thead>
          <tr>
            <th>{{ labels.file }}</th>
            <th>{{ labels.level }}</th>
            <th>{{ labels.title }}</th>
            <th>{{ labels.identifier }}</th>
            <th>{{ labels.dates }}</th>
            <th class="as-matcher-actions-col" />
          </tr>
        </thead>
        <tbody>
          <tr v-if="pairs.length === 0">
            <td
              colspan="6"
              class="text-muted"
            >
              {{ labels.noPairsYet }}
            </td>
          </tr>
          <tr
            v-for="pair in pairs"
            :key="pair.localId"
            class="atk-matcher-match-item"
          >
            <td :title="pair.objectPath">
              {{ pair.objectPath }}
            </td>
            <td>{{ pair.levelOfDescription }}</td>
            <td :title="pair.title">
              {{ pair.title }}
            </td>
            <td>{{ pair.identifier }}</td>
            <td>{{ pair.dates }}</td>
            <td class="as-matcher-actions-col">
              <button
                type="button"
                class="delete-btn"
                :title="labels.deleteMatch"
                :disabled="deletingPairIds.has(pair.localId)"
                @click="$emit('removePair', pair)"
              >
                <i
                  class="fa fa-trash"
                  aria-hidden="true"
                />
                <span class="sr-only">{{ labels.deleteMatch }}</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

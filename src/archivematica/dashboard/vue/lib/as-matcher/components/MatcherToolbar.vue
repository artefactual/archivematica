<script setup lang="ts">
import type { MatcherLabels } from '../types'

defineProps<{
  labels: MatcherLabels
  urls: {
    review: string
    reset: string | null
  }
  pairDisabled: boolean
}>()

defineEmits<{
  pair: []
}>()
</script>

<template>
  <div class="as-matcher-toolbar well well-sm">
    <div class="as-matcher-toolbar-body">
      <div class="as-matcher-toolbar-group as-matcher-toolbar-actions">
        <a
          v-if="urls.reset"
          class="btn btn-default btn-sm"
          :href="urls.reset"
        >
          <i
            class="fa fa-undo"
            aria-hidden="true"
          />
          {{ labels.restartMatching }}
        </a>
        <button
          v-else
          type="button"
          class="btn btn-default btn-sm"
          disabled
        >
          <i
            class="fa fa-undo"
            aria-hidden="true"
          />
          {{ labels.restartMatching }}
        </button>
        <a
          class="btn btn-default btn-sm"
          :href="urls.review"
        >
          <i
            class="fa fa-list-ul"
            aria-hidden="true"
          />
          {{ labels.reviewMatches }}
        </a>
        <button
          type="button"
          class="btn btn-primary btn-sm"
          :disabled="pairDisabled"
          @click="$emit('pair')"
        >
          <i
            class="fa fa-link"
            aria-hidden="true"
          />
          {{ labels.pairSelectedObjects }}
        </button>
      </div>
    </div>
  </div>
</template>

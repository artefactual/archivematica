<script setup lang="ts">
import type { MatcherLabels } from '../types'

defineProps<{
  labels: MatcherLabels
  reviewUrl: string
  resetUrl: string
  resetAvailable: boolean
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
          v-if="resetAvailable"
          class="btn btn-default btn-sm"
          :href="resetUrl"
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
          :href="reviewUrl"
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

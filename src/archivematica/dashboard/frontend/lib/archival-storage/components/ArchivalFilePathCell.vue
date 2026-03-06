<script setup lang="ts">
import { I18nT, useI18n } from 'vue-i18n'

defineProps<{
  path: string
  rawUrl: string
}>()

const { t } = useI18n()
</script>

<template>
  <I18nT
    keypath="archivalStorage.filePathWithRawTemplate"
    scope="global"
    tag="span"
  >
    <template #path>
      {{ path }}
    </template>
    <template #link>
      <a :href="rawUrl">{{ t('archivalStorage.viewRaw') }}</a>
    </template>
  </I18nT>
</template>

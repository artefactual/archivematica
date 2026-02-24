<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

type PaginationPageItem = number | 'ellipsis'

const props = defineProps<{
  pageIndex: number
  pageCount: number
  pageSize: number
  pageSizeOptions: number[]
  canPreviousPage: boolean
  canNextPage: boolean
  startRow: number
  endRow: number
  filteredCount: number
  totalCount: number
}>()
const { t, locale } = useI18n()

const emit = defineEmits<{
  setPageIndex: [pageIndex: number]
  previousPage: []
  nextPage: []
  setPageSize: [pageSize: number]
}>()

const pageItems = computed<PaginationPageItem[]>(() => {
  if (props.pageCount <= 1) {
    return [0]
  }

  const current = props.pageIndex
  const last = props.pageCount - 1
  const items: PaginationPageItem[] = []

  const pushPage = (value: number) => {
    if (!items.includes(value)) {
      items.push(value)
    }
  }

  pushPage(0)

  const start = Math.max(1, current - 2)
  const end = Math.min(last - 1, current + 2)

  if (start > 1) {
    items.push('ellipsis')
  }

  for (let page = start; page <= end; page += 1) {
    pushPage(page)
  }

  if (end < last - 1) {
    items.push('ellipsis')
  }

  pushPage(last)

  return items
})

const onPageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement | null
  if (!target) {
    return
  }
  const nextSize = Number(target.value)
  if (Number.isFinite(nextSize) && nextSize > 0) {
    emit('setPageSize', nextSize)
  }
}

const numberFormatter = computed(() => new Intl.NumberFormat(locale.value))
const formatNumber = (value: number) => numberFormatter.value.format(value)

const infoText = computed(() => {
  const params = {
    start: formatNumber(props.startRow),
    end: formatNumber(props.endRow),
    total: formatNumber(props.totalCount),
    filtered: formatNumber(props.filteredCount),
  }
  if (props.filteredCount < props.totalCount) {
    return t('misc.pagination.filteredInfoTemplate', params)
  }
  return t('misc.pagination.infoTemplate', {
    start: params.start,
    end: params.end,
    total: params.total,
  })
})

const lengthTemplateParts = computed(() =>
  t('misc.pagination.lengthTemplate', { select: '{select}' }).split('{select}'),
)
</script>

<template>
  <div class="fpr-pagination">
    <div class="fpr-pagination-info text-muted">
      {{ infoText }}
    </div>

    <div class="fpr-pagination-controls">
      <div class="fpr-pagination-length">
        <label class="control-label">
          <template v-if="lengthTemplateParts[0]">{{ lengthTemplateParts[0] }}</template>
          <select
            class="form-control input-sm"
            :value="pageSize"
            @change="onPageSizeChange"
          >
            <option
              v-for="size in pageSizeOptions"
              :key="size"
              :value="size"
            >
              {{ size }}
            </option>
          </select>
          <template v-if="lengthTemplateParts[1]">{{ lengthTemplateParts[1] }}</template>
        </label>
      </div>

      <nav
        v-if="pageCount > 1"
        :aria-label="t('misc.pagination.ariaLabel')"
      >
        <ul class="pagination pagination-sm fpr-pagination-list">
          <li :class="{ disabled: !canPreviousPage }">
            <button
              type="button"
              :aria-label="t('misc.pagination.previous')"
              :disabled="!canPreviousPage"
              @click="emit('previousPage')"
            >
              {{ t('misc.pagination.previous') }}
            </button>
          </li>

          <li
            v-for="(item, index) in pageItems"
            :key="`${item}-${index}`"
            :class="{ active: item !== 'ellipsis' && item === pageIndex, disabled: item === 'ellipsis' }"
          >
            <span v-if="item === 'ellipsis'">…</span>
            <button
              v-else
              type="button"
              :aria-current="item === pageIndex ? 'page' : undefined"
              @click="emit('setPageIndex', item)"
            >
              {{ item + 1 }}
            </button>
          </li>

          <li :class="{ disabled: !canNextPage }">
            <button
              type="button"
              :aria-label="t('misc.pagination.next')"
              :disabled="!canNextPage"
              @click="emit('nextPage')"
            >
              {{ t('misc.pagination.next') }}
            </button>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.fpr-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
}

.fpr-pagination-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.fpr-pagination-length label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: normal;
}

.fpr-pagination-length select {
  width: auto;
  min-width: 72px;
}

.fpr-pagination-list {
  margin: 0;
}

.fpr-pagination-list > li > button {
  position: relative;
  float: left;
  padding: 6px 12px;
  line-height: 1.42857143;
  color: #337ab7;
  text-decoration: none;
  background-color: #fff;
  border: 1px solid #ddd;
  margin-left: -1px;
}

.fpr-pagination-list > li:first-child > button {
  margin-left: 0;
  border-top-left-radius: 3px;
  border-bottom-left-radius: 3px;
}

.fpr-pagination-list > li:last-child > button {
  border-top-right-radius: 3px;
  border-bottom-right-radius: 3px;
}

.fpr-pagination-list > li > button:hover {
  z-index: 2;
  color: #23527c;
  background-color: #eee;
  border-color: #ddd;
}

.fpr-pagination-list > li.active > button {
  z-index: 3;
  color: #fff;
  background-color: #337ab7;
  border-color: #337ab7;
  cursor: default;
}

.fpr-pagination-list > li.disabled > button {
  color: #777;
  background-color: #fff;
  border-color: #ddd;
  cursor: not-allowed;
}

.fpr-pagination-list > li.disabled > span {
  position: relative;
  float: left;
  padding: 6px 12px;
  line-height: 1.42857143;
  color: #777;
  text-decoration: none;
  background-color: #fff;
  border: 1px solid #ddd;
  margin-left: -1px;
}

@media (max-width: 767px) {
  .fpr-pagination {
    flex-direction: column;
    align-items: stretch;
  }

  .fpr-pagination-controls {
    margin-left: 0;
    justify-content: space-between;
  }
}
</style>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

defineOptions({ name: 'ResultsPagination' })

type PaginationPageItem = number | 'ellipsis'
type ControlMode = 'pages' | 'edges'
type InfoStyle = 'plain' | 'chip'
type PageSizeLabelMode = 'template' | 'show'

const props = withDefaults(defineProps<{
  pageIndex: number
  pageCount: number
  pageSize: number
  pageSizeOptions: number[]
  canPreviousPage: boolean
  canNextPage: boolean
  startRow: number
  endRow: number
  totalCount: number
  filteredCount?: number
  controlMode?: ControlMode
  infoStyle?: InfoStyle
  pageSizeLabelMode?: PageSizeLabelMode
  showInfo?: boolean
  showPageSize?: boolean
}>(), {
  filteredCount: undefined,
  controlMode: 'pages',
  infoStyle: 'plain',
  pageSizeLabelMode: 'template',
  showInfo: true,
  showPageSize: true,
})

const emit = defineEmits<{
  setPageIndex: [pageIndex: number]
  previousPage: []
  nextPage: []
  firstPage: []
  lastPage: []
  setPageSize: [pageSize: number]
}>()

const { t, locale } = useI18n()

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

const filteredCount = computed(() => props.filteredCount ?? props.totalCount)

const infoText = computed(() => {
  const params = {
    start: formatNumber(props.startRow),
    end: formatNumber(props.endRow),
    total: formatNumber(props.totalCount),
    filtered: formatNumber(filteredCount.value),
  }
  if (filteredCount.value < props.totalCount) {
    return t('misc.pagination.filteredInfoTemplate', params)
  }
  return t('misc.pagination.infoTemplate', {
    start: params.start,
    end: params.end,
    total: params.total,
  })
})

const pageOfText = computed(() => t('misc.pagination.pageOfTemplate', {
  current: props.pageIndex + 1,
  total: props.pageCount,
}))

const lengthTemplateParts = computed(() =>
  t('misc.pagination.lengthTemplate', { select: '{select}' }).split('{select}'),
)
</script>

<template>
  <div
    :class="[
      'am-pagination',
      `am-pagination--${controlMode}`,
      `am-pagination--info-${infoStyle}`,
    ]"
  >
    <template v-if="controlMode === 'pages'">
      <div
        v-if="showInfo"
        class="am-pagination-info fpr-pagination-info"
        :class="{ 'text-muted': infoStyle === 'plain' }"
      >
        {{ infoText }}
      </div>

      <div class="am-pagination-controls fpr-pagination-controls">
        <div
          v-if="showPageSize"
          class="am-pagination-length fpr-pagination-length"
        >
          <label class="control-label">
            <template v-if="pageSizeLabelMode === 'template' && lengthTemplateParts[0]">
              {{ lengthTemplateParts[0] }}
            </template>
            <template v-else-if="pageSizeLabelMode === 'show'">
              {{ t('misc.pagination.show') }}
            </template>
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
            <template v-if="pageSizeLabelMode === 'template' && lengthTemplateParts[1]">
              {{ lengthTemplateParts[1] }}
            </template>
          </label>
        </div>

        <nav
          v-if="pageCount > 1"
          :aria-label="t('misc.pagination.ariaLabel')"
        >
          <ul class="pagination pagination-sm am-pagination-list fpr-pagination-list">
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
    </template>

    <template v-else>
      <div class="pagination-row">
        <button
          class="btn btn-default"
          :disabled="!canPreviousPage"
          @click="emit('firstPage')"
        >
          {{ t('misc.pagination.first') }}
        </button>
        <button
          class="btn btn-default"
          :disabled="!canPreviousPage"
          @click="emit('previousPage')"
        >
          {{ t('misc.pagination.previous') }}
        </button>
        <span>
          {{ pageOfText }}
        </span>
        <button
          class="btn btn-default"
          :disabled="!canNextPage"
          @click="emit('nextPage')"
        >
          {{ t('misc.pagination.next') }}
        </button>
        <button
          class="btn btn-default"
          :disabled="!canNextPage"
          @click="emit('lastPage')"
        >
          {{ t('misc.pagination.last') }}
        </button>
        <span
          v-if="showInfo"
          class="pagination-summary"
        >
          <span
            class="pagination-summary-chip"
            :class="{ 'pagination-summary-chip--plain': infoStyle === 'plain' }"
          >
            {{ infoText }}
          </span>
        </span>
        <label
          v-if="showPageSize"
          class="page-size-label"
        >
          <template v-if="pageSizeLabelMode === 'template' && lengthTemplateParts[0]">
            {{ lengthTemplateParts[0] }}
          </template>
          <template v-else>
            {{ t('misc.pagination.show') }}
          </template>
          <select
            class="form-control"
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
          <template v-if="pageSizeLabelMode === 'template' && lengthTemplateParts[1]">
            {{ lengthTemplateParts[1] }}
          </template>
        </label>
      </div>
    </template>
  </div>
</template>

<style scoped>
.am-pagination--pages {
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
}

.am-pagination--edges .pagination-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.am-pagination--edges .pagination-summary {
  flex: 1;
  text-align: center;
  min-width: 220px;
}

.am-pagination--edges .pagination-summary-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 2px 8px;
  border: 1px solid #d7d7d7;
  border-radius: 999px;
  background: #fff;
}

.am-pagination--edges .pagination-summary-chip--plain {
  border: none;
  padding: 0;
  border-radius: 0;
  background: transparent;
}

.am-pagination--edges .page-size-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 767px) {
  .am-pagination--pages {
    justify-content: center;
  }

  .fpr-pagination-controls {
    margin-left: 0;
    justify-content: center;
  }
}
</style>

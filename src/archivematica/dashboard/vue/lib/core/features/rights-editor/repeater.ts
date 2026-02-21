import $ from 'jquery'
import type { RightsEditorFormdataType, RightsFormdataRecord } from '@/shared/http'
import { listRightsFormdata, saveRightsFormdata } from '@/shared/http'
import { translate } from '@/shared/i18n/plain'

type JQueryElement = ReturnType<typeof $>

type RepeaterFieldType = 'input' | 'textarea' | 'select'

type RepeaterOptionConfig = {
  value: string
  label?: string
  labelKey?: string
}

type RepeaterFieldConfig = {
  name: string
  type?: RepeaterFieldType
  label?: string
  labelKey?: string
  options?: RepeaterOptionConfig[]
}

type RepeaterConfig = {
  idPrefix: string
  formdataType: RightsEditorFormdataType
  fields: RepeaterFieldConfig[]
}

const LOAD_FAILURE_MESSAGE = 'Failed to load existing records. You can still enter new data below.'
const SAVE_FAILURE_MESSAGE = 'Could not save changes. Try again.'
const SAVE_SUCCESS_MESSAGE = 'Saved'
const STATUS_HIDE_DELAY_MS = 1200
const ROW_STATUS_SELECTOR = '.repeating-ajax-data-status'
const saveQueueByRow = new WeakMap<Element, Promise<void>>()

const extractParentId = (idPrefix: string, id: string): string => id.slice(idPrefix.length)

const createFieldInput = (field: RepeaterFieldConfig): JQueryElement => {
  const type = field.type ?? 'textarea'
  if (type === 'input') {
    return $('<input>')
  }

  if (type === 'select') {
    const select = $('<select>')
    ;(field.options ?? []).forEach((option) => {
      const label = option.labelKey ? translate(option.labelKey) : (option.label ?? '')
      select.append($('<option>').attr('value', option.value).text(label))
    })
    return select
  }

  return $('<textarea></textarea>')
}

const createRecordRow = (
  config: RepeaterConfig,
  record: RightsFormdataRecord,
): JQueryElement => {
  const row = $('<div class="repeating-ajax-data-row"></div>').attr('data-record-id', String(record.id))

  config.fields.forEach((field) => {
    const label = field.labelKey ? translate(field.labelKey) : field.label
    if (label) {
      row.append($('<label>').text(label))
    }

    const fieldWrapper = $('<div class="repeating-ajax-data-field"></div>')
    const input = createFieldInput(field)
      .attr('name', field.name)
      .addClass('form-control')
      .val(record.values[field.name] ?? '')

    fieldWrapper.append(input)
    row.append(fieldWrapper)
  })

  return row
}

const renderRepeatingData = (
  container: JQueryElement,
  config: RepeaterConfig,
  records: RightsFormdataRecord[],
): JQueryElement[] => {
  container.empty()
  return records.map((record) => {
    const row = createRecordRow(config, record)
    container.append(row)
    return row
  })
}

const toggleManualRow = (container: JQueryElement, hasData: boolean): void => {
  const fieldset = container.closest('.repeating-ajax-data-fieldset')
  if (!fieldset.length) {
    return
  }
  fieldset.children('.repeating-ajax-data-row').toggle(!hasData)
}

const showLoadAlert = (container: JQueryElement, message: string): void => {
  const fieldset = container.closest('.repeating-ajax-data-fieldset')
  if (!fieldset.length) {
    return
  }

  let alert = fieldset.children('.repeating-ajax-data-alert')
  if (!alert.length) {
    alert = $('<div class="repeating-ajax-data-alert alert alert-warning"></div>')
    fieldset.prepend(alert)
  }
  alert.text(message)
}

const clearLoadAlert = (container: JQueryElement): void => {
  const fieldset = container.closest('.repeating-ajax-data-fieldset')
  if (!fieldset.length) {
    return
  }
  fieldset.children('.repeating-ajax-data-alert').remove()
}

const getStatusElement = (row: JQueryElement): JQueryElement => {
  let status = row.children(ROW_STATUS_SELECTOR)
  if (!status.length) {
    status = $('<small class="repeating-ajax-data-status text-muted" aria-live="polite"></small>').hide()
    row.append(status)
  }
  return status
}

const clearStatusTimer = (status: JQueryElement): void => {
  const timerId = Number(status.data('hideTimer') ?? 0)
  if (timerId) {
    window.clearTimeout(timerId)
    status.removeData('hideTimer')
  }
}

const showSavedStatus = (row: JQueryElement): void => {
  const status = getStatusElement(row)
  clearStatusTimer(status)
  status.removeClass('text-danger').addClass('text-muted').text(SAVE_SUCCESS_MESSAGE).show()

  const timerId = window.setTimeout(() => {
    status.fadeOut(200)
    status.removeData('hideTimer')
  }, STATUS_HIDE_DELAY_MS)

  status.data('hideTimer', timerId)
}

const showSaveError = (row: JQueryElement): void => {
  const status = getStatusElement(row)
  clearStatusTimer(status)
  status.removeClass('text-muted').addClass('text-danger').text(SAVE_FAILURE_MESSAGE).show()
}

const queueSaveForRow = (row: JQueryElement, task: () => Promise<void>): void => {
  const rowElement = row.get(0)
  if (!rowElement) {
    return
  }

  const previous = saveQueueByRow.get(rowElement) ?? Promise.resolve()
  const next = previous.catch(() => undefined).then(task)
  saveQueueByRow.set(rowElement, next)

  void next.finally(() => {
    if (saveQueueByRow.get(rowElement) === next) {
      saveQueueByRow.delete(rowElement)
    }
  })
}

const getRowValues = (
  row: JQueryElement,
  fields: RepeaterConfig['fields'],
): Record<string, string> => {
  const values: Record<string, string> = {}
  fields.forEach((field) => {
    const value = row.find(`[name="${field.name}"]`).first().val()
    values[field.name] = String(value ?? '')
  })
  return values
}

const bindUpdateHandlers = (
  row: JQueryElement,
  config: RepeaterConfig,
  parentId: string,
): void => {
  const idAttr = row.attr('data-record-id')
  const recordId = idAttr ? Number(idAttr) : undefined
  if (!recordId) {
    return
  }

  row.find('input,textarea,select').on('change', () => {
    const values = getRowValues(row, config.fields)
    queueSaveForRow(row, async () => {
      try {
        await saveRightsFormdata(config.formdataType, parentId, values, recordId)
        showSavedStatus(row)
      } catch (error) {
        console.error(
          `Failed to save rights repeater row ${config.idPrefix}${parentId}/${recordId}`,
          error,
        )
        showSaveError(row)
      }
    })
  })
}

const initRepeaterContainer = async (
  container: JQueryElement,
  config: RepeaterConfig,
): Promise<void> => {
  const id = container.attr('id') ?? ''
  const parentId = extractParentId(config.idPrefix, id)
  if (!parentId || parentId === 'None') {
    return
  }

  try {
    const response = await listRightsFormdata(config.formdataType, parentId)
    const records = response.results ?? []
    const rows = renderRepeatingData(container, config, records)
    rows.forEach(row => bindUpdateHandlers(row, config, parentId))
    toggleManualRow(container, records.length > 0)
    clearLoadAlert(container)
  } catch (error) {
    console.error(`Failed to initialize rights repeater for ${config.idPrefix}${parentId}`, error)
    showLoadAlert(container, LOAD_FAILURE_MESSAGE)
    toggleManualRow(container, false)
  }
}

const initRepeaters = async (configs: RepeaterConfig[]): Promise<void> => {
  const tasks: Promise<void>[] = []

  configs.forEach((config) => {
    $(`[id^="${config.idPrefix}"]`).each((_: number, element: Element) => {
      tasks.push(initRepeaterContainer($(element as HTMLElement), config))
    })
  })

  await Promise.all(tasks)
}

export type { RepeaterFieldType, RepeaterOptionConfig, RepeaterFieldConfig, RepeaterConfig }
export { initRepeaters }

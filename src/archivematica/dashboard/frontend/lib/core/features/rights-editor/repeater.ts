import type { RightsEditorFormdataType, RightsFormdataRecord } from '@/shared/http'
import { listRightsFormdata, saveRightsFormdata } from '@/shared/http'
import { translate } from '@/shared/i18n/plain'

type RepeaterFieldType = 'input' | 'textarea' | 'select'
type RepeaterControlElement = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement

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

const getDirectChildrenByClass = (
  element: HTMLElement,
  className: string,
): HTMLElement[] =>
  Array.from(element.children).filter(
    (child): child is HTMLElement =>
      child instanceof HTMLElement && child.classList.contains(className),
  )

const getFieldControls = (row: HTMLElement): RepeaterControlElement[] =>
  Array.from(row.querySelectorAll<RepeaterControlElement>('input,textarea,select'))

const createFieldInput = (field: RepeaterFieldConfig): RepeaterControlElement => {
  const type = field.type ?? 'textarea'
  if (type === 'input') {
    return document.createElement('input')
  }

  if (type === 'select') {
    const select = document.createElement('select')
    ;(field.options ?? []).forEach((option: RepeaterOptionConfig) => {
      const label = option.labelKey ? translate(option.labelKey) : (option.label ?? '')
      const optionElement = document.createElement('option')
      optionElement.value = option.value
      optionElement.textContent = label
      select.append(optionElement)
    })
    return select
  }

  return document.createElement('textarea')
}

const createRecordRow = (
  config: RepeaterConfig,
  record: RightsFormdataRecord,
): HTMLElement => {
  const row = document.createElement('div')
  row.className = 'repeating-ajax-data-row'
  row.dataset.recordId = String(record.id)

  config.fields.forEach((field) => {
    const label = field.labelKey ? translate(field.labelKey) : field.label
    if (label) {
      const labelElement = document.createElement('label')
      labelElement.textContent = label
      row.append(labelElement)
    }

    const fieldWrapper = document.createElement('div')
    fieldWrapper.className = 'repeating-ajax-data-field'
    const input = createFieldInput(field)
    input.name = field.name
    input.classList.add('form-control')
    input.value = String(record.values[field.name] ?? '')

    fieldWrapper.append(input)
    row.append(fieldWrapper)
  })

  return row
}

const renderRepeatingData = (
  container: HTMLElement,
  config: RepeaterConfig,
  records: RightsFormdataRecord[],
): HTMLElement[] => {
  container.replaceChildren()
  return records.map((record) => {
    const row = createRecordRow(config, record)
    container.append(row)
    return row
  })
}

const toggleManualRow = (container: HTMLElement, hasData: boolean): void => {
  const fieldset = container.closest<HTMLElement>('.repeating-ajax-data-fieldset')
  if (!fieldset) {
    return
  }

  getDirectChildrenByClass(fieldset, 'repeating-ajax-data-row').forEach((row) => {
    if (hasData) {
      row.style.display = 'none'
      return
    }

    row.style.removeProperty('display')
  })
}

const showLoadAlert = (container: HTMLElement, message: string): void => {
  const fieldset = container.closest<HTMLElement>('.repeating-ajax-data-fieldset')
  if (!fieldset) {
    return
  }

  let alert = getDirectChildrenByClass(fieldset, 'repeating-ajax-data-alert')[0]
  if (!alert) {
    alert = document.createElement('div')
    alert.className = 'repeating-ajax-data-alert alert alert-warning'
    fieldset.prepend(alert)
  }
  alert.textContent = message
}

const clearLoadAlert = (container: HTMLElement): void => {
  const fieldset = container.closest<HTMLElement>('.repeating-ajax-data-fieldset')
  if (!fieldset) {
    return
  }

  getDirectChildrenByClass(fieldset, 'repeating-ajax-data-alert').forEach((alert) => {
    alert.remove()
  })
}

const getStatusElement = (row: HTMLElement): HTMLElement => {
  const existingStatus = row.querySelector<HTMLElement>(`:scope > ${ROW_STATUS_SELECTOR}`)
  if (existingStatus) {
    return existingStatus
  }

  const status = document.createElement('small')
  status.className = 'repeating-ajax-data-status text-muted'
  status.setAttribute('aria-live', 'polite')
  status.style.display = 'none'
  row.append(status)
  return status
}

const clearStatusTimer = (status: HTMLElement): void => {
  const timerId = Number(status.dataset.hideTimer ?? '0')
  if (timerId) {
    window.clearTimeout(timerId)
    delete status.dataset.hideTimer
  }
}

const showSavedStatus = (row: HTMLElement): void => {
  const status = getStatusElement(row)
  clearStatusTimer(status)
  status.classList.remove('text-danger')
  status.classList.add('text-muted')
  status.textContent = SAVE_SUCCESS_MESSAGE
  status.style.removeProperty('display')

  const timerId = window.setTimeout(() => {
    status.style.display = 'none'
    delete status.dataset.hideTimer
  }, STATUS_HIDE_DELAY_MS)

  status.dataset.hideTimer = String(timerId)
}

const showSaveError = (row: HTMLElement): void => {
  const status = getStatusElement(row)
  clearStatusTimer(status)
  status.classList.remove('text-muted')
  status.classList.add('text-danger')
  status.textContent = SAVE_FAILURE_MESSAGE
  status.style.removeProperty('display')
}

const queueSaveForRow = (rowElement: HTMLElement, task: () => Promise<void>): void => {
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
  row: HTMLElement,
  fields: RepeaterConfig['fields'],
): Record<string, string> => {
  const values: Record<string, string> = {}
  const controls = getFieldControls(row)
  fields.forEach((field) => {
    const control = controls.find(candidate => candidate.name === field.name)
    values[field.name] = control?.value ?? ''
  })
  return values
}

const bindUpdateHandlers = (
  row: HTMLElement,
  config: RepeaterConfig,
  parentId: string,
): void => {
  const recordId = Number(row.dataset.recordId ?? '')
  if (!recordId) {
    return
  }

  getFieldControls(row).forEach((control) => {
    control.addEventListener('change', () => {
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
  })
}

const initRepeaterContainer = async (
  container: HTMLElement,
  config: RepeaterConfig,
): Promise<void> => {
  const id = container.id
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
    document.querySelectorAll<HTMLElement>(`[id^="${config.idPrefix}"]`).forEach((element) => {
      tasks.push(initRepeaterContainer(element, config))
    })
  })

  await Promise.all(tasks)
}

export type { RepeaterFieldType, RepeaterOptionConfig, RepeaterFieldConfig, RepeaterConfig }
export { initRepeaters }

import { formatDateTime } from '@/shared/date'

const TIMESTAMP_SELECTOR = '.timestamp'
const DATETIME_SELECTOR = '.datetime'

const localizeUnixTimestamp = (value: string): string => {
  const timestamp = Number(value)
  if (!Number.isFinite(timestamp)) {
    return ''
  }
  return formatDateTime(timestamp)
}

const localizeIsoDateTime = (value: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString()
}

const localizeElements = (
  elements: NodeListOf<HTMLElement>,
  localize: (value: string) => string,
): void => {
  elements.forEach((element) => {
    element.textContent = localize(element.textContent ?? '')
  })
}

export const localizeTimestampElements = (root: ParentNode = document): void => {
  localizeElements(root.querySelectorAll<HTMLElement>(TIMESTAMP_SELECTOR), localizeUnixTimestamp)
  localizeElements(root.querySelectorAll<HTMLElement>(DATETIME_SELECTOR), localizeIsoDateTime)
}

export const init = (): void => {
  // Contract: this feature is initialized once by the core feature loader.
  localizeTimestampElements()
}

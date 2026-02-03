import { formatDate } from '@vueuse/shared'

export const ARCHIVEMATICA_DATE_TIME_FORMAT = 'YYYY-MM-DD HH:mm'

export const formatDateTime = (timestamp: number): string => {
  return formatDate(
    new Date(timestamp * 1000),
    ARCHIVEMATICA_DATE_TIME_FORMAT,
  )
}

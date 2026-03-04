import { formatDate } from '@vueuse/shared'

const ARCHIVEMATICA_DATE_TIME_FORMAT = 'YYYY-MM-DD HH:mm'

// TODO: Consider Intl.DateTimeFormat for locale-aware rendering when we decide
// to prioritize localized display over fixed-format backward compatibility.
export const formatDateTime = (timestamp: number): string => {
  return formatDate(
    new Date(timestamp * 1000),
    ARCHIVEMATICA_DATE_TIME_FORMAT,
  )
}

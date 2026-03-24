import { createUrl } from './client'

export const getJobTasksUrl = (jobUuid: string): string => {
  return createUrl(`/tasks/${jobUuid}/`)
}

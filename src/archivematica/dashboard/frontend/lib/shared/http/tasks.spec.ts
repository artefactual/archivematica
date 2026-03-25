import { describe, it, expect } from 'vitest'
import { getJobTasksUrl } from '@/shared/http/tasks'

describe('tasks routes', () => {
  it('builds job tasks URL', () => {
    expect(getJobTasksUrl('job-1')).toContain('/tasks/job-1/')
  })
})

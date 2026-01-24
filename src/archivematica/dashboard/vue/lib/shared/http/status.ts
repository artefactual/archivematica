import { createHttpClient } from '@/shared/http/client'

export type StatusResponse = {
  sip: number
  transfer: number
  dip: number
}

const client = createHttpClient()

export const getStatus = async (): Promise<StatusResponse> => {
  return client.getJson<StatusResponse>('/status/', { cacheBust: true, strictJson: true })
}

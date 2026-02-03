import { createHttpClient } from './client'

export type ExecuteChoicePayload = {
  uuid: string
  choice: string
}

const client = createHttpClient()

export const executeChoice = async (payload: ExecuteChoicePayload): Promise<string> => {
  const body = new URLSearchParams()
  body.set('uuid', payload.uuid)
  body.set('choice', payload.choice)

  return client.requestText('/mcp/execute/', {
    method: 'POST',
    body: body.toString(),
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    },
  })
}

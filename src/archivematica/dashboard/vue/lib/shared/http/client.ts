type QueryValue = string | number | boolean | null | undefined

export type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  query?: Record<string, QueryValue>
  headers?: HeadersInit
  body?: BodyInit | null
  json?: unknown
  strictJson?: boolean
  credentials?: RequestCredentials
  cacheBust?: boolean
  signal?: AbortSignal

  // Artificial delay for testing purposes (in milliseconds).
  delay?: number
}

export type HttpClientOptions = {
  baseUrl?: string
  defaultHeaders?: HeadersInit
  credentials?: RequestCredentials
}

export class HttpError extends Error {
  status: number
  statusText: string
  url: string
  bodyText?: string
  bodyJson?: unknown

  constructor(message: string, response: Response, bodyText?: string, bodyJson?: unknown) {
    super(message)
    this.name = 'HttpError'
    this.status = response.status
    this.statusText = response.statusText
    this.url = response.url
    this.bodyText = bodyText
    this.bodyJson = bodyJson
  }
}

export type HttpErrorInfo = {
  status: number
  statusText: string
  url: string
  bodyText: string | null
  bodyJson: unknown | null
}

export const toHttpErrorInfo = (err: unknown): HttpErrorInfo | null => {
  if (!(err instanceof HttpError)) return null
  return {
    status: err.status,
    statusText: err.statusText,
    url: err.url,
    bodyText: err.bodyText ?? null,
    bodyJson: err.bodyJson ?? null,
  }
}

const safeParseJson = (text: string): unknown | null => {
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

const buildUrl = (
  baseUrl: string,
  path: string,
  query?: RequestOptions['query'],
  cacheBust?: boolean,
): string => {
  const url = new URL(path, baseUrl)

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined) continue
      url.searchParams.set(key, String(value))
    }
  }

  if (cacheBust) {
    url.searchParams.set('_', String(Date.now()))
  }

  return url.toString()
}

export const createUrl = (
  path: string,
  options: Pick<RequestOptions, 'query' | 'cacheBust'> = {},
  baseUrl = window.location.origin,
): string => {
  return buildUrl(baseUrl, path, options.query, options.cacheBust)
}

export const openDownload = (
  path: string,
  options: Pick<RequestOptions, 'query'> = {},
  baseUrl = window.location.origin,
): void => {
  const url = buildUrl(baseUrl, path, options.query, false)
  window.open(url, '_blank', 'noopener')
}

const getCookie = (name: string): string => {
  const prefix = `${name}=`
  return document.cookie
    .split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(prefix))
    ?.slice(prefix.length) ?? ''
}

const getCsrfToken = (): string => {
  return getCookie('csrftoken')
}

const needsCsrf = (method?: string) =>
  !method || !['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())

const buildRequestInit = (
  options: RequestOptions,
  defaults: Required<Pick<HttpClientOptions, 'defaultHeaders' | 'credentials'>>,
): RequestInit => {
  const headers = new Headers(defaults.defaultHeaders)
  if (options.headers) {
    new Headers(options.headers).forEach((value, key) => headers.set(key, value))
  }
  if (!headers.has('X-Requested-With')) {
    headers.set('X-Requested-With', 'XMLHttpRequest')
  }

  let body = options.body ?? null
  if (options.json !== undefined) {
    if (body !== null) {
      throw new Error('Provide either json or body, not both.')
    }
    body = JSON.stringify(options.json)
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  if (needsCsrf(options.method ?? 'GET')) {
    const token = getCsrfToken()
    if (token && !headers.has('X-CSRFToken')) {
      headers.set('X-CSRFToken', token)
    }
  }

  return {
    method: options.method ?? 'GET',
    headers,
    body,
    credentials: options.credentials ?? defaults.credentials,
    signal: options.signal,
  }
}

export const delay = (ms: number, signal?: AbortSignal): Promise<void> =>
  new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }
    const timeout = setTimeout(resolve, ms)
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(timeout)
        reject(new DOMException('Aborted', 'AbortError'))
      },
      { once: true },
    )
  })

export const createHttpClient = (options: HttpClientOptions = {}) => {
  const baseUrl = options.baseUrl ?? window.location.origin
  const defaultHeaders = options.defaultHeaders ?? {}
  const credentials = options.credentials ?? 'same-origin'

  const requestJson = async <T>(path: string, requestOptions: RequestOptions = {}): Promise<T> => {
    if (requestOptions.delay) {
      await delay(requestOptions.delay, requestOptions.signal)
    }
    const url = buildUrl(baseUrl, path, requestOptions.query, requestOptions.cacheBust)
    const response = await fetch(
      url,
      buildRequestInit(requestOptions, { defaultHeaders, credentials }),
    )

    if (!response.ok) {
      const bodyText = await response.text()
      const bodyJson = safeParseJson(bodyText)
      throw new HttpError(
        `Request failed: ${response.status}`,
        response,
        bodyText,
        bodyJson ?? undefined,
      )
    }

    const text = await response.text()
    const parsed = safeParseJson(text)
    if (requestOptions.strictJson && parsed === null) {
      throw new Error(`Expected JSON response from ${response.url || url}.`)
    }
    return (parsed ?? null) as T
  }

  const getJson = async <T>(path: string, requestOptions: RequestOptions = {}): Promise<T> => {
    return requestJson<T>(path, { ...requestOptions, method: 'GET' })
  }

  return {
    requestJson,
    getJson,
  }
}

const unsafeCharRegex = /[^A-Za-z0-9_-]/g

const normalizePath = (raw: string): string => {
  if (!raw) {
    return 'empty'
  }

  let decoded = raw

  try {
    decoded = decodeURIComponent(raw)
  } catch {
    decoded = raw
  }

  return decoded
    .replace(/\\/g, '/')
    .replace(/\/+/g, '/')
}

const fallbackHash = (input: string): string => {
  const normalized = normalizePath(input)
  let hash = 0

  for (let i = 0; i < normalized.length; i++) {
    hash = (hash << 5) - hash + normalized.charCodeAt(i)
    hash |= 0
  }

  return Math.abs(hash).toString(16)
}

export const createTreeNodeId = (path: string): string => {
  const normalized = normalizePath(path)
  const sanitized = normalized
    .replace(unsafeCharRegex, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')

  if (sanitized.length > 0) {
    return `node-${sanitized}`
  }

  return `node-${fallbackHash(path)}`
}

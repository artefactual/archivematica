import { i18n } from './index'

type Params = Record<string, string | number>

// Lightweight placeholder interpolation for fallback messages.
// Replaces `{param}` tokens with provided values.
const interpolate = (message: string, params?: Params): string => {
  if (!params) {
    return message
  }
  return Object.entries(params).reduce((value, [key, param]) => {
    return value.split(`{${key}}`).join(String(param))
  }, message)
}

// Translation helper for plain TypeScript modules (outside Vue templates/components).
//
// - Returns localized text when the key exists in loaded i18n messages.
// - Falls back to a simple interpolated string when the key is missing.
export const translate = (key: string, params?: Params): string => {
  if (i18n.global.te(key)) {
    const translated = i18n.global.t(key, params ?? {}) as string
    return translated
  }

  return interpolate(key, params)
}

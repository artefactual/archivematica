// Thin wrapper around base64-helpers that provides a branded Base64String type
// for safer handling of encoded values in the UI codebase.
import * as Base64 from 'base64-helpers'

export type Base64String = string & { readonly __brand: unique symbol }

export const encodeBase64 = (value: string): Base64String => {
  return Base64.encode(value) as Base64String
}

export const decodeBase64 = (value: Base64String): string => {
  return Base64.decode(value)
}

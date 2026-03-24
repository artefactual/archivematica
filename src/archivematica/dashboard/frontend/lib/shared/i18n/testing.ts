import { createI18n } from 'vue-i18n'
import en from './locales/en.json'

export function createI18nMock() {
  return createI18n({
    legacy: false,
    locale: 'en',
    fallbackLocale: 'en',
    messages: { en: en },
    silentTranslationWarn: true,
    silentFallbackWarn: true,
  })
}

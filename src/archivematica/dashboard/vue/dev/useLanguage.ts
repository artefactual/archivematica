import { ref, computed } from 'vue'
import {
  AVAILABLE_LOCALES,
  setLocale,
  initialLocale,
  type AvailableLocale,
} from '@/shared/i18n'

const currentLanguage = ref(initialLocale)

const SUPPORTED_LANGUAGES = AVAILABLE_LOCALES.map(code => ({
  code,
  name: (() => {
    const name = new Intl.DisplayNames([code], { type: 'language' }).of(code) ?? code
    return name.charAt(0).toUpperCase() + name.slice(1)
  })(),
}))

export function useLanguage() {
  const currentLanguageName = computed(() => {
    const lang = SUPPORTED_LANGUAGES.find(l => l.code === currentLanguage.value)
    return lang?.name || 'Language'
  })

  const availableLanguages = computed(() => SUPPORTED_LANGUAGES)

  const selectLanguage = (langCode: AvailableLocale) => {
    currentLanguage.value = langCode
    setLocale(langCode)
  }

  return {
    currentLanguage,
    currentLanguageName,
    availableLanguages,
    selectLanguage,
  }
}

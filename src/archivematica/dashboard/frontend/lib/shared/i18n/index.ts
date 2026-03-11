import { createI18n } from 'vue-i18n'

// Available locales for async loading. This mirrors the authoritative LANGUAGES
// list in archivematica/dashboard/settings/base.py.
const AVAILABLE_LOCALES = ['en', 'es', 'fr', 'ja', 'no', 'pt', 'pt-br', 'sv'] as const
type AvailableLocale = typeof AVAILABLE_LOCALES[number]

// Default locale for the application.
const DEFAULT_LOCALE: AvailableLocale = 'en'

// Simple function to set locale with async loading.
async function setLocale(locale: AvailableLocale): Promise<void> {
  if (!AVAILABLE_LOCALES.includes(locale)) {
    locale = DEFAULT_LOCALE
  }

  // Load the locale messages dynamically.
  let messages: Record<string, unknown>
  try {
    messages = (await import(`./locales/${locale}.json`)).default

    // Set the messages in the i18n instance.
    i18n.global.setLocaleMessage(locale, messages)

    // Change the active locale.
    i18n.global.locale.value = locale
  } catch {
    // Fall back to default locale if loading fails.
    i18n.global.locale.value = DEFAULT_LOCALE
  }
}

// Convert POSIX/CLDR format (pt_BR) to BCP 47 format (pt-br).
function posixToBcp47Locale(posixLocale: string): string {
  return posixLocale.replace('_', '-').toLowerCase()
}

// Initialize i18n.
const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  silentTranslationWarn: true,
  silentFallbackWarn: true,
})

function getInitialLocale(): AvailableLocale {
  const language = document.body?.dataset.currentLanguage
    || document.documentElement.dataset.currentLanguage
  if (!language) {
    return DEFAULT_LOCALE
  }

  const candidate = posixToBcp47Locale(language)
  if ((AVAILABLE_LOCALES as readonly string[]).includes(candidate)) {
    return candidate as AvailableLocale
  }

  return DEFAULT_LOCALE
}

// Initialize the i18n instance from a DOM data attribute.
// Expected format is POSIX/CLDR (e.g., "pt_BR") converted to BCP 47.
const initialLocale: AvailableLocale = getInitialLocale()

async function initI18n(): Promise<void> {
  try {
    await setLocale(initialLocale)
  } catch (error) {
    console.warn('Failed to set initial locale:', error)
  }
}

export {
  i18n,
  initI18n,
}

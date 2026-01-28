# Archivematica Vue Components

Vue.js components for Archivematica Dashboard, migrating from Angular 1.x to
modern Vue 3 + TypeScript.

## Development

### Setup

```bash
npm install
```

### Development server

```bash
npm run dev
# Starts on http://localhost:3000 (or custom port with --port)
```

### Testing

```bash
npm run test              # Run unit tests
npm run test:interactive  # Run unit tests in watch mode
npm run lint              # Run ESLint with auto-fix
npm run type-check        # Run TypeScript checks
npm run check             # Run all checks (lint + type-check + test + build)
```

### Build

```bash
npm run build             # Production build
npm run build:watch       # Production build (watch mode)
npm run preview           # Preview production build locally
```

## Internationalization (i18n)

Vue i18n is configured in `lib/shared/i18n` and loads JSON translation bundles
at runtime. The Vue package does not include gettext conversion scripts; the
JSON files under `lib/shared/i18n/locales` are the runtime source of truth.

### Translation files structure

The locale JSON files are located in `lib/shared/i18n/locales`:

```text
lib/shared/i18n/locales/
├── en.json
├── es.json
└── ...
```

`en.json` is the source language file and must contain all translation keys used
in the Vue components. Other language files should mirror the structure of
`en.json`.

### Adding translations

Use `$t()` in templates and `t()` in script sections:

```vue
<template>
  <h1>{{ $t('transfer.name') }}</h1>
  <button @click="startTransfer">{{ $t('transfer.startTransfer') }}</button>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

function showMessage() {
  alert(t('alerts.transferStarted', { name: 'Example' }))
}
</script>
```

#### Translation key naming convention

Follow the existing nested structure:

- `alerts.*` - Alert and notification messages
- `transfer.*` - Transfer-related UI elements
- `transferTypes.*` - Transfer type options
- `fileBrowser.*` - File browser interface elements

#### Message interpolation

Use Vue i18n interpolation syntax:

```javascript
// Component
t('alerts.transferStarted', { name: transferName })

// Translation file
"Transfer \"{name}\" started successfully"
```

### Development environment

- **Language selector**: Available in `npm run dev` via the navbar dropdown
- **Runtime loading**: Locale JSON is lazy-loaded by `setLocale`

### Adding a new language

1. Add a new JSON file in `lib/shared/i18n/locales` (BCP 47 filename, e.g.
   `pt-br.json`).
2. Add the locale code to `AVAILABLE_LOCALES` in `lib/shared/i18n/index.ts`.
3. Ensure the backend sets `window.DashboardConfig.currentLanguage` to the
   POSIX/CLDR form (e.g. `pt_BR`) when needed.

### Language selection at runtime

- The initial locale comes from `window.DashboardConfig.currentLanguage` when
  present, and falls back to English.
- The runtime expects POSIX/CLDR style values like `pt_BR` and converts them to
  BCP 47 (`pt-br`) internally.

### Troubleshooting

**Missing translations:**

- Check the JSON files in `lib/shared/i18n/locales` for the missing key
- Verify translation keys match between Vue components and JSON files
- Ensure the locale code exists in `AVAILABLE_LOCALES` and on disk

**Build issues:**

- Ensure Vue components use correct `t()` or `$t()` syntax
- Validate JSON file format (no syntax errors)
- Confirm locale codes match between JSON files and Vue i18n config

# Archivematica Vue Components

Vue.js components for Archivematica Dashboard, migrating from Angular 1.x to
modern Vue 3 + TypeScript.

## Components

- **Transfer Browser** (`/browser`) - File system browser for transfer content
  selection

## Development

### Setup

```bash
npm install
```

### Development Server

```bash
npm run dev
# Starts on http://localhost:3000 (or custom port with --port)
```

### Testing & Quality

```bash
npm run test          # Run unit tests
npm run lint          # Run ESLint with auto-fix
npm run type-check    # Run TypeScript checks
npm run format        # Run Prettier formatter
npm run check         # Run all checks (lint + type-check + test + build)
```

### Build

```bash
npm run build         # Production build
npm run preview       # Preview production build locally
```

## Internationalization (i18n)

The application uses a **gettext-compatible workflow** with Vue i18n for runtime
translation management. This hybrid approach maintains compatibility with
existing Weblate translation infrastructure while using modern Vue i18n for
development.

### Supported Languages

- English (en) - Base language
- Spanish (es)
- French (fr)
- Japanese (ja)
- Portuguese (pt)
- Portuguese Brazil (pt_BR)
- Swedish (sv)

### Translation Workflow

The workflow uses custom scripts in `scripts/i18n/` to bridge gettext (.po
files) and vue-i18n (JSON files):

#### For Developers

1. **Extract translation keys** from Vue components:

   ```bash
   npm run i18n:extract-pot    # Creates messages.pot template
   ```

2. **Convert existing translations** to .po format:

   ```bash
   npm run i18n:json-to-po     # JSON → .po files
   ```

3. **Generate runtime files** for Vue i18n:

   ```bash
   npm run i18n:po-to-json     # .po files → JSON
   ```

#### Quick Commands

```bash
npm run i18n:build          # Extract + convert to JSON (standard workflow)
npm run i18n:setup          # Extract + convert to .po (for new translations)
npm run i18n:full           # Complete cycle: extract + po + json
```

### Translation Files Structure

```text
scripts/i18n/
├── messages.pot             # Generated template (all translatable strings)
├── locales/                 # Source .po files for translators
│   ├── en.po               # English (source language)
│   ├── es.po               # Spanish
│   └── ...                 # Other languages
└── [scripts]               # Conversion utilities

lib/browser/i18n/locales/   # Runtime JSON files for Vue i18n
├── en.json
├── es.json
└── ...
```

### Adding Translations

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

#### Translation Key Naming Convention

Follow the existing nested structure:

- `alerts.*` - Alert and notification messages
- `transfer.*` - Transfer-related UI elements
- `transferTypes.*` - Transfer type options
- `fileBrowser.*` - File browser interface elements

#### Message Interpolation

Use Vue i18n interpolation syntax:

```javascript
// Component
t('alerts.transferStarted', { name: transferName })

// Translation file
"Transfer \"{name}\" started successfully"
```

### Development Environment

- **Language selector**: Available in navbar during development
- **Language persistence**: Selected language saved in localStorage
- **Hot reload**: Translation changes reflected immediately during development

### Translator Workflow

1. **Work with .po files** in `scripts/i18n/locales/`
2. **Use standard tools**: Poedit, Weblate, or any gettext-compatible editor
3. **Reference source**: English translations in `en.po`
4. **Generate runtime**: Run `npm run i18n:po-to-json` after updates

### CI/CD Integration

Maintains compatibility with existing translation infrastructure:

1. **Extract**: `npm run i18n:extract-pot` → generates `messages.pot`
2. **Translate**: Existing Weblate integration processes .po files
3. **Build**: `npm run i18n:po-to-json` → generates runtime JSON
4. **Deploy**: JSON files included in application build

Benefits:

- `.po` files work with Weblate translation platform
- Standard gettext tools remain functional
- CI pipelines can validate and process `.po` files as before
- No changes required to existing translation management

### Migration from Angular

Translations were migrated from the Angular 1.x app. The migration script maps
Angular's flat keys to Vue's nested structure while preserving all existing
translations.

### Available Scripts Reference

| Script | Purpose | Input | Output |
| ------ | ------- | ----- | ------ |
| `i18n:extract-pot` | Extract translatable strings | Vue components | `messages.pot` |
| `i18n:json-to-po` | Convert JSON to .po | JSON files | .po files with translations |
| `i18n:po-to-json` | Convert .po to JSON | .po files | JSON files for vue-i18n |
| `i18n:build` | Extract + convert to JSON | Vue components | Runtime JSON files |
| `i18n:setup` | Extract + populate .po files | Vue components + JSON | .po files with translations |
| `i18n:full` | Complete workflow | Vue components + JSON | All outputs |

### Troubleshooting

**Missing translations:**

- Check `.po` files have non-empty `msgstr` values
- Verify translation keys match between Vue components and .po files
- Run `npm run i18n:po-to-json` to regenerate runtime files

**Build issues:**

- Ensure Vue components use correct `t()` or `$t()` syntax
- Validate .po file format (no syntax errors)
- Confirm language codes match between .po files and Vue i18n config

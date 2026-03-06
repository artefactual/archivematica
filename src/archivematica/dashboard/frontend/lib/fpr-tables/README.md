# FPR Tables (Vue)

`fpr-tables` is the Vue/TanStack replacement for the old FPR jQuery
DataTables setup.

This is a **first iteration**:

- keep Django routes/views mostly unchanged
- stop rendering large HTML tables in Django templates
- render JSON payloads (`json_script`) instead
- let Vue render the table UI (sorting/filtering/pagination/actions)

## What It Does

- Vue 3 + TanStack Table
- Bootstrap-compatible table/pager/button markup
- client-side sorting, filtering, and pagination
- shared renderer for many FPR table pages (`kind`-based)

## How It Loads

1. Django template renders:
   - a mount node (`data-fpr-table-root`)
   - a `json_script` payload
2. `fpr/templates/fpr/app_layout.html` loads `frontend/fpr-tables.js`
3. `index.ts` initializes Vue i18n and mounts `App.vue` for each table root

## Files

- `index.ts`: bootstrap + mount logic
- `App.vue`: shared FPR table renderer
- `TablePagination.vue`: pager + page-size selector
- `payloads.py` (Django): builds the JSON payloads consumed by Vue

## Payload Shape (High Level)

Expected fields:

- `version`
- `kind`
- `columns`
- `rows`
- `ui`

Notes:

- `rows` should be plain JSON values (no HTML strings)
- send identifiers/slugs and action metadata keys (`view`/`edit`/...)
  not rendered DOM
- send enum/code values for choice fields
  (`type`, `usage`, `purpose`, `configuration`)
  and let Vue translate them
- `kind` selects the table layout/columns in `App.vue`
- generic table chrome is client-owned: payload `columns` can omit `label`
  and pagination labels/templates come from Vue i18n

## i18n (Vue Side)

- Uses `lib/shared/i18n`
- Namespaces:
  - `fpr` for FPR table strings (column labels, booleans, search,
    empty/create text, action labels)
  - `misc.pagination` for shared pagination labels
- Backend payload should only include data and UI control metadata (for example:
  action keys/styles and create button style + route params)
- For FPR choice values, use `fpr.values.*` keys in Vue i18n;
  avoid `get_*_display()`
  in payload builders

## Testing

Basic component tests live next to the components:

- `App.spec.ts`
- `TablePagination.spec.ts`

Use `createI18nMock()` from `@/shared/i18n/testing` and standard Vue Test Utils
`mount(...)`.

## Extending / Adding a New FPR Table

1. Add/extend a serializer in `src/archivematica/dashboard/fpr/payloads.py`
2. Render mount node + `json_script` payload in the Django template
3. Add/update the `COLUMN_DEFINITIONS_BY_KIND` map in `App.vue`
   if the table shape is new
4. Prefer plain fields + route params + action metadata over HTML-in-JSON

## Current Limits (Intentional)

- Pagination/filtering/sorting are client-side
- Django still sends full datasets
- No server-side pagination/filtering API yet

That is deliberate for this migration step. The main goal is replacing the
frontend rendering layer safely before changing server behavior.

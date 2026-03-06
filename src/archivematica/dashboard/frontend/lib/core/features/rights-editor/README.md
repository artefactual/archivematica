# Rights Editor Feature Architecture

This document explains how the `rights-editor` feature is structured and how it
maps to the two Django templates:

- `rights_edit.html` (main rights statement editor)
- `rights_grants_edit.html` (rights granted editor)

## How It Loads

1. Django templates set:
   - `data-features="rights-editor"`
   - `body id` as either:
     - `page-rights-editor-main`
     - `page-rights-editor-grants`
2. `core/index.ts` lazy-loads `features/rights-editor/index.ts`.
3. `rights-editor/index.ts`:
   - initializes i18n (`initI18n`)
   - dispatches to the page-specific initializer.

## Entry Points

- `index.ts`
  - feature bootstrap and page dispatch.
- `main-page.ts`
  - main page initializer (date mask + basis behavior + main repeaters).
- `grants-page.ts`
  - grants page initializer (date mask + grants layout behavior + grants
    repeaters).

## Shared Building Blocks

- `core/features/datemask`
  - shared date mask module used by rights-editor date fields.
- `repeater.ts`
  - shared repeater runtime for both pages:
    - finds repeater containers by id prefix
    - fetches records from `/formdata/...`
    - renders rows
    - posts updates on change
    - hides manual “new row” when data exists.
- `main-page.ts` also contains:
  - basis switching/relabel behavior (`Copyright`, `Statute`, `License`,
    `Policy`, `Donor`, `Other`).
- `grants-page.ts` also contains:
  - grants-page layout behavior:
    - reveal-button for last grant fieldset
    - spacing for subsequent grant fieldsets
    - restriction block repositioning.

## HTTP Layer

`repeater.ts` uses shared HTTP helpers from:

- `shared/http/rights.ts`

Supported operations:

- `GET /formdata/{type}/{parentId}/`
- `POST /formdata/{type}/{parentId}/`
- `DELETE /formdata/{type}/{parentId}/{id}/` (available in HTTP layer; not
   currently exposed in UI).

## Server Interaction Model (Technical Debt)

The rights editor is a hybrid Django + frontend orchestration flow:

- The main Django form POST (`Save` / `Next`) persists the rights statement and
  its basis-specific parent formset records.
- Repeating child records (documentation identifiers, notes, grants
  restrictions/notes) are loaded and updated by frontend code against
  `/formdata/...` endpoints, keyed by the parent record ID.
- Child repeaters with `parentId=None` are intentionally inert until the parent
  is saved and receives a real primary key.

Why this is technical debt:

- Relationship orchestration is split between full Django form posts and
  frontend `/formdata/...` calls.
- Child-record lifecycle is coupled to DOM IDs and parent PK availability
  (`None` vs persisted IDs).
- This coupling makes behavior harder to reason about and increases
  integration-test burden.

Why this still exists in this iteration:

- This first iteration is intentionally a strict 1:1 behavioral reproduction of
  legacy `rights_edit.js` / `repeating-ajax-data.js`.
- It is not a workflow redesign or data-model redesign; parity and migration
  safety are the primary goals.

## i18n Strategy

- UI text is sourced from `shared/i18n` via:
  - `shared/i18n/plain.ts` (`translate(...)`) for plain TypeScript code.
- Page init calls `initI18n()` before any UI behavior runs.
- Repeater configs use translation keys (e.g. `rights.type`, `rights.allow`)
  instead of hardcoded strings.

## Current Repeater Coverage

Currently wired repeater flows:

- Main page:
  - `copyrightdocidfields_*` -> `copyrightdocumentationidentifier`
  - `copyrightnotes_*` -> `copyrightnote`
  - `statutedocidfields_*` -> `statutedocumentationidentifier`
  - `statutenotes_*` -> `statutenote`
  - `licensedocidfields_*` -> `licensedocumentationidentifier`
  - `licensenotes_*` -> `licensenote`
  - `otherrightsdocidfields_*` -> `otherrightsdocumentationidentifier`
  - `otherrightsnotes_*` -> `otherrightsnote`
- Grants page:
  - `rightsrestrictions_*` -> `rightsrestriction`
  - `rightsfields_*` -> `rightsnote`

## Tests

Feature tests live next to modules:

- `repeater.spec.ts`
- `main-page.spec.ts`
- `grants-page.spec.ts`

They validate page dispatch behavior, repeater render/update behavior, and
page-specific DOM behavior.

Date mask behavior is covered in `core/features/datemask/index.spec.ts`.

## TODO

- Improve legacy-derived DOM coupling in grants layout behavior
  (`repositionRestrictionField`) so it no longer depends on child index order.
- Move new repeater status/error strings (`Saved`, load/save failures) into
  localized i18n keys once product wording is finalized.
- Evaluate a follow-up iteration that removes jQuery. Date masking no longer
  uses `inputmask` and now lives in shared `core/features/datemask`.
- Evaluate replacing native `title` attributes with an accessible design-system
  tooltip once strict migration parity is no longer required.

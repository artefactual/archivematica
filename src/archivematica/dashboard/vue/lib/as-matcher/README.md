# ArchivesSpace Matcher (`as-matcher`)

Vue replacement for the legacy Backbone/jQuery ArchivesSpace DIP object matcher
that powers the assign/pair page (`ingest/as/match.html`).

This UI is reached during the DIP upload to ArchivesSpace flow: after the user
chooses `Upload DIP to ArchivesSpace`, Archivematica sends them to the
ArchivesSpace browse pages (`/upload/as/`), where they navigate remote
collections/resources and then click `Assign DIP objects to this resource` (or
the component-level equivalent) to open the matcher page.

## Purpose

This app keeps the existing Django backend contract (`POST`/`DELETE` to the
match endpoint) while moving UI state, filtering, sorting, and pairing
interactions to Vue.

## Boundaries

- In scope: matcher page UI (`/upload/as/match/...`)
- Out of scope: collections/resource/review Django pages and ArchivesSpace
  server logic

## Bootstrap contract

The Django view builds a single `matcher_payload` dict and injects it with
`json_script` as `#as-matcher-data`. `index.ts` reads that payload and mounts the
app into `#as_matcher`.

## Structure

- `index.ts`: Bootstrap / mount
- `App.vue`: Matcher state orchestration and API calls
- `components/*`: Presentational panes/toolbar/alerts
- `types.ts`: Server bootstrap payload types
- `types.ts`: Server bootstrap payload and client-side matcher row/state types

## Why this design

- Preserve backend behavior to reduce migration risk.
- Keep pairing optimistic-ish but server-authoritative (each pair persists immediately).
- Keep Bootstrap markup compatibility while modernizing interaction logic.
- Use TanStack Table for table sorting state without replacing the HTML tables.

// Visual style variants supported by Bootstrap-compatible row action buttons.
export type TableActionStyle = 'default' | 'primary' | 'warning'
export type TableActionKey = 'view' | 'edit' | 'replace' | 'disable' | 'enable' | 'delete'

// Row action metadata sent by Django for rendering links/buttons in the actions column.
export type TableAction = {
  key: TableActionKey
  style: TableActionStyle
}

// Column metadata sent by Django. `key` maps to row fields; `label` is optional
// and only needed for per-page overrides.
export type TableColumnMeta = {
  key: string
  label?: string
  sortable?: boolean
}

// Supported FPR table variants rendered by the shared Vue table component.
export type FprTableKind
  = | 'format-list'
    | 'idcommand-list'
    | 'fpcommand-list'
    | 'idtool-list'
    | 'fptool-list'
    | 'formatgroup-list'
    | 'idrule-list'
    | 'fprule-list'
    | 'format-detail-versions'
    | 'idtool-detail-commands'
    | 'fptool-detail-commands'
    | 'formatgroup-form-formats'

// Generic row payload for FPR tables. Rows are plain JSON objects with optional action metadata.
export type FprRow = Record<string, unknown> & {
  id: string
  actions?: TableAction[]
}

// UI strings/config provided by Django for the table shell.
// Generic table chrome (column defaults, pager strings, boolean labels) is owned
// by Vue i18n to avoid duplicated translations across backend and frontend.
export type FprTableUi = {
  create: {
    style: TableActionStyle
    parentUuid?: string
    formatSlug?: string
  } | null
}

// Full Django -> Vue bootstrap payload consumed by `App.vue`.
export type FprTablePayload = {
  version: number
  kind: FprTableKind
  columns: TableColumnMeta[]
  rows: FprRow[]
  ui: FprTableUi
}

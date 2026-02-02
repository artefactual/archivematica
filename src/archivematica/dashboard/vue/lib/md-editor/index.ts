import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'

// Define the shape of the editor data expected from the server.
type EditorData = Readonly<{
  sipUUID: string
  // Mapping of source directory identifiers to their paths, e.g.:
  // "7df82cfd-c9d4-4740-a28b-a43893e6c206" => "/home".
  sourceDirectories: Readonly<Record<string, string>>
}>

// Retrieves the editor data from the #md-editor-data script tag.
const getEditorData = (): EditorData => {
  const el = document.getElementById('md-editor-data')
  if (!(el instanceof HTMLScriptElement)) {
    throw new Error('#md-editor-data not found or not a <script> tag.')
  }
  const raw = el.textContent?.trim()
  if (!raw) {
    throw new Error('#md-editor-data is empty.')
  }
  try {
    return Object.freeze(JSON.parse(raw) as EditorData)
  } catch {
    throw new Error('Invalid JSON in #md-editor-data.')
  }
}

async function bootstrap() {
  const editorData = getEditorData()
  await initI18n()
  const app = createApp(App, editorData)
  app.use(i18n)
  app.mount('#md-editor')
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap app:', err)
})

import { createApp } from 'vue'
import TransferBrowser from '@/browser/TransferBrowser.vue'
import { i18n } from '@/shared/i18n'

const app = createApp(TransferBrowser)

app.use(i18n)
app.mount('#transfer-browser')

import { createApp } from 'vue'
import App from './App.vue'
import { i18n, initI18n } from '@/shared/i18n'
import { getMonitorConfig, type MonitorUnitType } from '@/monitor/composables'

type MonitorBootstrapTarget = {
  mountEl: HTMLElement
  configScriptId: string
  unitType: MonitorUnitType
}

const resolveBootstrapTarget = (): MonitorBootstrapTarget => {
  const transferMount = document.getElementById('transfer-monitor')
  if (transferMount) {
    return {
      mountEl: transferMount,
      configScriptId: 'transfer-monitor-config',
      unitType: 'Transfer',
    }
  }

  const ingestMount = document.getElementById('ingest-monitor')
  if (ingestMount) {
    return {
      mountEl: ingestMount,
      configScriptId: 'ingest-monitor-config',
      unitType: 'SIP',
    }
  }

  throw new Error('No monitor mount element found.')
}

async function bootstrap() {
  const target = resolveBootstrapTarget()
  await initI18n()
  const config = getMonitorConfig(target.configScriptId)
  createApp(App, { unitType: target.unitType, config }).use(i18n).mount(target.mountEl)
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap app:', err)
})

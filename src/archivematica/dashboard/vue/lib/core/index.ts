export type FeatureModule = {
  init?: () => void | Promise<void>
}

const modules = import.meta.glob<FeatureModule>('./features/*/index.ts')

const FEATURE_NAME_RE = /^[a-z0-9-]+$/

const parseFeatureNames = (raw: string): string[] => {
  const names = raw
    .split(/[,\s]+/)
    .map(name => name.trim())
    .filter(Boolean)
    .filter(name => FEATURE_NAME_RE.test(name))

  return Array.from(new Set(names))
}

async function boot(): Promise<void> {
  const featureAttr = document.body.dataset.features ?? ''
  if (!featureAttr) {
    return
  }

  const featureNames = parseFeatureNames(featureAttr)
  for (const featureName of featureNames) {
    const path = `./features/${featureName}/index.ts`
    const loader = modules[path]
    if (!loader) {
      console.error(`Feature "${featureName}" is not available`)
      continue
    }

    try {
      const mod = await loader()
      await mod.init?.()
    } catch (err) {
      console.error(`Failed to load feature "${featureName}"`, err)
    }
  }
}

function onReady(): void {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => void boot(), { once: true })
    return
  }
  void boot()
}

onReady()

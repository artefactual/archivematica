import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import stylistic from '@stylistic/eslint-plugin'

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,vue}'],
  },

  globalIgnores(['**/dist/**', '**/node_modules/**']),

  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,

  {
    ...pluginVitest.configs.recommended,
    files: ['lib/**/*.spec.ts'],
  },

  stylistic.configs.customize({
    semi: false,
    quotes: 'single',
    jsx: false,
    braceStyle: '1tbs',
  }),

  {
    rules: {
      '@stylistic/multiline-comment-style': ['error', 'separate-lines', { checkJSDoc: true }],
    },
  },

)

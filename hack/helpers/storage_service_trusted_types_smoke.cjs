const assert = require('node:assert/strict')

const { chromium } = require('playwright')

const baseUrl = process.env.STORAGE_SERVICE_BASE_URL ?? 'http://127.0.0.1:62081'
const loginUrl =
  process.env.STORAGE_SERVICE_LOGIN_URL ?? `${baseUrl}/login/?next=/spaces/create/`
const username = process.env.STORAGE_SERVICE_USERNAME ?? 'test'
const password = process.env.STORAGE_SERVICE_PASSWORD ?? 'test'

const allowedConsoleErrors = ['favicon.ico']

;(async () => {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()

  const consoleErrors = []
  const pageErrors = []

  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })

  try {
    await page.goto(loginUrl, { waitUntil: 'domcontentloaded' })
    await page.getByLabel('Username:').fill(username)
    await page.getByLabel('Password:').fill(password)
    await page.getByRole('button', { name: 'Log in' }).click()
    await page.waitForURL('**/spaces/create/')
    await page.waitForLoadState('networkidle')

    const trustedTypesSupported = await page.evaluate(() => !!window.trustedTypes)
    assert.equal(trustedTypesSupported, true, 'Chromium did not expose window.trustedTypes')

    const protocolFieldsResponse = page.waitForResponse((response) => {
      return response.url().includes('protocol=GPG') && response.ok()
    })
    await page.locator('#id_space-access_protocol').selectOption('GPG')
    await protocolFieldsResponse
    await page.locator('#id_protocol-key').waitFor({ state: 'visible' })

    const headers = await page.evaluate(async () => {
      const response = await fetch(window.location.href, { credentials: 'same-origin' })
      return {
        csp: response.headers.get('content-security-policy'),
        cspReportOnly: response.headers.get('content-security-policy-report-only'),
      }
    })

    assert.ok(headers.csp, 'Expected enforced CSP header on Storage Service page')
    assert.ok(headers.cspReportOnly, 'Expected report-only CSP header on Storage Service page')
    assert.match(
      headers.csp,
      /require-trusted-types-for 'script'/,
      'Expected Trusted Types enforced directive',
    )
    assert.match(
      headers.csp,
      /trusted-types\b.*\bam-storage-service\b/,
      'Expected Storage Service Trusted Types policy name in enforced header',
    )
    assert.match(
      headers.cspReportOnly,
      /require-trusted-types-for 'script'/,
      'Expected Trusted Types report-only directive',
    )
    assert.match(
      headers.cspReportOnly,
      /trusted-types\b.*\bam-storage-service\b/,
      'Expected Storage Service Trusted Types policy name in report-only header',
    )

    const unexpectedConsoleErrors = consoleErrors.filter(
      (message) => !allowedConsoleErrors.some((allowed) => message.includes(allowed)),
    )
    assert.deepEqual(unexpectedConsoleErrors, [], 'Unexpected console errors were logged')
    assert.deepEqual(pageErrors, [], 'Unexpected page errors were logged')

    console.log('Storage Service Trusted Types smoke passed.')
    console.log(JSON.stringify(headers))
  } finally {
    await context.close()
    await browser.close()
  }
})().catch((error) => {
  console.error(error)
  process.exitCode = 1
})

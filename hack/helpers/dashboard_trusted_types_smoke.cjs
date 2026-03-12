const assert = require('node:assert/strict')

const { chromium } = require('playwright')

const baseUrl = process.env.DASHBOARD_BASE_URL ?? 'http://127.0.0.1:62080'
const loginUrl =
  process.env.DASHBOARD_LOGIN_URL ?? `${baseUrl}/administration/accounts/login/?next=/transfer/`
const username = process.env.DASHBOARD_USERNAME ?? 'test'
const password = process.env.DASHBOARD_PASSWORD ?? 'test'

const allowedConsoleErrors = ['favicon.ico', '/archival-storage/load_state/aips/']

const assertTrustedTypesReportOnlyHeader = async (page) => {
  const headers = await page.evaluate(async () => {
    const response = await fetch(window.location.href, { credentials: 'same-origin' })
    return {
      csp: response.headers.get('content-security-policy'),
      cspReportOnly: response.headers.get('content-security-policy-report-only'),
    }
  })

  assert.ok(headers.csp, 'Expected enforced CSP header on Dashboard page')
  assert.ok(headers.cspReportOnly, 'Expected report-only CSP header on Dashboard page')
  assert.match(
    headers.cspReportOnly,
    /require-trusted-types-for 'script'/,
    'Expected Trusted Types report-only directive',
  )
  assert.equal(
    headers.csp.includes('require-trusted-types-for'),
    false,
    'Did not expect Trusted Types in the enforced Dashboard header yet',
  )

  return headers
}

;(async () => {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()

  const consoleErrors = []
  const pageErrors = []

  page.on('console', (message) => {
    if (message.type() === 'error') {
      const location = message.location()
      consoleErrors.push(`${message.text()} @ ${location.url}`)
    }
  })

  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })

  try {
    await page.goto(loginUrl, { waitUntil: 'domcontentloaded' })

    const loginHeaders = await assertTrustedTypesReportOnlyHeader(page)
    const trustedTypesSupported = await page.evaluate(() => !!window.trustedTypes)
    assert.equal(trustedTypesSupported, true, 'Chromium did not expose window.trustedTypes')

    await page.locator('input[name="username"]').fill(username)
    await page.locator('input[name="password"]').fill(password)
    await page.getByRole('button', { name: 'Log in' }).click()
    await page.waitForURL('**/transfer/')
    await page.waitForTimeout(1500)

    const transferHeaders = await assertTrustedTypesReportOnlyHeader(page)
    assert.equal(
      await page.evaluate(() => !!document.querySelector('#transfer-browser')),
      true,
      'Expected transfer browser mount element on /transfer/',
    )
    assert.equal(
      await page.evaluate(() => !!document.querySelector('#transfer-monitor')),
      true,
      'Expected transfer monitor mount element on /transfer/',
    )

    await page.goto(`${baseUrl}/archival-storage/`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1500)

    const archivalHeaders = await assertTrustedTypesReportOnlyHeader(page)
    const archivalRouteValid = await page.evaluate(() => {
      return (
        !!document.querySelector('#archival-storage-app') ||
        document.body.textContent?.includes('Elasticsearch Indexing Disabled') === true
      )
    })
    assert.equal(archivalRouteValid, true, 'Expected archival storage route content to render')

    const unexpectedConsoleErrors = consoleErrors.filter(
      (message) => !allowedConsoleErrors.some((allowed) => message.includes(allowed)),
    )
    assert.deepEqual(unexpectedConsoleErrors, [], 'Unexpected console errors were logged')
    assert.deepEqual(pageErrors, [], 'Unexpected page errors were logged')

    console.log('Dashboard Trusted Types smoke passed.')
    console.log(JSON.stringify({ loginHeaders, transferHeaders, archivalHeaders }))
  } finally {
    await context.close()
    await browser.close()
  }
})().catch((error) => {
  console.error(error)
  process.exitCode = 1
})

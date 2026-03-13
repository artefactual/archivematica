const assert = require('node:assert/strict')
const path = require('node:path')

const { chromium } = require('playwright')

const routeManifest = require(path.join(__dirname, 'dashboard_trusted_types_routes.json'))

const baseUrl = process.env.DASHBOARD_BASE_URL ?? routeManifest.baseUrl
const loginUrl =
  process.env.DASHBOARD_LOGIN_URL ?? `${baseUrl}${routeManifest.login.path}`
const username = process.env.DASHBOARD_USERNAME ?? 'test'
const password = process.env.DASHBOARD_PASSWORD ?? 'test'
const expectTrustedTypesInCsp = (process.env.DASHBOARD_EXPECT_TT_IN_CSP ?? 'true') === 'true'
const expectTrustedTypesInCspReportOnly =
  (process.env.DASHBOARD_EXPECT_TT_IN_CSP_REPORT_ONLY ?? 'false') === 'true'
const defaultTimeoutMs = Number.parseInt(process.env.DASHBOARD_ROUTE_TIMEOUT_MS ?? '10000', 10)

const allowedConsoleErrors = routeManifest.allowedConsoleErrors ?? []

const assertTrustedTypesHeaders = async (page, routeId) => {
  const headers = await page.evaluate(async () => {
    const response = await fetch(window.location.href, { credentials: 'same-origin' })
    return {
      csp: response.headers.get('content-security-policy'),
      cspReportOnly: response.headers.get('content-security-policy-report-only'),
    }
  })

  assert.ok(headers.csp, `Expected enforced CSP header on Dashboard page for ${routeId}`)

  const cspContainsTrustedTypes = headers.csp?.includes("require-trusted-types-for 'script'") === true
  assert.equal(
    cspContainsTrustedTypes,
    expectTrustedTypesInCsp,
    `Unexpected enforced Trusted Types state for ${routeId}`,
  )

  const cspReportOnlyContainsTrustedTypes =
    headers.cspReportOnly?.includes("require-trusted-types-for 'script'") === true
  assert.equal(
    cspReportOnlyContainsTrustedTypes,
    expectTrustedTypesInCspReportOnly,
    `Unexpected report-only Trusted Types state for ${routeId}`,
  )

  if (expectTrustedTypesInCspReportOnly) {
    assert.ok(headers.cspReportOnly, `Expected report-only CSP header on Dashboard page for ${routeId}`)
  } else {
    assert.equal(headers.cspReportOnly, null, `Did not expect report-only header for ${routeId}`)
  }

  return headers
}

const waitForSelectors = async (page, selectors) => {
  for (const selector of selectors) {
    await page.locator(selector).first().waitFor({
      state: 'attached',
      timeout: defaultTimeoutMs,
    })
  }
  return selectors
}

const waitForAnySelector = async (page, selectors, routeId) => {
  for (const selector of selectors) {
    const locator = page.locator(selector).first()
    if ((await locator.count()) > 0) {
      await locator.waitFor({ state: 'attached', timeout: defaultTimeoutMs })
      return selector
    }
  }

  throw new assert.AssertionError({
    message: `Expected one of ${selectors.join(', ')} on ${routeId}`,
  })
}

const visitRoute = async (page, route) => {
  await page.goto(`${baseUrl}${route.path}`, { waitUntil: 'domcontentloaded' })

  if (route.postNavigationWaitMs) {
    await page.waitForTimeout(route.postNavigationWaitMs)
  }

  const headers = await assertTrustedTypesHeaders(page, route.id)

  const matchedSelectors = {}
  if (route.assertAllSelectors?.length) {
    matchedSelectors.all = await waitForSelectors(page, route.assertAllSelectors)
  }
  if (route.assertAnySelectors?.length) {
    matchedSelectors.any = await waitForAnySelector(page, route.assertAnySelectors, route.id)
  }

  return {
    id: route.id,
    path: route.path,
    headers,
    matchedSelectors,
  }
}

const performLogin = async (page) => {
  await page.goto(loginUrl, { waitUntil: 'domcontentloaded' })

  await page.locator(routeManifest.login.usernameSelector).fill(username)
  await page.locator(routeManifest.login.passwordSelector).fill(password)
  await page.locator(routeManifest.login.submitSelector).click()
  await page.waitForURL(`**${routeManifest.login.successPath}`)
  await page.waitForTimeout(1500)
}

;(async () => {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()

  const consoleErrors = []
  const pageErrors = []
  let currentRouteId = 'startup'

  page.on('console', (message) => {
    if (message.type() === 'error') {
      const location = message.location()
      consoleErrors.push({
        routeId: currentRouteId,
        message: `${message.text()} @ ${location.url}`,
      })
    }
  })

  page.on('pageerror', (error) => {
    pageErrors.push({
      routeId: currentRouteId,
      message: error.message,
    })
  })

  try {
    const routeResults = []
    let isLoggedIn = false

    currentRouteId = 'login'
    const loginRoute = routeManifest.routes.find((route) => route.id === 'login')
    assert.ok(loginRoute, 'Missing login route in dashboard trusted types route manifest')
    routeResults.push(await visitRoute(page, loginRoute))

    const trustedTypesSupported = await page.evaluate(() => !!window.trustedTypes)
    assert.equal(trustedTypesSupported, true, 'Chromium did not expose window.trustedTypes')

    for (const route of routeManifest.routes) {
      if (route.id === 'login') {
        continue
      }
      if (route.requiresAuth && !isLoggedIn) {
        currentRouteId = 'perform-login'
        await performLogin(page)
        isLoggedIn = true
      }
      currentRouteId = route.id
      routeResults.push(await visitRoute(page, route))
    }

    const unexpectedConsoleErrors = consoleErrors.filter(
      ({ message }) => !allowedConsoleErrors.some((allowed) => message.includes(allowed)),
    )
    assert.deepEqual(unexpectedConsoleErrors, [], 'Unexpected console errors were logged')
    assert.deepEqual(pageErrors, [], 'Unexpected page errors were logged')

    console.log('Dashboard Trusted Types smoke passed.')
    console.log(JSON.stringify(routeResults))
  } finally {
    await context.close()
    await browser.close()
  }
})().catch((error) => {
  console.error(error)
  process.exitCode = 1
})

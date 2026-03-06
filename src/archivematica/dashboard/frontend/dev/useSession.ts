import { ref } from 'vue'

const authenticated = ref(false)
const authError = ref<string | null>(null)

// Session caching helpers to reduce authentication requests.
interface CachedSession {
  csrfToken: string
  timestamp: number
  authenticated: boolean
}

const SESSION_CACHE_KEY = 'archivematica_dev_session'
const SESSION_TTL_MS = 120 * 60 * 1000 // Session expires after 120 minutes.

function getCachedSession(): CachedSession | null {
  try {
    const cached = localStorage.getItem(SESSION_CACHE_KEY)
    if (!cached) return null

    const session: CachedSession = JSON.parse(cached)
    const now = Date.now()

    // Check if session has expired based on timestamp.
    if (now - session.timestamp > SESSION_TTL_MS) {
      localStorage.removeItem(SESSION_CACHE_KEY)
      return null
    }

    return session
  } catch {
    localStorage.removeItem(SESSION_CACHE_KEY)
    return null
  }
}

function setCachedSession(csrfToken: string): void {
  try {
    const session: CachedSession = {
      csrfToken,
      timestamp: Date.now(),
      authenticated: true,
    }
    localStorage.setItem(SESSION_CACHE_KEY, JSON.stringify(session))
  } catch {
  }
}

function clearCachedSession(): void {
  localStorage.removeItem(SESSION_CACHE_KEY)
}

function restoreCachedSession(session: CachedSession): void {
  // Only restore CSRF token - sessionid is HttpOnly and managed by Django
  document.cookie = `csrftoken=${session.csrfToken}; path=/`
}

function extractCookieValue(name: string): string | null {
  const cookieString = document.cookie
  const cookies = cookieString.split(';')

  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=')
    if (cookieName === name) {
      return cookieValue ?? null
    }
  }

  return null
}

// Verify if the session is still valid by making a request to a known endpoint.
async function verifySession(): Promise<boolean> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 3000) // Abort verification after 3 seconds.

    const response = await fetch('/api/processing-configuration/', {
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    return response.status === 200
  } catch {
    return false
  }
}

// Ensure we have a valid Django session for API access.
async function establishSession() {
  try {
    // Try to use a cached session first to avoid unnecessary authentication.
    const cachedSession = getCachedSession()
    if (cachedSession) {
      restoreCachedSession(cachedSession)

      const valid = await verifySession()
      if (valid) {
        authenticated.value = true
        return
      } else {
        clearCachedSession()
        // Clear CSRF token from expired session.
        document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
      }
    }

    // Check if we already have a valid session in cookies
    // Note: sessionid cookie is HttpOnly and not accessible via JavaScript
    // We'll check if we can make authenticated requests instead
    const hasSessionId = document.cookie.includes('sessionid=')
    if (hasSessionId) {
      const valid = await verifySession()
      if (valid) {
        authenticated.value = true

        // Cache this valid session for future use to improve performance.
        const csrfToken = extractCookieValue('csrftoken')
        if (csrfToken) {
          setCachedSession(csrfToken)
        }
        return
      } else {
        // Clear invalid session cookies.
        document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
        document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
      }
    }

    // Get the login page to retrieve CSRF token with timeout protection.
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000) // Abort request after 5 seconds.

    const loginPageResponse = await fetch('/administration/accounts/login/', {
      credentials: 'include',
      signal: controller.signal,
    })
    clearTimeout(timeoutId)

    const loginPageText = await loginPageResponse.text()
    const csrfMatch = loginPageText.match(/name=['\"]csrfmiddlewaretoken['\"] value=['\"]([^'\"]+)['\"]/)

    if (!csrfMatch) {
      throw new Error('Could not find CSRF token in login page')
    }

    const csrfToken = csrfMatch[1]
    if (!csrfToken) {
      throw new Error('Login page returned an invalid CSRF token')
    }

    // Perform login with test credentials.
    const formData = new URLSearchParams()
    formData.append('username', 'test')
    formData.append('password', 'test')
    formData.append('csrfmiddlewaretoken', csrfToken)
    formData.append('next', '/')

    const loginController = new AbortController()
    const loginTimeoutId = setTimeout(() => loginController.abort(), 5000) // Abort login after 5 seconds.

    const loginResponse = await fetch('/administration/accounts/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
      credentials: 'include',
      redirect: 'follow',
      signal: loginController.signal,
    })
    clearTimeout(loginTimeoutId)

    // Check if we were redirected to a success page (not back to login)
    const isLoginPage = loginResponse.url.includes('/administration/accounts/login/')

    if (loginResponse.status === 200 && !isLoginPage) {
      // Set CSRF token for API calls.
      document.cookie = `csrftoken=${csrfToken}; path=/`

      // Verify session is working before marking as authenticated.
      const sessionValid = await verifySession()
      if (sessionValid) {
        authenticated.value = true

        // Cache the CSRF token and auth state for future use.
        setCachedSession(csrfToken)
      } else {
        throw new Error('Session verification failed after login')
      }
    } else if (isLoginPage) {
      // We were redirected back to login page, meaning login failed.
      const responseText = await loginResponse.text()
      if (responseText.includes('Please enter a correct username and password')) {
        throw new Error('Invalid username or password')
      } else {
        throw new Error('Login failed - redirected back to login page')
      }
    } else {
      throw new Error(`Login failed with status: ${loginResponse.status}`)
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      // For development, if backend is unreachable, allow access anyway.
      console.warn('Backend server is not reachable. Running in development mode without authentication.')
      authenticated.value = true
      authError.value = null
    } else {
      // For development, allow access even when authentication fails.
      console.warn('Authentication failed, but allowing access for development:', error instanceof Error ? error.message : 'Unknown error')
      authenticated.value = true
      authError.value = null
    }
    // Clear any cached session on authentication failure.
    clearCachedSession()
  }
}

export function useSession() {
  return {
    authenticated,
    authError,
    establishSession,
    verifySession,
  }
}

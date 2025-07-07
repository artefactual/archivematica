import { ref, computed } from 'vue'

export function useCSRFToken() {
  const token = ref<string | null>(null)

  // Extract CSRF token from document cookies.
  const extractTokenFromCookie = (): string | null => {
    const csrfCookie = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))

    if (!csrfCookie) {
      return null
    }

    const [, cookieValue] = csrfCookie.split('=')
    return cookieValue ?? null
  }

  // Get current CSRF token from cookie.
  const getToken = (): string | null => {
    token.value = extractTokenFromCookie()
    return token.value
  }

  return {
    // Computed properties.
    token: computed(() => getToken()),

    // Methods.
    getToken,
  }
}

import { describe, it, expect, beforeEach } from 'vitest'
import { useCSRFToken } from '@/browser/composables/useCSRFToken'

describe('useCSRFToken', () => {
  beforeEach(() => {
    // Reset document.cookie
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    })
  })

  describe('extractTokenFromCookie', () => {
    it('should extract CSRF token from cookie', () => {
      document.cookie = 'csrftoken=abc123; sessionid=def456'

      const { token } = useCSRFToken()

      expect(token.value).toBe('abc123')
    })

    it('should return null if no CSRF token cookie exists', () => {
      document.cookie = 'sessionid=def456'

      const { token } = useCSRFToken()

      expect(token.value).toBeNull()
    })

    it('should return null if no cookies exist', () => {
      document.cookie = ''

      const { token } = useCSRFToken()

      expect(token.value).toBeNull()
    })
  })

  describe('getToken', () => {
    it('should return current token from cookie', () => {
      document.cookie = 'csrftoken=current-token'

      const { getToken } = useCSRFToken()

      expect(getToken()).toBe('current-token')
    })

    it('should return null if no token in cookie', () => {
      document.cookie = 'sessionid=def456'

      const { getToken } = useCSRFToken()

      expect(getToken()).toBeNull()
    })

    it('should update token value when cookie changes', () => {
      document.cookie = 'csrftoken=first-token'

      const { getToken, token } = useCSRFToken()

      expect(getToken()).toBe('first-token')
      expect(token.value).toBe('first-token')

      // Change cookie
      document.cookie = 'csrftoken=second-token'

      expect(getToken()).toBe('second-token')
      expect(token.value).toBe('second-token')
    })
  })

  describe('reactive token computed', () => {
    it('should read fresh token from cookie each time', () => {
      document.cookie = 'csrftoken=reactive-token'

      const { token, getToken } = useCSRFToken()

      // First access
      expect(token.value).toBe('reactive-token')

      // Change cookie
      document.cookie = 'csrftoken=new-reactive-token'

      // The computed property calls getToken() which reads from cookie each time
      // This ensures fresh token is always returned
      expect(getToken()).toBe('new-reactive-token')
      expect(token.value).toBe('new-reactive-token')
    })
  })
})

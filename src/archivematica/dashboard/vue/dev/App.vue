<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import TransferBrowser from '@/browser/App.vue'
import { useLanguage } from './useLanguage'
import { useSession } from './useSession'
import { type AvailableLocale } from '@/shared/i18n'

const currentPath = ref(window.location.pathname)

const { authenticated, authError, establishSession } = useSession()

const {
  currentLanguage,
  currentLanguageName,
  availableLanguages,
  selectLanguage,
} = useLanguage()

// Toggle dropdown visibility using direct DOM manipulation for simplicity.
const toggleDropdown = (event: Event) => {
  event.preventDefault()
  const dropdown = document.getElementById('lang-dropdown')
  if (dropdown) {
    dropdown.classList.toggle('open')
  }
}

// Close dropdown when clicking outside to improve UX.
const handleClickOutside = (event: MouseEvent) => {
  const dropdown = document.querySelector('.dropdown')
  if (dropdown && !dropdown.contains(event.target as Node)) {
    dropdown.classList.remove('open')
  }
}

const chooseLanguage = (langCode: AvailableLocale) => {
  selectLanguage(langCode)
  const dropdown = document.querySelector('.dropdown')
  if (dropdown) {
    dropdown.classList.remove('open')
  }
}

const routes = {
  browser: {
    component: TransferBrowser,
    title: 'Transfer Browser',
  },
}

function getRouteKey(path: string): string {
  const firstPathComponent = path.split('/')[1]
  return firstPathComponent || 'browser'
}

const currentComponent = computed(() => {
  const routeKey = getRouteKey(currentPath.value)
  return routes[routeKey as keyof typeof routes]?.component
})

const pageTitle = computed(() => {
  const routeKey = getRouteKey(currentPath.value)
  return routes[routeKey as keyof typeof routes]?.title
})

function handlePopState() {
  currentPath.value = window.location.pathname
}

function navigateTo(path: string, event: Event) {
  event.preventDefault()
  history.pushState(null, '', path)
  currentPath.value = path
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState)
  window.addEventListener('click', handleClickOutside)
  establishSession()
})

onUnmounted(() => {
  window.removeEventListener('popstate', handlePopState)
  window.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="page-container">
    <nav class="navbar navbar-default">
      <div class="container-fluid">
        <div class="navbar-header">
          <a
            class="navbar-brand"
            href="#"
          >
            <img
              src="/vite.svg"
              alt="Vite"
              class="logo"
            >
            Vue Components
          </a>
        </div>
        <ul class="nav navbar-nav">
          <li :class="{ active: currentPath === '/browser' || currentPath === '/' }">
            <a
              href="/browser"
              @click="navigateTo('/browser', $event)"
            >Transfer Browser</a>
          </li>
        </ul>
        <ul class="nav navbar-nav navbar-right">
          <li
            id="lang-dropdown"
            class="dropdown"
          >
            <button
              type="button"
              class="btn btn-default dropdown-toggle"
              @click="toggleDropdown"
            >
              <i class="fa fa-globe" />
              {{ currentLanguageName }}
              <span class="caret" />
            </button>
            <ul class="dropdown-menu">
              <li
                v-for="lang in availableLanguages"
                :key="lang.code"
              >
                <a
                  href="#"
                  @click.prevent="chooseLanguage(lang.code as AvailableLocale)"
                >
                  {{ lang.name }}
                  <span v-if="lang.code === currentLanguage"> ✓</span>
                </a>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </nav>

    <div class="page-header">
      <h1>{{ pageTitle }}</h1>
    </div>

    <div
      v-if="!authenticated && !authError"
      class="alert alert-info"
    >
      <i class="fa fa-spinner fa-spin" /> Authenticating...
    </div>
    <div
      v-else-if="authError"
      class="alert alert-danger"
    >
      <strong>Authentication Failed</strong><br>
      {{ authError }}<br><br>
      <small>Make sure Django server is running on http://127.0.0.1:62080/ and restart it if you just updated settings.</small>
    </div>
    <div
      v-if="authenticated"
      class="page-container"
    >
      <component :is="currentComponent" />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  border-bottom: 1px solid #e5e5e5;
}

.page-header h1 {
  color: #333;
  margin: 0;
  font-size: 24px;
  font-weight: 300;
}

.logo {
  height: 20px;
  float: left;
  margin-right: 8px;
  margin-top: -2px;
}

/* Loading states for language dropdown */
.dropdown-toggle.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dropdown-menu li.disabled > a {
  color: #999;
  cursor: not-allowed;
  pointer-events: none;
}

.dropdown-menu li.disabled > a:hover,
.dropdown-menu li.disabled > a:focus {
  background-color: transparent;
  color: #999;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.page-container > .component {
  padding: 40px;
}

/* Language dropdown styles */
.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle {
  background: none;
  border: none;
  color: #777;
  text-decoration: none;
  padding: 10px 15px;
  line-height: 20px;
  display: block;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.15s ease-in-out;
}

.dropdown-toggle:hover,
.dropdown-toggle:focus {
  color: #333;
  background-color: transparent;
  outline: none;
}

.dropdown-toggle .caret {
  margin-left: 5px;
  vertical-align: middle;
  border-top: 4px solid;
  border-right: 4px solid transparent;
  border-left: 4px solid transparent;
  display: inline-block;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 1000;
  display: none;
  float: left;
  min-width: 180px;
  padding: 5px 0;
  margin: 2px 0 0;
  font-size: 14px;
  text-align: left;
  list-style: none;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ccc;
  border: 1px solid rgba(0, 0, 0, .15);
  border-radius: 4px;
  box-shadow: 0 6px 12px rgba(0, 0, 0, .175);
  transform: translateY(-2px);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s ease-in-out, transform 0.15s ease-in-out;
}

.dropdown.open .dropdown-menu {
  display: block !important;
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateY(0) !important;
}

.dropdown-menu > li > a {
  display: block;
  padding: 8px 20px;
  clear: both;
  font-weight: 400;
  line-height: 1.42857143;
  color: #333;
  white-space: nowrap;
  text-decoration: none;
  transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
  border-radius: 0 !important;
}

.dropdown-menu > li:first-child > a {
  border-top-left-radius: 3px !important;
  border-top-right-radius: 3px !important;
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
}

.dropdown-menu > li:last-child > a {
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important;
  border-bottom-left-radius: 3px !important;
  border-bottom-right-radius: 3px !important;
}

.dropdown-menu > li > a:hover,
.dropdown-menu > li > a:focus {
  color: #262626;
  text-decoration: none;
  background-color: #f5f5f5;
}

.dropdown-menu > li > a:active {
  color: #fff;
  text-decoration: none;
  background-color: #337ab7;
}

/* Current language indicator */
.dropdown-menu > li > a span {
  float: right;
  color: #337ab7;
  font-weight: bold;
  margin-left: 10px;
}

.fa-globe {
  margin-right: 6px;
  opacity: 0.7;
}

/* Navbar integration */
.navbar-nav > li > .dropdown-toggle {
  padding-top: 15px;
  padding-bottom: 15px;
  margin: 0;
  border: none;
  background: none;
  color: #777;
}

.navbar-nav > li:hover > .dropdown-toggle,
.navbar-nav > li.open > .dropdown-toggle {
  color: #333;
  background-color: #e7e7e7;
}

/* Responsive adjustments */
@media (max-width: 767px) {
  .dropdown-menu {
    position: static;
    float: none;
    width: auto;
    margin-top: 0;
    background-color: transparent;
    border: 0;
    box-shadow: none;
  }

  .dropdown-menu > li > a {
    padding: 5px 15px 5px 25px;
  }
}
</style>

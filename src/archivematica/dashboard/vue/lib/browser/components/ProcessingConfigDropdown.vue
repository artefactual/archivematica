<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import type { ProcessingConfig } from '@/browser/types'

const props = withDefaults(defineProps<{
  configs: ProcessingConfig[]
  disabled?: boolean
  startLabel: string
  submissionOptionsLabel: string
  showConfigOptionsLabel: string
  startWithConfigLabel: (configName: string) => string
  defaultConfigName?: string
}>(), {
  disabled: false,
  defaultConfigName: 'default',
})

const emit = defineEmits<{
  'start-default': []
  'start-config': [configPk: string]
}>()

const isOpen = ref(false)
const currentIndex = ref(-1)
const dropdownButtonRef = ref<HTMLElement>()
const dropdownMenuRef = ref<HTMLElement>()
const searchBuffer = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const getDropdownItems = (): HTMLElement[] => {
  if (!dropdownMenuRef.value) {
    return []
  }
  return Array.from(dropdownMenuRef.value.querySelectorAll<HTMLElement>('a[role="menuitem"]'))
}

const openDropdown = (focusFirst = false) => {
  if (props.disabled) {
    return
  }
  isOpen.value = true
  currentIndex.value = -1
  if (focusFirst) {
    nextTick(() => {
      const items = getDropdownItems()
      if (items.length > 0) {
        currentIndex.value = 0
        items[0]?.focus()
      }
    })
  }
}

const closeDropdown = () => {
  isOpen.value = false
}

const toggleDropdown = () => {
  if (isOpen.value) {
    closeDropdown()
    return
  }
  openDropdown(false)
}

const handleStartDefault = () => {
  closeDropdown()
  emit('start-default')
}

const handleSelectConfig = (configPk: string) => {
  emit('start-config', configPk)
  closeDropdown()
}

const handleDropdownButtonKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
    case ' ': {
      event.preventDefault()
      if (isOpen.value) {
        closeDropdown()
        return
      }
      openDropdown(true)
      break
    }
    case 'ArrowDown':
      event.preventDefault()
      openDropdown(true)
      break
  }
}

const handleDropdownKeyDown = (event: KeyboardEvent) => {
  const menuItems = getDropdownItems()
  if (menuItems.length === 0) {
    return
  }

  switch (event.key) {
    case 'Escape':
      closeDropdown()
      dropdownButtonRef.value?.focus()
      break
    case 'Tab':
      closeDropdown()
      break
    case 'ArrowDown': {
      event.preventDefault()
      currentIndex.value = Math.min(currentIndex.value + 1, menuItems.length - 1)
      menuItems[currentIndex.value]?.focus()
      break
    }
    case 'ArrowUp': {
      event.preventDefault()
      currentIndex.value = Math.max(currentIndex.value - 1, 0)
      menuItems[currentIndex.value]?.focus()
      break
    }
    case 'Home': {
      event.preventDefault()
      currentIndex.value = 0
      menuItems[0]?.focus()
      break
    }
    case 'End': {
      event.preventDefault()
      currentIndex.value = menuItems.length - 1
      menuItems[currentIndex.value]?.focus()
      break
    }
    default:
      if (event.key.length === 1 && event.key.trim() !== '' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault()
        searchBuffer.value += event.key.toLowerCase()
        if (searchTimeout) {
          clearTimeout(searchTimeout)
        }
        searchTimeout = setTimeout(() => {
          searchBuffer.value = ''
        }, 1000)
        const matchIndex = menuItems.findIndex(item =>
          item.textContent?.toLowerCase().startsWith(searchBuffer.value),
        )
        if (matchIndex !== -1) {
          currentIndex.value = matchIndex
          menuItems[matchIndex]?.focus()
        }
      }
  }
}

const handleClickOutside = (event: MouseEvent) => {
  if (!dropdownButtonRef.value || !dropdownMenuRef.value) {
    return
  }
  const target = event.target as HTMLElement
  if (!dropdownButtonRef.value.contains(target) && !dropdownMenuRef.value.contains(target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<template>
  <div
    class="btn-group dropdown"
    :class="{ open: isOpen }"
    role="group"
    :aria-label="submissionOptionsLabel"
  >
    <button
      type="button"
      class="btn btn-success"
      :disabled="props.disabled"
      :aria-disabled="props.disabled"
      :aria-label="startWithConfigLabel(props.defaultConfigName)"
      @click="handleStartDefault"
    >
      {{ props.startLabel }}
    </button>
    <button
      ref="dropdownButtonRef"
      type="button"
      class="btn btn-success dropdown-toggle"
      :disabled="props.disabled"
      :aria-disabled="props.disabled"
      :aria-expanded="isOpen"
      aria-haspopup="true"
      :aria-label="props.showConfigOptionsLabel"
      @click="toggleDropdown"
      @keydown="handleDropdownButtonKeyDown"
    >
      <span class="caret" />
    </button>
    <ul
      ref="dropdownMenuRef"
      class="dropdown-menu dropdown-menu-right"
      role="menu"
      @keydown="handleDropdownKeyDown"
    >
      <li
        v-for="config in props.configs"
        :key="config.pk"
        role="presentation"
      >
        <a
          href="#"
          role="menuitem"
          class="processing-config-choice"
          :aria-label="startWithConfigLabel(config.name)"
          :tabindex="isOpen ? 0 : -1"
          @click.prevent="handleSelectConfig(config.pk)"
          @keydown.enter.prevent="handleSelectConfig(config.pk)"
          @keydown.space.prevent="handleSelectConfig(config.pk)"
          @keydown="handleDropdownKeyDown"
        >
          {{ startWithConfigLabel(config.name) }}
        </a>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.processing-config-choice {
  display: block;
  color: #333;
  text-decoration: none;
}

.processing-config-choice:hover {
  background-color: #f5f5f5;
  color: #333;
  text-decoration: none;
}
</style>

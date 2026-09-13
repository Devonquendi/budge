/**
 * Light/dark preference, in three states: an explicit choice wins, and with no
 * choice stored we follow the system. MediaQuery keeps the system case live, so
 * the toggle's icon is right even if nothing has been clicked yet.
 */

import { MediaQuery } from 'svelte/reactivity'

const THEME_KEY = 'budge-theme'

type Theme = 'light' | 'dark'

const systemPrefersDark = new MediaQuery('prefers-color-scheme: dark')
const chosen = $state<{ theme: Theme | null }>({ theme: null })

function read(): Theme | null {
  try {
    const stored = localStorage.getItem(THEME_KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    // localStorage unavailable (private browsing, etc.) — the system
    // preference in app.css still applies.
    return null
  }
}

/** Run before mounting: sets data-theme from storage, if anything is stored. */
export function applyStoredTheme(): void {
  chosen.theme = read()
  if (chosen.theme) document.documentElement.dataset.theme = chosen.theme
}

export function followsSystem(): boolean {
  return chosen.theme === null
}

export function followSystem(): void {
  chosen.theme = null
  delete document.documentElement.dataset.theme
  try {
    localStorage.removeItem(THEME_KEY)
  } catch {
    // Nothing stored to remove, which is the state we wanted anyway.
  }
}

export function isDark(): boolean {
  return chosen.theme ? chosen.theme === 'dark' : systemPrefersDark.current
}

export function setTheme(theme: Theme): void {
  chosen.theme = theme
  document.documentElement.dataset.theme = theme
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    // Ignore — the theme just won't persist across reloads.
  }
}

export function toggleTheme(): void {
  setTheme(isDark() ? 'light' : 'dark')
}

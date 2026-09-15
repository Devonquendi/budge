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

const THEME_COLOR_ID = 'theme-color-choice'

/**
 * A phone tints its browser chrome from <meta name="theme-color">, and uses the
 * first tag whose media matches. index.html declares one per system scheme; an
 * explicit choice matches neither, so put an unscoped tag in front of them and
 * take it away again when we go back to following the system. The colour is
 * read off the page rather than repeated here, so it can't drift from app.css.
 */
function applyThemeColor(): void {
  document.getElementById(THEME_COLOR_ID)?.remove()
  if (!chosen.theme) return

  const mantle = getComputedStyle(document.documentElement)
    .getPropertyValue('--ctp-mantle')
    .trim()
  if (!mantle) return

  const meta = document.createElement('meta')
  meta.id = THEME_COLOR_ID
  meta.name = 'theme-color'
  meta.content = mantle
  document.head.prepend(meta)
}

function read(): Theme | null {
  try {
    const stored = localStorage.getItem(THEME_KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    // localStorage unavailable (private browsing, etc.), so the system
    // preference in app.css still applies.
    return null
  }
}

/** Run before mounting: sets data-theme from storage, if anything is stored. */
export function applyStoredTheme(): void {
  chosen.theme = read()
  if (chosen.theme) document.documentElement.dataset.theme = chosen.theme
  applyThemeColor()
}

export function followsSystem(): boolean {
  return chosen.theme === null
}

export function followSystem(): void {
  chosen.theme = null
  delete document.documentElement.dataset.theme
  applyThemeColor()
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
  applyThemeColor()
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    // Ignore: the theme just won't persist across reloads.
  }
}

export function toggleTheme(): void {
  setTheme(isDark() ? 'light' : 'dark')
}

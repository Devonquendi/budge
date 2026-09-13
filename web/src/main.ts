import { mount } from 'svelte'

// Pico first: app.css themes it by overriding its variables, so it has to load
// underneath.
import '@picocss/pico/css/pico.min.css'
import './app.css'

import App from './App.svelte'
import { applyStoredTheme } from './lib/theme.svelte'

// Before mounting, so the page never flashes the wrong theme.
applyStoredTheme()

export default mount(App, {
  target: document.getElementById('app')!,
})

import { mount } from 'svelte'

import './app.css'
import App from './App.svelte'
import { applyStoredTheme } from './lib/theme.svelte'

// Before mounting, so the page never flashes the wrong theme.
applyStoredTheme()

export default mount(App, {
  target: document.getElementById('app')!,
})

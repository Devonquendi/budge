/**
 * A history-API router in thirty lines. Six flat pages with no nested layouts
 * isn't enough to justify a dependency — SvelteKit is ruled out by the
 * architecture, and everything else would be more code than this.
 */

const state = $state({ path: window.location.pathname })

/** The current path. Read it in a template or a `$derived` and it stays live. */
export function path(): string {
  return state.path
}

export function navigate(to: string, { replace = false } = {}): void {
  if (to === state.path) return
  if (replace) history.replaceState({}, '', to)
  else history.pushState({}, '', to)
  state.path = to
  window.scrollTo(0, 0)
}

// Back and forward move the same state the links do.
window.addEventListener('popstate', () => {
  state.path = window.location.pathname
})

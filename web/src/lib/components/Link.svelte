<script lang="ts">
  import type { Snippet } from 'svelte'
  import { navigate, path } from '../router.svelte'

  let {
    href,
    children,
    onclick,
    ...rest
  }: {
    href: string
    children: Snippet
    /** Runs alongside the routing, not instead of it. */
    onclick?: (event: MouseEvent) => void
    [key: string]: unknown
  } = $props()

  const current = $derived(path() === href ? 'page' : undefined)

  function intercept(event: MouseEvent) {
    onclick?.(event)
    // Leave modified clicks alone so "open in new tab" still works.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return
    event.preventDefault()
    navigate(href)
  }
</script>

<!-- rest before onclick: spread last, a passed-in handler would silently
     replace the routing and every link would reload the page. -->
<a {href} aria-current={current} {...rest} onclick={intercept}>{@render children()}</a>

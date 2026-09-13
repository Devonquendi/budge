<script lang="ts">
  import type { Snippet } from 'svelte'
  import { navigate, path } from '../router.svelte'

  let {
    href,
    children,
    ...rest
  }: { href: string; children: Snippet; [key: string]: unknown } = $props()

  const current = $derived(path() === href ? 'page' : undefined)

  function intercept(event: MouseEvent) {
    // Leave modified clicks alone so "open in new tab" still works.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return
    event.preventDefault()
    navigate(href)
  }
</script>

<a {href} aria-current={current} onclick={intercept} {...rest}>{@render children()}</a>

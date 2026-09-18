<script lang="ts">
  import type { Settled } from '../api'
  import Link from './Link.svelte'
  import { formatCents } from '../money'

  // The far end of the loop. Money arrived, it closed a request, and the row it
  // arrived on should say which one rather than leaving you to remember.
  let {
    settled,
    compact = false,
  }: {
    settled: Settled
    /** For rows too narrow to carry the detail. The link still works. */
    compact?: boolean
  } = $props()
</script>

<Link
  href="/r/{settled.token}"
  class={['settled-mark', { compact }]}
  title="Settles {settled.who}'s {formatCents(
    settled.amount_cents,
    'NZD',
  )} share of {settled.title}"
>
  {#if compact}
    Settled
  {:else}
    Settles {settled.who} · {settled.title}
  {/if}
</Link>

<style>
  :global(.settled-mark) {
    display: inline-block;
    padding: 0.0625rem 0.375rem;
    border-radius: 999px;
    font-size: var(--text-micro);
    font-weight: 500;
    white-space: nowrap;
    text-decoration: none;
    background: color-mix(in oklab, var(--ctp-green) 20%, transparent);
    color: var(--ctp-green);
  }

  :global(.settled-mark:hover) {
    background: color-mix(in oklab, var(--ctp-green) 32%, transparent);
  }

  :global(.settled-mark.compact) {
    flex: none;
    padding: 0.0625rem 0.25rem;
    font-size: 0.5625rem;
    line-height: 1.5;
    text-transform: uppercase;
  }
</style>

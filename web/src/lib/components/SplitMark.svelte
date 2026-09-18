<script lang="ts">
  import type { SplitSummary } from '../api'
  import { formatCents } from '../money'

  // The lasting answer to "did I already ask anyone for this?". Without it a
  // split leaves no trace on the ledger, and the only way to find out is to go
  // looking through requests.
  let { summary }: { summary: SplitSummary } = $props()

  const settled = $derived(summary.outstanding_cents === 0)
</script>

<span
  class={['split-mark', { settled }]}
  title={settled
    ? `All ${summary.people} paid up`
    : `${formatCents(summary.outstanding_cents, 'NZD')} still owed by ${summary.people}`}
>
  {#if settled}
    Split · paid
  {:else}
    Split · {formatCents(summary.outstanding_cents, 'NZD')} owed
  {/if}
</span>

<style>
  .split-mark {
    display: inline-block;
    padding: 0.0625rem 0.375rem;
    border-radius: 999px;
    font-size: var(--text-micro);
    font-weight: 500;
    white-space: nowrap;
    background: color-mix(in oklab, var(--ctp-yellow) 20%, transparent);
    color: var(--ctp-yellow);
  }

  .settled {
    background: color-mix(in oklab, var(--ctp-green) 20%, transparent);
    color: var(--ctp-green);
  }
</style>

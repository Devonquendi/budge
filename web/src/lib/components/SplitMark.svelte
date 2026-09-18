<script lang="ts">
  import type { SplitSummary } from '../api'
  import { formatCents } from '../money'

  // The lasting answer to "did I already ask anyone for this?". Without it a
  // split leaves no trace on the ledger, and the only way to find out is to go
  // looking through requests.
  let {
    summary,
    compact = false,
  }: {
    summary: SplitSummary
    /** For rows too narrow to carry the figure. The tooltip still has it. */
    compact?: boolean
  } = $props()

  const settled = $derived(summary.outstanding_cents === 0)
</script>

<span
  class={['split-mark', { settled, compact }]}
  title={settled
    ? `Split ${summary.people} ways, all paid up`
    : `Split ${summary.people} ways, ${formatCents(summary.outstanding_cents, 'NZD')} still owed`}
>
  {#if compact}
    Split
  {:else if settled}
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

  /* Its own column rather than inside the merchant name, which truncates: the
     badge was being clipped away entirely on the dashboard. */
  .compact {
    flex: none;
    padding: 0.0625rem 0.25rem;
    font-size: 0.5625rem;
    line-height: 1.5;
    text-transform: uppercase;
  }
</style>

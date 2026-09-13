<script lang="ts">
  import { categoryColor } from '../categories'
  import { formatCents } from '../money'
  import type { Slice } from '../spending'

  let {
    slices,
    currency,
    limit = 6,
  }: {
    slices: Slice[]
    currency: string
    /** Anything past this is folded into a single "Other" bar. */
    limit?: number
  } = $props()

  type Bar = Slice & { color: string; width: string }

  /**
   * Bars are drawn against the largest category rather than the total, so the
   * smallest one is still legible instead of a sliver — this is a ranking, not
   * a pie chart.
   */
  const bars = $derived.by((): Bar[] => {
    const shown: Slice[] = slices.slice(0, limit)
    const rest = slices.slice(limit).reduce((sum, slice) => sum + slice.cents, 0)
    if (rest > 0) shown.push({ name: 'Other', cents: rest })

    const largest = shown[0]?.cents ?? 0

    return shown.map((slice) => ({
      ...slice,
      color: categoryColor(slice.name === 'Other' ? null : slice.name),
      width: largest
        ? `${Math.max(Math.round((slice.cents / largest) * 100), 2)}%`
        : '0%',
    }))
  })
</script>

{#if bars.length === 0}
  <p class="empty muted">Nothing spent yet this month</p>
{:else}
  <ul>
    {#each bars as bar (bar.name)}
      <li>
        <span class="line">
          <span class="name">{bar.name}</span>
          <span class="amount numeric muted">{formatCents(bar.cents, currency)}</span>
        </span>
        <span class="track">
          <span class="fill" style:--accent={bar.color} style:width={bar.width}></span>
        </span>
      </li>
    {/each}
  </ul>
{/if}

<style>
  ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.4375rem;
    margin: 0;
    padding: 0;
  }

  li {
    display: flex;
    flex-direction: column;
    gap: 0.1875rem;
  }

  .line {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    font-size: var(--text-label);
  }

  .name {
    margin-right: auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .amount {
    white-space: nowrap;
  }

  .track {
    display: block;
    height: 0.25rem;
    overflow: hidden;
    border-radius: 999px;
    background: var(--ctp-surface0);
  }

  .fill {
    display: block;
    height: 100%;
    border-radius: 999px;
    background: var(--accent);
  }

  .empty {
    margin: 0;
    padding-block: 1rem;
    text-align: center;
    font-size: var(--text-label);
  }
</style>

<script lang="ts">
  import type { Transaction } from '../api'
  import { format, toCents } from '../money'

  let { transactions }: { transactions: Transaction[] } = $props()

  const dayFormat = new Intl.DateTimeFormat('en-NZ', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })

  type Day = { key: string; label: string; rows: Transaction[] }

  // One heading per date, which is how a bank statement reads and how you
  // actually scan for "what did I spend on Saturday".
  const days = $derived.by((): Day[] => {
    const groups = new Map<string, Day>()

    for (const transaction of transactions) {
      const date = new Date(transaction.date)
      const key = date.toDateString()
      let day = groups.get(key)
      if (!day) {
        day = { key, label: dayFormat.format(date), rows: [] }
        groups.set(key, day)
      }
      day.rows.push(transaction)
    }

    return [...groups.values()]
  })

  /** The merchant if Akahu or Genie named one, else the bank's own line. */
  function title(transaction: Transaction): string {
    return transaction.merchant?.name ?? transaction.description
  }
</script>

{#each days as day (day.key)}
  <section>
    <h2 class="eyebrow">{day.label}</h2>

    <ul>
      {#each day.rows as transaction (transaction.id)}
        {@const cents = toCents(transaction.amount)}
        <li>
          <span class="who">
            <span class="name">{title(transaction)}</span>
            <span class="meta muted">
              {#if transaction.category}
                <span
                  class={['tag', { guess: transaction.category.source === 'genie' }]}
                  title={transaction.category.source === 'genie'
                    ? `Genie's guess, ${Math.round((transaction.category.confidence ?? 0) * 100)}% confident`
                    : 'Categorised by Akahu'}
                >
                  {transaction.category.name}
                </span>
              {:else}
                <span class="tag unknown">Uncategorised</span>
              {/if}
              {transaction.account_name}
            </span>
          </span>

          <span class={['amount', 'numeric', { incoming: cents > 0 }]}>
            {cents > 0 ? '+' : ''}{format(transaction.amount, transaction.currency)}
          </span>
        </li>
      {/each}
    </ul>
  </section>
{:else}
  <p class="muted empty">No transactions in this period.</p>
{/each}

<style>
  section {
    margin-bottom: 2rem;
  }

  h2 {
    margin: 0 0 0.5rem;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: var(--pico-card-background-color);
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
  }

  li {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    padding: 0.75rem 1.125rem;
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  .who {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 0;
    margin-right: auto;
  }

  .name {
    font-weight: 600;
    /* Bank descriptions run long; one line each keeps the column scannable. */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    font-size: 0.8125rem;
    line-height: 1.35;
  }

  .tag {
    padding: 0.0625rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 999px;
    background: color-mix(in srgb, var(--ctp-green) 18%, transparent);
    color: var(--ctp-green);
  }

  /* Genie matched on the description alone, so it's a guess, not a fact. */
  .guess {
    background: color-mix(in srgb, var(--ctp-mauve) 18%, transparent);
    color: var(--ctp-mauve);
  }

  .unknown {
    background: color-mix(in srgb, var(--pico-muted-color) 14%, transparent);
    color: var(--pico-muted-color);
  }

  .amount {
    font-weight: 600;
    white-space: nowrap;
  }

  .incoming {
    color: var(--ctp-green);
  }

  .empty {
    padding-block: 2rem;
    text-align: center;
  }
</style>

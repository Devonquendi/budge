<script lang="ts">
  import type { Account, Transaction } from '../api'
  import { formatCents, toCents } from '../money'
  import { prefs } from '../prefs.svelte'
  import type { Totals } from '../workspace.svelte'

  let {
    totals,
    accounts,
    transactions,
  }: {
    totals: Totals[]
    accounts: Account[]
    transactions: Transaction[]
  } = $props()

  type Tone = 'ink' | 'green' | 'red'
  type Stat = { label: string; value: string; note: string; tone: Tone }

  const monthName = new Intl.DateTimeFormat('en-NZ', { month: 'short' })

  function flows(currency: string) {
    const now = new Date()
    const month = now.getMonth()
    const year = now.getFullYear()

    let incoming = 0
    let outgoing = 0
    let deposits = 0
    let payments = 0

    for (const transaction of transactions) {
      if (transaction.currency !== currency) continue
      const date = new Date(transaction.date)
      if (date.getMonth() !== month || date.getFullYear() !== year) continue

      const cents = toCents(transaction.amount)
      if (cents > 0) {
        incoming += cents
        deposits += 1
      } else {
        outgoing += cents
        payments += 1
      }
    }

    return { incoming, outgoing, deposits, payments }
  }

  function owingCount(currency: string): number {
    return accounts.filter(
      (account) =>
        account.currency === currency && toCents(account.balance_current) < 0,
    ).length
  }

  function plural(count: number, one: string, many = `${one}s`): string {
    return `${count} ${count === 1 ? one : many}`
  }

  const groups = $derived(
    totals.map((total) => {
      const { currency } = total
      const round = prefs().hideCents
      const { incoming, outgoing, deposits, payments } = flows(currency)
      const movement = incoming + outgoing
      const owing = owingCount(currency)
      const month = monthName.format(new Date())

      const stats: Stat[] = [
        {
          label: 'Net',
          value: formatCents(total.net, currency, round),
          note: `${movement >= 0 ? '+' : ''}${formatCents(movement, currency)} this month`,
          tone: 'ink',
        },
        {
          label: 'Assets',
          value: formatCents(total.assets, currency, round),
          note: plural(total.count - owing, 'account'),
          tone: 'ink',
        },
      ]

      if (total.owing !== 0) {
        stats.push({
          label: 'Owing',
          value: formatCents(total.owing, currency, round),
          note: plural(owing, 'account'),
          tone: 'red',
        })
      }

      stats.push(
        {
          label: `In · ${month}`,
          value: formatCents(incoming, currency),
          note: plural(deposits, 'deposit'),
          tone: 'green',
        },
        {
          label: `Out · ${month}`,
          value: formatCents(Math.abs(outgoing), currency),
          note: plural(payments, 'transaction'),
          tone: 'ink',
        },
      )

      return { currency, stats }
    }),
  )
</script>

{#each groups as group (group.currency)}
  {#if groups.length > 1}
    <p class="eyebrow currency">{group.currency}</p>
  {/if}
  <div class="tiles">
    {#each group.stats as stat (stat.label)}
      <div class="tile">
        <p class="eyebrow">{stat.label}</p>
        <p class={['value', 'numeric', stat.tone]}>{stat.value}</p>
        <p class="note muted">{stat.note}</p>
      </div>
    {/each}
  </div>
{/each}

<style>
  .currency {
    margin: 0.5rem 0 0.25rem;
  }

  /*
   * Two up on a phone, as many as fit after that. 8.75rem is about as wide as
   * a figure like -$1,284.77 gets, so tiles never clip their own number.
   */
  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(8.75rem, 1fr));
    gap: 0.5rem;
  }

  .tile {
    padding: 0.5rem 0.625rem;
    background: var(--pico-card-background-color);
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
  }

  .tile p {
    margin: 0;
  }

  .value {
    margin-top: 0.25rem;
    font-size: 1.1875rem;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }

  .green {
    color: var(--ctp-green);
  }

  .red {
    color: var(--ctp-red);
  }

  .note {
    margin-top: 0.125rem;
    font-size: var(--text-meta);
    line-height: 1.3;
  }

  @media (max-width: 26rem) {
    .tiles {
      /* Below this, auto-fit would drop to one very wide tile per row. */
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .value {
      font-size: 1.0625rem;
    }
  }
</style>

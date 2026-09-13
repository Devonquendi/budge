<script lang="ts">
  import type { Account } from '../api'
  import { formatCents, toCents } from '../money'

  let { accounts }: { accounts: Account[] } = $props()

  type Total = {
    currency: string
    count: number
    net: number
    assets: number
    owing: number
  }

  // One set of totals per currency. Adding NZD to AUD would produce a headline
  // number that means nothing, so we never do it — a second currency gets its
  // own block instead.
  const totals = $derived.by((): Total[] => {
    const currencies = [...new Set(accounts.map((account) => account.currency))]

    return currencies.map((currency) => {
      const cents = accounts
        .filter((account) => account.currency === currency)
        .map((account) => toCents(account.balance_current))

      return {
        currency,
        count: cents.length,
        net: cents.reduce((sum, value) => sum + value, 0),
        assets: cents.reduce((sum, value) => sum + Math.max(value, 0), 0),
        owing: cents.reduce((sum, value) => sum + Math.min(value, 0), 0),
      }
    })
  })
</script>

{#each totals as total (total.currency)}
  <section>
    <p class="eyebrow">
      Net balance{#if totals.length > 1}&nbsp;· {total.currency}{/if}
    </p>
    <p class="net numeric">{formatCents(total.net, total.currency)}</p>
    <p class="muted">
      across {total.count}
      {total.count === 1 ? 'account' : 'accounts'}
    </p>

    <dl>
      <div>
        <dt class="eyebrow">Assets</dt>
        <dd class="numeric">{formatCents(total.assets, total.currency)}</dd>
      </div>
      {#if total.owing !== 0}
        <div>
          <dt class="eyebrow">Owing</dt>
          <dd class="numeric owing">{formatCents(total.owing, total.currency)}</dd>
        </div>
      {/if}
    </dl>
  </section>
{/each}

<style>
  section {
    margin-bottom: 2.5rem;
  }

  .net {
    margin-block: 0.25rem;
    font-size: clamp(2.5rem, 9vw, 3.75rem);
    font-weight: 600;
    line-height: 1.05;
    letter-spacing: -0.03em;
  }

  dl {
    display: flex;
    gap: 2.5rem;
    margin: 1.75rem 0 0;
    padding-top: 1.25rem;
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  dd {
    margin: 0.125rem 0 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .owing {
    color: var(--ctp-red);
  }
</style>

<script lang="ts">
  import type { Account } from '../api'
  import { formatCents, toCents } from '../money'

  let { accounts }: { accounts: Account[] } = $props()

  const cents = $derived(accounts.map((account) => toCents(account.balance_current)))
  const total = $derived(cents.reduce((sum, value) => sum + value, 0))
  const assets = $derived(cents.reduce((sum, value) => sum + Math.max(value, 0), 0))
  const owing = $derived(cents.reduce((sum, value) => sum + Math.min(value, 0), 0))
  // Mixed currencies would need converting first; until then the first wins.
  const currency = $derived(accounts[0]?.currency ?? 'NZD')
</script>

<section>
  <p class="eyebrow">Net balance</p>
  <p class="total numeric">{formatCents(total, currency)}</p>
  <p class="muted">
    across {accounts.length}
    {accounts.length === 1 ? 'account' : 'accounts'}
  </p>

  <dl>
    <div>
      <dt class="eyebrow">Assets</dt>
      <dd class="numeric">{formatCents(assets, currency)}</dd>
    </div>
    {#if owing !== 0}
      <div>
        <dt class="eyebrow">Owing</dt>
        <dd class="numeric owing">{formatCents(owing, currency)}</dd>
      </div>
    {/if}
  </dl>
</section>

<style>
  section {
    margin-bottom: 2.5rem;
  }

  .total {
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

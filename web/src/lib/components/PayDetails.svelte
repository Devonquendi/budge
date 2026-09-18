<script lang="ts">
  import type { PayTo } from '../api'
  import { formatCents } from '../money'

  // What a payer types into their banking app. Everything here is meant to be
  // copied, so every line has its own button: retyping an account number by
  // eye is exactly how money reaches the wrong person.
  let {
    payTo,
    cents,
    compact = false,
  }: {
    payTo: PayTo
    cents: number
    /** Inside a list row rather than a page of its own. */
    compact?: boolean
  } = $props()

  let copied = $state('')

  async function copy(what: string, value: string) {
    await navigator.clipboard.writeText(value)
    copied = what
    setTimeout(() => (copied = ''), 1500)
  }

  const lines = $derived([
    { key: 'account', label: 'Account', value: payTo.account },
    ...(payTo.name ? [{ key: 'name', label: 'Name', value: payTo.name }] : []),
    { key: 'reference', label: 'Reference', value: payTo.reference },
    { key: 'amount', label: 'Amount', value: (cents / 100).toFixed(2) },
  ])
</script>

<div class={['pay', { compact }]}>
  <p class="eyebrow">Pay into</p>
  <dl>
    {#each lines as line (line.key)}
      <div class="line">
        <dt>{line.label}</dt>
        <dd class={['value', { numeric: line.key !== 'name' }]}>
          {line.key === 'amount' ? formatCents(cents, 'NZD') : line.value}
        </dd>
        <button
          type="button"
          class="secondary outline"
          onclick={() => copy(line.key, line.value)}
        >
          {copied === line.key ? 'Copied' : 'Copy'}
        </button>
      </div>
    {/each}
  </dl>

  {#if !payTo.verified}
    <p class="muted note">
      This account hasn't been checked against their bank. Make sure you know who you're
      paying.
    </p>
  {/if}
</div>

<style>
  .pay {
    padding: 0.625rem 0.6875rem 0.75rem;
    background: var(--ctp-recessed);
    border-radius: var(--pico-border-radius);
  }

  .compact {
    border-radius: 0;
  }

  dl {
    margin: 0.4375rem 0 0;
  }

  .line {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.1875rem 0;
  }

  .line + .line {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  dt {
    flex: none;
    width: 5rem;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }

  dd {
    flex: 1 1 auto;
    margin: 0;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 600;
  }

  button {
    flex: none;
    width: auto;
    margin: 0;
    padding: 0.125rem 0.5rem;
    font-size: var(--text-meta);
  }

  .note {
    margin: 0.5rem 0 0;
    font-size: var(--text-meta);
    line-height: 1.4;
  }
</style>

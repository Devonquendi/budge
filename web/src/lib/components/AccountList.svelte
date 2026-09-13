<script lang="ts">
  import { badge, hue, typeLabel } from '../accounts'
  import type { Account } from '../api'
  import { format, toCents } from '../money'

  let { accounts }: { accounts: Account[] } = $props()
</script>

<ul>
  {#each accounts as account (account.id)}
    <li>
      <span class="badge" style:--hue={hue(account.connection_name)} aria-hidden="true">
        {badge(account.connection_name)}
      </span>

      <span class="who">
        <span class="name">{account.name}</span>
        <span class="meta muted">
          {account.connection_name} · {typeLabel(account.type)}
          {#if account.formatted_account}· {account.formatted_account}{/if}
        </span>
      </span>

      <span
        class={[
          'balance',
          'numeric',
          { negative: toCents(account.balance_current) < 0 },
        ]}
      >
        {format(account.balance_current, account.currency)}
      </span>
    </li>
  {:else}
    <li class="empty muted">No accounts are switched on for the dashboard yet.</li>
  {/each}
</ul>

<style>
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
    padding: 0.875rem 1.125rem;
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  .badge {
    display: grid;
    place-items: center;
    flex: none;
    width: 2.5rem;
    height: 2.5rem;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    border-radius: 0.5rem;
    /* Mixing against the card keeps this readable in both themes. */
    background: color-mix(in oklch, oklch(0.7 0.12 var(--hue)) 22%, var(--pico-card-background-color));
    color: color-mix(in oklch, oklch(0.7 0.12 var(--hue)) 70%, var(--pico-color));
  }

  .who {
    display: flex;
    flex-direction: column;
    min-width: 0;
    margin-right: auto;
  }

  .name {
    font-weight: 600;
  }

  .meta {
    font-size: 0.8125rem;
    line-height: 1.35;
  }

  .balance {
    font-size: 1.0625rem;
    font-weight: 600;
    white-space: nowrap;
  }

  .negative {
    color: var(--ctp-red);
  }

  .empty {
    justify-content: center;
    padding-block: 2rem;
  }
</style>

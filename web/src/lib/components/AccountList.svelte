<script lang="ts">
  import { typeLabel } from '../accounts'
  import type { Account } from '../api'
  import { format, toCents } from '../money'
  import { prefs } from '../prefs.svelte'
  import BankBadge from './BankBadge.svelte'

  let { accounts }: { accounts: Account[] } = $props()
</script>

<ul>
  {#each accounts as account (account.id)}
    <li>
      <BankBadge connection={account.connection_name} />

      <span class="who">
        <span class="name">{account.name}</span>
        <span class="meta muted">
          {account.connection_name} · {typeLabel(account.type)}
          {#if account.formatted_account}· {account.formatted_account}{/if}
        </span>
      </span>

      <span
        class={['balance', 'numeric', { negative: toCents(account.balance_current) < 0 }]}
      >
        {format(account.balance_current, account.currency, prefs().hideCents)}
      </span>
    </li>
  {:else}
    <li class="empty muted">No accounts</li>
  {/each}
</ul>

<style>
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  li {
    display: flex;
    align-items: center;
    gap: 0.5625rem;
    padding: 0.375rem 0.6875rem;
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  .who {
    display: flex;
    flex-direction: column;
    min-width: 0;
    margin-right: auto;
  }

  .name {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Bank · type · number runs long; one line keeps the rows the same height. */
  .meta {
    font-size: var(--text-meta);
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .balance {
    font-weight: 600;
    white-space: nowrap;
  }

  .negative {
    color: var(--ctp-red);
  }

  .empty {
    justify-content: center;
    padding-block: 1.5rem;
  }
</style>
